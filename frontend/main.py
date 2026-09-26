"""
Refactored main.py using service classes for better separation of concerns
"""
import os
import time
from datetime import datetime

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.ai_guide import create_router as create_ai_guide_router
from app.ai_guide import is_enabled as ai_guide_enabled
from app.api.wordpress import clear_cache
from app.config import (
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    DEBUG,
    ITEMS_PER_PAGE,
    POST_TYPES,
    SITE_URL,
    config,
    validate_config,
)
from app.services.cache_service import CacheService
from app.services.http_service import HTTPService
from app.utils.category_urls import get_category_url_path, normalize_public_url
from app.utils.helpers import (
    decode_entities,
    get_category_gallery_icon,
    get_category_placeholder_url,
    get_featured_image,
    get_hero_image_sources,
    get_homepage_listing_alt,
    get_listing_card_image,
    get_religious_site_listing_excerpt,
    is_placeholder_image,
    split_display_title,
)

# Use production logging in production environment
if os.getenv('ENVIRONMENT') == 'production':
    from app.utils.logging_config_production import setup_logging
else:
    from app.utils.logging_config import setup_logging
import asyncio

from app.i18n import (
    current_lang,
    lang_prefix,
    language_switch_urls,
    localize_href,
    prefix_internal_links,
    tr,
    translate,
)
from app.middleware.error_handling import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.head_method import HeadMethodMiddleware
from app.middleware.legacy_urls import LegacyCategoryUrlMiddleware
from app.middleware.locale import LocaleMiddleware
from app.middleware.security import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    setup_cors_middleware,
)
from app.services.cache_warming_service import CacheWarmingService
from app.services.contact_service import ContactService
from app.services.content_service import ContentService
from app.services.contribution_service import ContributionService
from app.services.favorites_service import FavoritesService
from app.services.health_service import HealthService
from app.services.homepage_service import HomepageService
from app.services.metrics_service import MetricsService
from app.services.sitemap_service import SitemapService
from app.services.submission_service import SubmissionService
from app.services.template_service import TemplateService
from app.utils.validation import InputValidator

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    debug=DEBUG,
    redirect_slashes=False,
)

# Setup security middleware
setup_cors_middleware(app)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 requests per minute
app.add_middleware(RequestSizeLimitMiddleware, max_size=100*1024*1024)  # 100MB limit for video uploads
app.add_middleware(LegacyCategoryUrlMiddleware)
app.add_middleware(HeadMethodMiddleware)

# Setup exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Background task for cache warming
async def warm_cache_on_startup():
    """Background task to warm cache on startup"""
    try:
        # Small delay to let the app fully initialize
        await asyncio.sleep(2)
        
        # Warm the cache
        stats = await CacheWarmingService.warm_all_caches()
        
        if stats["success"]:
            logger.info(
                f"🔥 Cache warming completed: "
                f"{stats['total_items']} items in {stats['duration_seconds']}s"
            )
        else:
            logger.error(f"Cache warming failed: {stats.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Cache warming background task failed: {str(e)}")


# Middleware to track metrics
@app.middleware("http")
async def static_cache_middleware(request: Request, call_next):
    """Long-cache versioned static assets."""
    response = await call_next(request)
    if lang_prefix() and "text/html" in response.headers.get("content-type", ""):
        body = b"".join([chunk async for chunk in response.body_iterator])
        html = prefix_internal_links(body.decode("utf-8", "replace"))
        kept = [
            (key, value)
            for key, value in response.raw_headers
            if key.lower() not in (b"content-length", b"content-type")
        ]
        response = HTMLResponse(html, status_code=response.status_code)
        response.raw_headers.extend(kept)
    path = request.url.path
    if path.startswith("/static/") and ("?v=" in str(request.url) or path.endswith((".webp", ".png", ".ico", ".svg", ".woff2"))):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


app.add_middleware(LocaleMiddleware)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000  # Convert to ms
        
        # Record metrics
        MetricsService.record_request(
            str(request.url.path),
            request.method,
            response.status_code,
            duration
        )
        
        return response
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        MetricsService.record_error(type(e).__name__)
        raise


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    # Validate configuration
    validation_result = validate_config(config)
    if not validation_result["valid"]:
        logger.error(f"Configuration validation failed: {validation_result['issues']}")
        for issue in validation_result["issues"]:
            logger.error(f"  - {issue}")
    
    if validation_result["warnings"]:
        for warning in validation_result["warnings"]:
            logger.warning(f"Configuration warning: {warning}")
    
    logger.info(f"Environment: {validation_result['environment']}")
    
    # Test Redis connection
    redis_healthy = await CacheService.health_check()
    if redis_healthy:
        logger.info("✅ Redis connection established successfully")
    else:
        logger.warning("⚠️ Redis connection failed - caching will be disabled")
    
    # Log HTTP service configuration
    http_info = await HTTPService.get_connection_info()
    logger.info(f"HTTP service initialized: {http_info}")
    
    # Warm up cache with popular content (non-blocking)
    if redis_healthy:
        logger.info("Starting cache warming in background...")
        asyncio.create_task(warm_cache_on_startup())
    else:
        logger.warning("Skipping cache warming - Redis not available")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")
    
    await CacheService.close_redis()
    await HTTPService.close_clients()
    
    logger.info("🔌 All connections closed")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# Initialize Jinja2 Templates
templates = Jinja2Templates(directory="templates")
templates.env.globals.update(now=datetime.utcnow)
templates.env.filters["split_display_title"] = split_display_title
templates.env.filters["is_placeholder_image"] = is_placeholder_image
templates.env.filters["category_placeholder"] = get_category_placeholder_url
templates.env.filters["category_gallery_icon"] = get_category_gallery_icon
templates.env.filters["decode_entities"] = decode_entities
templates.env.filters["religious_site_listing_excerpt"] = get_religious_site_listing_excerpt
templates.env.filters["homepage_listing_alt"] = lambda title, category_slug: get_homepage_listing_alt(category_slug, title)
templates.env.filters["category_url"] = get_category_url_path
templates.env.filters["public_url"] = lambda url: localize_href(normalize_public_url(url))
templates.env.filters["listing_card_image"] = get_listing_card_image
templates.env.filters["hero_image_sources"] = get_hero_image_sources
templates.env.filters["t"] = translate
templates.env.globals["lang_code"] = current_lang

# Initialize services
template_service = TemplateService(templates)
content_service = ContentService()
contact_service = ContactService()
favorites_service = FavoritesService()


async def build_detail_template_data(
    commons: dict,
    category_name: str,
    post_type_name: str,
    slug: str,
) -> dict | None:
    """Load item detail, related picks, and template context."""
    item_data = await content_service.get_item_detail(post_type_name, slug)
    if not item_data:
        return None
    related_items = await content_service.get_related_items(post_type_name, slug)
    location_data = content_service.get_location_data_for_item(
        item_data["item"], category_name
    )
    nearby_items = []
    if location_data:
        nearby_items = await content_service.get_nearby_items(
            location_data,
            slug,
            item_data["item"].get("id"),
        )
        nearby_slugs = {item["slug"] for item in nearby_items}
        related_items = [
            item for item in related_items if item.get("slug") not in nearby_slugs
        ][:4]
    return template_service.prepare_item_detail_template_data(
        commons, category_name, post_type_name, item_data, location_data, related_items, nearby_items
    )


# Template filters will be handled by JavaScript for now

# Common dependencies
async def get_common_template_data(request: Request):
    """Get common data for all templates including navigation menu"""
    from app.api.wordpress import get_navigation_menu
    
    common_data = template_service.get_common_template_data(request)
    common_data["lang"] = current_lang()
    common_data["lang_urls"] = language_switch_urls(request.url.path, request.url.query)

    # Fetch navigation menu from WordPress
    nav_menu = await get_navigation_menu("primary")
    common_data["nav_menu"] = nav_menu
    
    return common_data


templates.env.globals["ai_guide_enabled"] = ai_guide_enabled
app.include_router(create_ai_guide_router(templates, get_common_template_data))


# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, commons: dict = Depends(get_common_template_data)):
    """Home page with featured items from all categories"""
    # Fetch homepage settings from WordPress (sections + hero)
    hp_settings = await HomepageService.get_homepage_settings()
    homepage_sections = hp_settings.get("sections", [])
    hero_settings = hp_settings.get("hero", {"slides": [], "speed": 6})
    
    featured_items = await content_service.get_featured_items(homepage_sections)
    locations = await content_service.get_map_locations()
    
    template_data = template_service.prepare_home_template_data(
        commons, featured_items, locations
    )
    # Pass section configs and hero settings to template
    template_data["homepage_sections"] = homepage_sections
    template_data["hero_settings"] = hero_settings
    template_data["about_text"] = hp_settings.get("about_text", "")
    
    return templates.TemplateResponse(request=request, name="base/index.html", context=template_data)


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request, commons: dict = Depends(get_common_template_data)):
    """About VeriaGuide — mission, editorial team and heritage focus."""
    hp_settings = await HomepageService.get_homepage_settings()
    about_text = hp_settings.get("about_text", "")
    template_data = template_service.prepare_about_template_data(commons, about_text)
    return templates.TemplateResponse(request=request, name="about/page.html", context=template_data)


MAP_LISTING_PAGES = {
    "religious_sites": ("religious_site", "Byzantine Churches Map – Veria, Greece",
                        "Explore churches and monasteries across Veria (Veroia), Imathia — including sites linked to Apostle Paul."),
    "restaurants": ("restaurant", "Restaurants in Veria, Greece", "Discover authentic Greek cuisine and dining experiences in Veria"),
    "cafes": ("cafe", "Cafes in Veria, Greece", "Discover cozy cafes and coffee shops in Veria"),
    "accommodations": ("accommodation", "Accommodations in Veria, Greece",
                       "Find the perfect place to stay in Veria and the surrounding area"),
    "museums": ("museum", "Museums in Veria, Greece", "Discover history, art and culture in Veria's museums"),
    "archaeological_sites": ("archaeological_site", "Archaeological Sites in Veria, Greece",
                             "Discover ancient ruins, temples and historical sites in Veria"),
    "ski_resorts": ("ski_resort", "Ski Resorts in Veria, Greece",
                    "Discover ski resorts and winter sports destinations near Veria"),
    "tours": ("tour", "Tours in Veria, Greece", "Explore all locations in Veria"),
    "hiking_trails": ("hiking_trail", "Hiking Trails in Veria, Greece", "Explore all locations in Veria"),
    "hidden_gems": ("hidden_gem", "Hidden Gems in Veria, Greece", "Hand-picked highlights from Veria"),
}


def register_map_listing_route(category_name: str, post_type_name: str, heading: str, intro: str) -> None:
    from collections import Counter

    from app.utils.helpers import get_meta_data, get_page_url

    public_path = get_category_url_path(category_name)

    async def map_listing(
        request: Request,
        site_type: str | None = Query(None),
        commons: dict = Depends(get_common_template_data),
    ):
        from app.api.wordpress import get_all_posts_for_type

        all_items = await get_all_posts_for_type(post_type_name)
        site_types = Counter(tag for item in all_items for tag in (item.get("tag_names") or []))
        items = all_items
        if site_type and site_type != "all":
            items = [item for item in all_items if site_type in (item.get("tag_names") or [])]

        template_data = {
            **commons,
            "meta": get_meta_data(title=heading, description=intro, url=get_page_url(request.url.path)),
            "items": items,
            "locations": ContentService._prepare_location_data(items),
            "filter_aggregations": {"site_types": dict(site_types.most_common())},
            "selected_site_type": site_type or "all",
            "map_path": public_path,
            "map_post_type": post_type_name,
            "map_heading": heading,
            "map_intro": intro,
            "lang_prefix": lang_prefix(),
            "needs_leaflet": True,
        }
        return templates.TemplateResponse(request=request, name="base/map-listings.html", context=template_data)

    app.add_api_route(f"/{public_path}/map", map_listing, methods=["GET"], response_class=HTMLResponse,
                      name=f"{category_name}_map_listing")
    # Must win over the /{category}/{slug} detail routes registered earlier.
    app.router.routes.insert(0, app.router.routes.pop())


for _category, (_post_type, _heading, _intro) in MAP_LISTING_PAGES.items():
    register_map_listing_route(_category, _post_type, _heading, _intro)


@app.get("/accommodations/{slug}", response_class=HTMLResponse)
async def accommodation_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Accommodation detail page"""
    template_data = await build_detail_template_data(
        commons, "accommodations", "accommodation", slug
    )
    if not template_data:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    
    return templates.TemplateResponse(request=request, name="accommodations/detail.html", context=template_data)


# Every category shares the churches listing layout: sidebar map, search, type filter, city filter.
CATEGORY_LIST_PAGES = {
    "religious_sites": (
        "Byzantine Churches & Monasteries in Veria, Greece",
        "Explore sacred sites across Veria (Veroia), Imathia — from centuries-old Byzantine churches to monasteries linked to Apostle Paul's visit.",
        "Veria is renowned for its extraordinary Byzantine heritage. Find churches near the ancient Vema amphitheatre, check visiting hours and explore every site on the map.",
        "Site Type",
    ),
    "museums": ("Museums in Veria", "Discover history, art and culture in Veria's museums", "", "Museum Type"),
    "archaeological_sites": ("Archaeological Sites in Veria",
                             "Discover ancient ruins, temples and historical sites in Veria", "", "Site Type"),
    "hidden_gems": ("Hidden Gems in Veria", "Hand-picked highlights from Veria", "", "Type"),
    "tours": ("Tours in Veria", "Explore all locations in Veria", "", "Tour Type:"),
    "hiking_trails": ("Hiking Trails in Veria", "Explore all locations in Veria", "", "Difficulty"),
    "ski_resorts": ("Ski Resorts in Veria", "Discover ski resorts and winter sports destinations near Veria", "",
                    "Ski Resort Type"),
    "restaurants": ("Best Restaurants in Veria", "Discover authentic Greek cuisine and dining experiences in Veria", "",
                    "Cuisine Type"),
    "cafes": ("Best Cafes in Veria", "Discover cozy cafes and coffee shops in Veria", "", "Cafe Type"),
    "accommodations": ("Accommodations in Veria", "Find the perfect place to stay in Veria and the surrounding area", "",
                       "Property Type"),
}

# Detail routes for these categories are declared individually further down.
SPECIALIZED_DETAIL_CATEGORIES = {
    "religious_sites", "archaeological_sites", "museums", "ski_resorts",
    "restaurants", "cafes", "accommodations",
}


def register_list_routes(category_name: str, post_type_name: str) -> None:
    public_path = get_category_url_path(category_name)
    heading, intro, intro_more, type_label = CATEGORY_LIST_PAGES.get(
        category_name, (category_name.replace("_", " ").title(), "", "", "Type")
    )

    async def list_items(
        request: Request,
        page: int = Query(1, ge=1),
        search: str | None = None,
        guestRating: str = Query('any'),
        city: str | None = Query(None),
        site_type: str | None = Query(None),
        cuisine_type: str | None = Query(None),
        cafe_type: str | None = Query(None),
        price_range: str | None = Query(None),
        amenities: list[str] = Query(None),
        commons: dict = Depends(get_common_template_data)
    ):
        if search:
            search = InputValidator.validate_search_query(search)
        # cuisine_type/cafe_type are the legacy filter parameter names
        type_filter = site_type or cuisine_type or cafe_type
        content_data = await content_service.get_category_items(
            post_type_name, page, search, None, guestRating,
            city=city, site_type=type_filter, price_range=price_range, amenities=amenities
        )
        template_data = template_service.prepare_category_list_template_data(
            commons, category_name, content_data, page, search, [], guestRating
        )
        template_data.update({
            "selected_city": city or "all",
            "selected_site_type": type_filter or "all",
            "selected_price_range": price_range or "all",
            "selected_amenities": amenities or [],
            "filter_aggregations": content_data.get("filter_aggregations", {}),
            "guestRating": guestRating,
            "total_all_count": content_data.get("rating_counts", {}).get("any", 0),
            "list_path": public_path,
            "list_post_type": post_type_name,
            "list_heading": heading,
            "list_intro": intro,
            "list_intro_more": intro_more,
            "list_type_label": type_label,
            "lang_prefix": lang_prefix(),
        })
        return templates.TemplateResponse(request=request, name="base/category-list.html", context=template_data)

    async def autocomplete():
        from app.api.wordpress import get_all_posts_for_type

        items = await get_all_posts_for_type(post_type_name)
        return [
            {
                "id": item.get("id"),
                "title": item.get("title", {}).get("rendered", ""),
                "slug": item.get("slug", ""),
                "city": (item.get("acf") or {}).get("city", "") if isinstance(item.get("acf"), dict) else "",
                "image": get_featured_image(item) or "",
            }
            for item in items
        ]

    app.add_api_route(f"/{public_path}", list_items, methods=["GET"], response_class=HTMLResponse,
                      name=f"{category_name}_list")
    app.add_api_route(f"/api/{public_path}/autocomplete", autocomplete, methods=["GET"],
                      name=f"{category_name}_autocomplete")


def register_detail_route(category_name: str, post_type_name: str) -> None:
    public_path = get_category_url_path(category_name)

    async def item_detail(
        request: Request,
        slug: str,
        commons: dict = Depends(get_common_template_data)
    ):
        template_data = await build_detail_template_data(
            commons, category_name, post_type_name, slug
        )
        if not template_data:
            raise HTTPException(status_code=404, detail="Item not found")
        return templates.TemplateResponse(request=request, name=f"{category_name}/detail.html", context=template_data)

    app.add_api_route(f"/{public_path}/{{slug}}", item_detail, methods=["GET"], response_class=HTMLResponse,
                      name=f"{category_name}_detail")


for _category, _post_type in POST_TYPES.items():
    register_list_routes(_category, _post_type)
    if _category not in SPECIALIZED_DETAIL_CATEGORIES:
        register_detail_route(_category, _post_type)


# Add the religious_sites, archaeological_sites, museums and ski_resorts detail routes separately since we excluded them from the loop
@app.get("/religious-sites/{slug}", response_class=HTMLResponse)
async def religious_sites_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Detail page for religious sites"""
    template_data = await build_detail_template_data(
        commons, "religious_sites", "religious_site", slug
    )
    if not template_data:
        raise HTTPException(status_code=404, detail="Religious site not found")
    
    return templates.TemplateResponse(request=request, name="religious_sites/detail.html", context=template_data)


@app.get("/archaeological-sites/{slug}", response_class=HTMLResponse)
async def archaeological_sites_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Detail page for archaeological sites"""
    template_data = await build_detail_template_data(
        commons, "archaeological_sites", "archaeological_site", slug
    )
    if not template_data:
        raise HTTPException(status_code=404, detail="Archaeological site not found")
    
    return templates.TemplateResponse(request=request, name="archaeological_sites/detail.html", context=template_data)


@app.get("/museums/{slug}", response_class=HTMLResponse)
async def museums_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Detail page for museums"""
    template_data = await build_detail_template_data(
        commons, "museums", "museum", slug
    )
    if not template_data:
        raise HTTPException(status_code=404, detail="Museum not found")
    
    return templates.TemplateResponse(request=request, name="museums/detail.html", context=template_data)


@app.get("/ski-resorts/{slug}", response_class=HTMLResponse)
async def ski_resorts_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Detail page for ski resorts"""
    template_data = await build_detail_template_data(
        commons, "ski_resorts", "ski_resort", slug
    )
    if not template_data:
        raise HTTPException(status_code=404, detail="Ski resort not found")
    
    return templates.TemplateResponse(request=request, name="ski_resorts/detail.html", context=template_data)


@app.get("/restaurants/{slug}", response_class=HTMLResponse)
async def restaurants_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Detail page for restaurants"""
    template_data = await build_detail_template_data(
        commons, "restaurants", "restaurant", slug
    )
    if not template_data:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return templates.TemplateResponse(request=request, name="restaurants/detail.html", context=template_data)


@app.get("/cafes/{slug}", response_class=HTMLResponse)
async def cafes_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Detail page for cafes"""
    template_data = await build_detail_template_data(
        commons, "cafes", "cafe", slug
    )
    if not template_data:
        raise HTTPException(status_code=404, detail="Cafe not found")
    
    return templates.TemplateResponse(request=request, name="cafes/detail.html", context=template_data)


@app.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str | None = None,
    type: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    commons: dict = Depends(get_common_template_data)
):
    """Search across content types"""
    results = []
    
    if q:
        # Validate and sanitize search query
        try:
            q = InputValidator.validate_search_query(q)
        except HTTPException as e:
            logger.warning(f"Invalid search query from {request.client.host}: {q}")
            raise e
        
        # Validate pagination
        pagination = InputValidator.validate_pagination_params(page, ITEMS_PER_PAGE)
        page = pagination["page"]
        
        # Validate type parameter
        if type and type not in POST_TYPES:
            raise HTTPException(status_code=400, detail="Invalid content type")
        
        results = await content_service.search_content(q, type, page, per_page)
    
    template_data = template_service.prepare_search_template_data(
        commons, q, type, results, page, per_page
    )
    
    return templates.TemplateResponse(request=request, name="search/results.html", context=template_data)


@app.get("/contact", response_class=HTMLResponse)
async def contact_form(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Contact form page"""
    template_data = template_service.prepare_contact_template_data(commons)
    return templates.TemplateResponse(request=request, name="contact/form.html", context=template_data)


@app.post("/contact", response_class=HTMLResponse)
async def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    privacy: str = Form(None),
    customSubject: str = Form(None),
    commons: dict = Depends(get_common_template_data)
):
    """Submit contact form"""
    # Validate and sanitize contact form data
    try:
        # Check privacy policy agreement
        if not privacy or privacy != "on":
            raise HTTPException(status_code=400, detail="You must agree to the Privacy Policy to send your message")
        
        # Handle custom subject for "Other" option
        final_subject = subject
        if subject == "Other" and customSubject:
            final_subject = f"Other: {customSubject.strip()}"
        elif subject == "Other" and not customSubject:
            raise HTTPException(status_code=400, detail="Please specify your topic when selecting 'Other'")
        
        validated_data = InputValidator.validate_contact_form(name, email, final_subject, message)
        result = await contact_service.submit_contact_form(
            validated_data["name"],
            validated_data["email"], 
            validated_data["subject"],
            validated_data["message"]
        )
    except HTTPException as e:
        logger.warning(f"Invalid contact form submission from {request.client.host}: {e.detail}")
        result = {"success": False, "message": e.detail}
    
    template_data = template_service.prepare_contact_template_data(
        commons, result.get("success", False), result.get("message", "")
    )
    
    return templates.TemplateResponse(request=request, name="contact/form.html", context=template_data)


@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Favorites page"""
    favorites = favorites_service.get_user_favorites(request)
    enriched_favorites = await favorites_service.enrich_favorites(favorites)
    template_data = template_service.prepare_favorites_template_data(commons, enriched_favorites)
    return templates.TemplateResponse(request=request, name="favorites/list.html", context=template_data)


@app.post("/favorites/add")
async def add_to_favorites(
    request: Request,
    response: Response,
    item_id: str = Form(...),
    item_type: str = Form(...),
    item_title: str = Form(...),
    item_image: str | None = Form(None)
):
    """Add item to favorites"""
    return favorites_service.add_to_favorites(
        request, response, item_id, item_type, item_title, item_image
    )


@app.post("/favorites/remove")
async def remove_from_favorites(
    request: Request,
    response: Response,
    item_id: str = Form(...)
):
    """Remove item from favorites"""
    return favorites_service.remove_from_favorites(request, response, item_id)


@app.post("/favorites/clear")
async def clear_all_favorites(
    request: Request,
    response: Response
):
    """Clear all favorites"""
    return favorites_service.clear_all_favorites(response)


@app.get("/map", response_class=HTMLResponse)
async def map_view(
    request: Request,
    type: str | None = None,
    commons: dict = Depends(get_common_template_data)
):
    """Interactive map view"""
    locations = await content_service.get_map_locations(type)
    template_data = template_service.prepare_map_template_data(commons, locations, type)
    return templates.TemplateResponse(request=request, name="base/map.html", context=template_data)


@app.get("/submit", response_class=HTMLResponse)
async def submission_form(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Business submission form page"""
    template_data = {
        **commons,
        "success": False,
        "message": "",
        "submission_id": None
    }
    from app.utils.helpers import get_meta_data, get_page_url
    template_data["meta"] = get_meta_data(
        title="Add your business to VeriaGuide",
        description="Add your business to our directory",
        url=get_page_url(request.url.path),
    )
    return templates.TemplateResponse(request=request, name="submit/form.html", context=template_data)


@app.post("/submit", response_class=HTMLResponse)
async def submit_business(
    request: Request,
    business_name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    opening_hours: str = Form(...),
    website: str | None = Form(None),
    latitude: str | None = Form(None),
    longitude: str | None = Form(None),
    images: list[UploadFile] = File(...),
    privacy: str = Form(None),
    terms: str = Form(None),
    commons: dict = Depends(get_common_template_data)
):
    """Submit business listing"""
    import base64
    
    result = {"success": False, "message": "", "submission_id": None}
    
    try:
        # Check privacy and terms agreement
        if not privacy or privacy != "on":
            raise HTTPException(status_code=400, detail="You must agree to the privacy policy")
        
        if not terms or terms != "on":
            raise HTTPException(status_code=400, detail="You must accept the terms")
        
        # Validate form data
        validated_data = InputValidator.validate_submission_form(
            business_name, category, description, email, phone,
            address, city, opening_hours, website, latitude, longitude
        )
        
        # Validate images
        if not images or len(images) == 0:
            raise HTTPException(status_code=400, detail="At least one photo is required")
        
        if len(images) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 photos allowed")
        
        # Process images
        processed_images = []
        for image in images:
            # Validate image
            validation = SubmissionService.validate_image(image.filename, image.size)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=validation["error"])
            
            # Read image content
            content = await image.read()
            
            # Convert to base64 for storage
            base64_image = base64.b64encode(content).decode('utf-8')
            
            processed_images.append({
                "filename": image.filename,
                "content_type": image.content_type,
                "size": image.size,
                "data": base64_image
            })
        
        # Save submission
        result = await SubmissionService.save_submission(
            business_name=validated_data["business_name"],
            category=validated_data["category"],
            description=validated_data["description"],
            email=validated_data["email"],
            phone=validated_data["phone"],
            address=validated_data["address"],
            city=validated_data["city"],
            opening_hours=validated_data["opening_hours"],
            website=validated_data["website"],
            latitude=validated_data["latitude"],
            longitude=validated_data["longitude"],
            images=processed_images
        )
        
        logger.info(f"Business submission from {request.client.host}: {business_name}")
        
    except HTTPException as e:
        logger.warning(f"Invalid submission from {request.client.host}: {e.detail}")
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        result = {
            "success": False,
            "message": "; ".join(tr(part) for part in detail.split("; ")),
            "submission_id": None,
        }
    except Exception as e:
        logger.error(f"Error processing submission: {str(e)}")
        result = {"success": False, "message": "An error occurred. Please try again later.", "submission_id": None}
    
    template_data = {
        **commons,
        "success": result.get("success", False),
        "message": tr(result.get("message", "")),
        "submission_id": result.get("submission_id")
    }
    from app.utils.helpers import get_meta_data, get_page_url
    template_data["meta"] = get_meta_data(
        title="Add your business to VeriaGuide",
        description="Add your business to our directory",
        url=get_page_url(request.url.path),
    )
    
    return templates.TemplateResponse(request=request, name="submit/form.html", context=template_data)


@app.get("/contribute", response_class=HTMLResponse)
async def contribution_form(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Contribution form page for adding content to existing listings"""
    template_data = {
        **commons,
        "success": False,
        "message": "",
        "contribution_id": None
    }
    from app.utils.helpers import get_meta_data, get_page_url
    template_data["meta"] = get_meta_data(
        title="Share content",
        description="Add photos, videos or descriptions to existing listings",
        url=get_page_url(request.url.path),
    )
    return templates.TemplateResponse(request=request, name="submit/contribute.html", context=template_data)


@app.post("/contribute", response_class=HTMLResponse)
async def submit_contribution(
    request: Request,
    listing_id: str = Form(...),
    listing_category: str = Form(...),
    contribution_types: list[str] = Form(...),
    email: str = Form(...),
    name: str | None = Form(None),
    description: str | None = Form(None),
    photos: list[UploadFile] = File(default=[]),
    videos: list[UploadFile] = File(default=[]),
    privacy: str = Form(None),
    commons: dict = Depends(get_common_template_data)
):
    """Submit contribution to existing listing"""
    import base64
    
    result = {"success": False, "message": "", "contribution_id": None}
    
    try:
        # Check privacy agreement
        if not privacy or privacy != "on":
            raise HTTPException(status_code=400, detail="You must agree to the terms")
        
        # Validate email
        if not InputValidator.validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Process photos
        processed_photos = []
        if photos and len(photos) > 0 and photos[0].filename:
            if len(photos) > ContributionService.MAX_IMAGES:
                raise HTTPException(status_code=400, detail="Maximum 10 photos allowed")
            
            for photo in photos:
                validation = ContributionService.validate_image(photo.filename, photo.size)
                if not validation["valid"]:
                    raise HTTPException(status_code=400, detail=validation["error"])
                
                content = await photo.read()
                base64_image = base64.b64encode(content).decode('utf-8')
                
                processed_photos.append({
                    "filename": photo.filename,
                    "content_type": photo.content_type,
                    "size": photo.size,
                    "data": base64_image
                })
        
        # Process videos
        processed_videos = []
        if videos and len(videos) > 0 and videos[0].filename:
            if len(videos) > ContributionService.MAX_VIDEOS:
                raise HTTPException(status_code=400, detail="Maximum 3 videos allowed")
            
            for video in videos:
                validation = ContributionService.validate_video(video.filename, video.size)
                if not validation["valid"]:
                    raise HTTPException(status_code=400, detail=validation["error"])
                
                content = await video.read()
                base64_video = base64.b64encode(content).decode('utf-8')
                
                processed_videos.append({
                    "filename": video.filename,
                    "content_type": video.content_type,
                    "size": video.size,
                    "data": base64_video
                })
        
        # Save contribution
        result = await ContributionService.save_contribution(
            listing_id=listing_id,
            listing_category=listing_category,
            contribution_types=contribution_types,
            email=email,
            name=name,
            description=description,
            photos=processed_photos,
            videos=processed_videos
        )
        
        logger.info(f"Contribution from {request.client.host} for listing {listing_id}")
        
    except HTTPException as e:
        logger.warning(f"Invalid contribution from {request.client.host}: {e.detail}")
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        result = {
            "success": False,
            "message": "; ".join(tr(part) for part in detail.split("; ")),
            "contribution_id": None,
        }
    except Exception as e:
        logger.error(f"Error processing contribution: {str(e)}")
        result = {"success": False, "message": "An error occurred. Please try again later.", "contribution_id": None}
    
    template_data = {
        **commons,
        "success": result.get("success", False),
        "message": tr(result.get("message", "")),
        "contribution_id": result.get("contribution_id")
    }
    from app.utils.helpers import get_meta_data, get_page_url
    template_data["meta"] = get_meta_data(
        title="Share content",
        description="Add photos, videos or descriptions to existing listings",
        url=get_page_url(request.url.path),
    )
    
    return templates.TemplateResponse(request=request, name="submit/contribute.html", context=template_data)


# Legacy route - should be refactored to use services
@app.get("/archaeologicals", response_class=HTMLResponse)
async def list_archaeologicals(request: Request):
    """Legacy archaeological sites route - TODO: refactor to use services"""
    from app.api.wordpress import get_posts
    
    archaeological_posts = await get_posts("archaeological", per_page=10)
    
    meta_data = {
        "title": "Archäologische Stätten",
        "description": "Entdecken Sie die archäologischen Stätten in Veria."
    }
    
    return templates.TemplateResponse(request=request, name="archaeologicals/list.html", context={
        "posts": archaeological_posts,
        "meta": meta_data
    })


# Admin authentication dependency
async def verify_admin_access(request: Request):
    """Verify admin access for protected endpoints"""
    if not InputValidator.validate_admin_access(request):
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized access to admin endpoint",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return True

# Admin and utility routes
@app.get("/admin/clear-cache")
async def admin_clear_cache(request: Request, _: bool = Depends(verify_admin_access)):
    """Clear application cache"""
    await clear_cache()
    logger.info(f"Cache cleared by admin from {request.client.host}")
    return {"success": True, "message": "Cache cleared successfully"}

@app.get("/admin/cache-info")
async def admin_cache_info(request: Request, _: bool = Depends(verify_admin_access)):
    """Get cache information and statistics"""
    cache_info = await CacheService.get_cache_info()
    return cache_info

@app.get("/admin/cache-health")
async def admin_cache_health():
    """Check cache health - public endpoint for monitoring"""
    is_healthy = await CacheService.health_check()
    return {"healthy": is_healthy, "service": "Redis"}

@app.post("/admin/clear-cache/{pattern}")
async def admin_clear_cache_pattern(
    pattern: str, 
    request: Request, 
    _: bool = Depends(verify_admin_access)
):
    """Clear cache entries matching a pattern"""
    # Validate pattern to prevent abuse
    if not InputValidator.validate_safe_string(pattern, 50):
        raise HTTPException(status_code=400, detail="Invalid cache pattern")
    
    deleted_count = await CacheService.delete_pattern(pattern)
    logger.info(f"Cache pattern '{pattern}' cleared by admin from {request.client.host}")
    return {"success": True, "deleted_keys": deleted_count, "pattern": pattern}

@app.get("/admin/config")
async def admin_config(request: Request, _: bool = Depends(verify_admin_access)):
    """Get current configuration (sanitized)"""
    validation_result = validate_config(config)
    
    # Sanitize sensitive information
    safe_config = {
        "environment": config.__class__.__name__,
        "debug": config.DEBUG,
        "app_name": config.APP_NAME,
        "app_version": config.APP_VERSION,
        "cache_expiry": config.CACHE_EXPIRY,
        "redis_default_ttl": config.REDIS_DEFAULT_TTL,
        "items_per_page": config.ITEMS_PER_PAGE,
        "http_timeout": config.HTTP_TIMEOUT,
        "wp_api_timeout": config.WP_API_TIMEOUT,
        "http_pool_connections": config.HTTP_POOL_CONNECTIONS,
        "http_pool_maxsize": config.HTTP_POOL_MAXSIZE,
        "log_level": config.LOG_LEVEL,
        "validation": validation_result
    }
    
    return safe_config

@app.get("/admin/http-info")
async def admin_http_info(request: Request, _: bool = Depends(verify_admin_access)):
    """Get HTTP service connection information"""
    return await HTTPService.get_connection_info()

@app.post("/admin/warm-cache")
async def admin_warm_cache(request: Request, _: bool = Depends(verify_admin_access)):
    """Manually trigger cache warming"""
    logger.info(f"Manual cache warming triggered by admin from {request.client.host}")
    stats = await CacheWarmingService.warm_all_caches()
    return stats

@app.post("/admin/warm-cache/{post_type}")
async def admin_warm_cache_category(
    post_type: str,
    request: Request,
    _: bool = Depends(verify_admin_access)
):
    """Warm cache for a specific category"""
    logger.info(f"Cache warming for {post_type} triggered by admin from {request.client.host}")
    result = await CacheWarmingService.warm_specific_category(post_type)
    return result

@app.post("/admin/invalidate-and-rewarm/{post_type}")
async def admin_invalidate_and_rewarm(
    post_type: str,
    request: Request,
    _: bool = Depends(verify_admin_access)
):
    """Invalidate and rewarm cache for a specific category"""
    logger.info(f"Cache invalidation and rewarming for {post_type} triggered by admin from {request.client.host}")
    result = await CacheWarmingService.invalidate_and_rewarm(post_type)
    return result

@app.get("/admin/cache-warming-status")
async def admin_cache_warming_status(request: Request, _: bool = Depends(verify_admin_access)):
    """Get cache warming status"""
    status = await CacheWarmingService.get_cache_warming_status()
    return status

@app.get("/admin/metrics")
async def admin_metrics(request: Request, _: bool = Depends(verify_admin_access)):
    """Get application metrics"""
    metrics = await MetricsService.get_metrics()
    return metrics

@app.get("/admin/metrics/health")
async def admin_metrics_health(request: Request, _: bool = Depends(verify_admin_access)):
    """Get health metrics"""
    health = await MetricsService.get_health_metrics()
    return health

@app.post("/admin/metrics/reset")
async def admin_metrics_reset(request: Request, _: bool = Depends(verify_admin_access)):
    """Reset metrics (for testing)"""
    logger.info(f"Metrics reset by admin from {request.client.host}")
    MetricsService.reset_metrics()
    return {"success": True, "message": "Metrics reset"}

@app.get("/admin/submissions")
async def admin_get_submissions(request: Request, _: bool = Depends(verify_admin_access)):
    """Get all pending submissions (admin only)"""
    submissions = await SubmissionService.get_pending_submissions()
    return {"success": True, "submissions": submissions, "count": len(submissions)}

@app.get("/admin/submissions/dashboard", response_class=HTMLResponse)
async def admin_submissions_dashboard(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Admin dashboard for managing submissions"""
    template_data = {**commons}
    return templates.TemplateResponse(request=request, name="admin/submissions.html", context=template_data)

@app.get("/admin/contributions/dashboard", response_class=HTMLResponse)
async def admin_contributions_dashboard(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Admin dashboard for managing contributions"""
    template_data = {**commons}
    return templates.TemplateResponse(request=request, name="admin/contributions.html", context=template_data)

@app.post("/admin/submissions/{submission_id}/approve")
async def admin_approve_submission(
    submission_id: str,
    request: Request,
    admin_notes: str | None = Form(None),
    _: bool = Depends(verify_admin_access)
):
    """Approve a submission (admin only)"""
    result = await SubmissionService.update_submission_status(
        submission_id, "approved", admin_notes
    )
    logger.info(f"Submission {submission_id} approved by admin from {request.client.host}")
    return result

@app.post("/admin/submissions/{submission_id}/reject")
async def admin_reject_submission(
    submission_id: str,
    request: Request,
    admin_notes: str | None = Form(None),
    _: bool = Depends(verify_admin_access)
):
    """Reject a submission (admin only)"""
    result = await SubmissionService.update_submission_status(
        submission_id, "rejected", admin_notes
    )
    logger.info(f"Submission {submission_id} rejected by admin from {request.client.host}")
    return result

@app.get("/admin/contributions")
async def admin_get_contributions(request: Request, _: bool = Depends(verify_admin_access)):
    """Get all pending contributions (admin only)"""
    contributions = await ContributionService.get_pending_contributions()
    return {"success": True, "contributions": contributions, "count": len(contributions)}

@app.post("/admin/contributions/{contribution_id}/approve")
async def admin_approve_contribution(
    contribution_id: str,
    request: Request,
    admin_notes: str | None = Form(None),
    _: bool = Depends(verify_admin_access)
):
    """Approve a contribution (admin only)"""
    result = await ContributionService.update_contribution_status(
        contribution_id, "approved", admin_notes
    )
    logger.info(f"Contribution {contribution_id} approved by admin from {request.client.host}")
    return result

@app.post("/admin/contributions/{contribution_id}/reject")
async def admin_reject_contribution(
    contribution_id: str,
    request: Request,
    admin_notes: str | None = Form(None),
    _: bool = Depends(verify_admin_access)
):
    """Reject a contribution (admin only)"""
    result = await ContributionService.update_contribution_status(
        contribution_id, "rejected", admin_notes
    )
    logger.info(f"Contribution {contribution_id} rejected by admin from {request.client.host}")
    return result

@app.get("/health")
async def health_check():
    """Application health check endpoint"""
    health = await HealthService.full_health_check()
    
    # Return appropriate status code
    status_code = 200 if health["status"] == "healthy" else 503
    
    return JSONResponse(
        content=health,
        status_code=status_code
    )

@app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with all service information"""
    health = await HealthService.get_detailed_status()
    
    status_code = 200 if health["application"]["status"] == "healthy" else 503
    
    return JSONResponse(
        content=health,
        status_code=status_code
    )


@app.get("/sitemap.xml")
async def sitemap():
    """Generate dynamic sitemap for SEO"""
    try:
        xml = await SitemapService.generate_sitemap()
        return Response(content=xml, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error generating sitemap: {e}")
        # Return empty sitemap on error
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',
            media_type="application/xml"
        )


@app.get("/robots.txt")
async def robots():
    """Generate robots.txt for search engines"""
    robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /favorites
Disallow: /search

# Crawl delay
Crawl-delay: 1

# Sitemap
Sitemap: {SITE_URL}/sitemap.xml

# Specific rules for common bots
User-agent: Googlebot
Allow: /
Crawl-delay: 0

User-agent: Bingbot
Allow: /
Crawl-delay: 1
"""
    return Response(content=robots_content, media_type="text/plain")


# API endpoint for global search autocomplete
@app.get("/api/search/autocomplete")
async def global_search_autocomplete(q: str = Query(..., min_length=2)):
    """API endpoint for global search autocomplete across all categories"""
    from app.api.wordpress import get_posts
    
    # Run searches in parallel for all categories
    tasks = []
    category_map = []
    
    for category, post_type in POST_TYPES.items():
        # Fetch up to 10 items per category to get more candidates for ranking
        tasks.append(get_posts(post_type, search=q, per_page=10))
        category_map.append(category)
    
    results_by_category = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_candidates = []
    
    for i, results in enumerate(results_by_category):
        category_name = category_map[i]
        
        if isinstance(results, Exception) or not results:
            continue
            
        for item in results:
            # Format label for category
            category_label = category_name.replace('_', ' ').title()
            if category_label.endswith('s'):
                category_label = category_label[:-1]
            category_label = tr(category_label)
                
            # Calculate relevance score
            title = item.get("title", {}).get("rendered", "").strip()
            score = 0
            
            # 1. Exact match (case-insensitive) - Highest priority
            if title.lower() == q.lower():
                score = 100
            # 2. Starts with query - High priority
            elif title.lower().startswith(q.lower()):
                score = 50
            # 3. Contains query as a word - Medium priority
            elif f" {q.lower()} " in f" {title.lower()} ":
                score = 25
            # 4. Contains query as substring - Low priority
            elif q.lower() in title.lower():
                score = 10
            
            # Bonus: Shorter titles might be more relevant for exact/prefix matches
            # Subtract a small amount based on length to break ties favor of shorter titles
            length_penalty = min(len(title) * 0.1, 5) # Max 5 points penalty
            final_score = score - length_penalty
            
            all_candidates.append({
                "id": item.get("id"),
                "title": title,
                "slug": item.get("slug", ""),
                "category": category_name,
                "category_label": category_label,
                "image": item.get("_embedded", {}).get("wp:featuredmedia", [{}])[0].get("source_url", "") if item.get("_embedded") and "wp:featuredmedia" in item.get("_embedded", {}) else "",
                "_score": final_score
            })
    
    # Sort by score descending
    all_candidates.sort(key=lambda x: x["_score"], reverse=True)
    
    # Return top 10 most relevant results, removing the internal score
    final_results = []
    for candidate in all_candidates[:10]:
        candidate_copy = candidate.copy()
        del candidate_copy["_score"]
        final_results.append(candidate_copy)
        
    return final_results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)