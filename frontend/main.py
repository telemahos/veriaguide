"""
Refactored main.py using service classes for better separation of concerns
"""
import os
import json
import time
from typing import Optional, List
from fastapi import FastAPI, Request, Response, Form, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime

from app.config import (
    ITEMS_PER_PAGE, POST_TYPES, APP_NAME, APP_DESCRIPTION, APP_VERSION,
    DEBUG, ALLOWED_HOSTS, validate_config, config, SITE_URL
)
from app.api.wordpress import clear_cache
from app.services.cache_service import CacheService
from app.services.http_service import HTTPService
import os
# Use production logging in production environment
if os.getenv('ENVIRONMENT') == 'production':
    from app.utils.logging_config_production import setup_logging, get_logger
else:
    from app.utils.logging_config import setup_logging, get_logger
from app.utils.validation import InputValidator
import asyncio
from app.middleware.security import (
    SecurityHeadersMiddleware, RateLimitMiddleware, RequestSizeLimitMiddleware, setup_cors_middleware
)
from app.middleware.error_handling import (
    http_exception_handler, general_exception_handler, validation_exception_handler
)
from app.services.content_service import ContentService
from app.services.template_service import TemplateService
from app.services.contact_service import ContactService
from app.services.favorites_service import FavoritesService
from app.services.cache_warming_service import CacheWarmingService
from app.services.sitemap_service import SitemapService
from app.services.metrics_service import MetricsService

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    debug=DEBUG
)

# Setup security middleware
setup_cors_middleware(app)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 requests per minute
app.add_middleware(RequestSizeLimitMiddleware, max_size=1024*1024)  # 1MB limit

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

# Initialize services
template_service = TemplateService(templates)
content_service = ContentService()
contact_service = ContactService()
favorites_service = FavoritesService()

# Template filters will be handled by JavaScript for now

# Common dependencies
def get_common_template_data(request: Request):
    """Get common data for all templates"""
    return template_service.get_common_template_data(request)


# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, commons: dict = Depends(get_common_template_data)):
    """Home page with featured items from all categories"""
    featured_items = await content_service.get_featured_items()
    locations = await content_service.get_map_locations()
    
    template_data = template_service.prepare_home_template_data(
        commons, featured_items, locations
    )
    
    return templates.TemplateResponse("base/index.html", template_data)


@app.get("/religious_sites", response_class=HTMLResponse)
async def religious_sites_list(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = None,
    denomination: List[str] = Query(None),
    guestRating: str = Query('any'),
    commons: dict = Depends(get_common_template_data)
):
    """Religious sites listing with filters"""
    logger.info(f"Religious sites request with filters: denomination={denomination}, rating={guestRating}")
    
    if search:
        search = InputValidator.validate_search_query(search)
    
    content_data = await content_service.get_category_items(
        "religious_site", page, search, denomination, guestRating
    )
    
    # Debug: Log the actual tag counts to see what tags exist
    logger.info(f"Available tags: {list(content_data.get('tag_counts', {}).keys())}")
    
    template_data = template_service.prepare_category_list_template_data(
        commons, "religious_sites", content_data, page, search, denomination or [], guestRating
    )
    
    return templates.TemplateResponse("religious_sites/list.html", template_data)


@app.get("/religious_sites/map", response_class=HTMLResponse)
async def religious_sites_map_listing(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Special route for religious sites map"""
    from app.api.wordpress import get_all_posts_for_type
    
    religious_sites_items = await get_all_posts_for_type("religious_site")
    locations = ContentService._prepare_location_data(religious_sites_items)
    
    template_data = template_service.prepare_religious_sites_map_template_data(
        commons, religious_sites_items, locations
    )
    
    return templates.TemplateResponse("religious_sites/map-listings.html", template_data)


# Dynamic routes for each content type (excluding religious_sites which has its own route)
for category, post_type in POST_TYPES.items():
    if category == "religious_sites":
        continue  # Skip religious_sites as it has its own specialized route above
    
    @app.get(f"/{category}", response_class=HTMLResponse)
    async def list_items(
        request: Request,
        category_name=category,
        post_type_name=post_type,
        page: int = Query(1, ge=1),
        search: Optional[str] = None,
        denomination: List[str] = Query(None),
        guestRating: str = Query('any'),
        commons: dict = Depends(get_common_template_data)
    ):
        """List items for a specific category with filtering and pagination"""
        content_data = await content_service.get_category_items(
            post_type_name, page, search, denomination, guestRating
        )
        
        template_data = template_service.prepare_category_list_template_data(
            commons, category_name, content_data, page, search,
            denomination or [], guestRating
        )
        
        return templates.TemplateResponse(f"{category_name}/list.html", template_data)
    
    @app.get(f"/{category}/{{slug}}", response_class=HTMLResponse)
    async def item_detail(
        request: Request,
        slug: str,
        category_name=category,
        post_type_name=post_type,
        commons: dict = Depends(get_common_template_data)
    ):
        """Detail page for a specific item"""
        item_data = await content_service.get_item_detail(post_type_name, slug)
        
        if not item_data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        location_data = content_service.get_location_data_for_item(
            item_data['item'], category_name
        )
        
        template_data = template_service.prepare_item_detail_template_data(
            commons, category_name, post_type_name, item_data, location_data
        )
        
        return templates.TemplateResponse(f"{category_name}/detail.html", template_data)


# Add the religious_sites detail route separately since we excluded it from the loop
@app.get("/religious_sites/{slug}", response_class=HTMLResponse)
async def religious_sites_detail(
    request: Request,
    slug: str,
    commons: dict = Depends(get_common_template_data)
):
    """Detail page for religious sites"""
    item_data = await content_service.get_item_detail("religious_site", slug)
    
    if not item_data:
        raise HTTPException(status_code=404, detail="Religious site not found")
    
    location_data = content_service.get_location_data_for_item(
        item_data['item'], "religious_sites"
    )
    
    template_data = template_service.prepare_item_detail_template_data(
        commons, "religious_sites", "religious_site", item_data, location_data
    )
    
    return templates.TemplateResponse("religious_sites/detail.html", template_data)


@app.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: Optional[str] = None,
    type: Optional[str] = None,
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
    
    return templates.TemplateResponse("search/results.html", template_data)


@app.get("/contact", response_class=HTMLResponse)
async def contact_form(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Contact form page"""
    template_data = template_service.prepare_contact_template_data(commons)
    return templates.TemplateResponse("contact/form.html", template_data)


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
    
    return templates.TemplateResponse("contact/form.html", template_data)


@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Favorites page"""
    favorites = favorites_service.get_user_favorites(request)
    template_data = template_service.prepare_favorites_template_data(commons, favorites)
    return templates.TemplateResponse("favorites/list.html", template_data)


@app.post("/favorites/add")
async def add_to_favorites(
    request: Request,
    response: Response,
    item_id: str = Form(...),
    item_type: str = Form(...),
    item_title: str = Form(...),
    item_image: Optional[str] = Form(None)
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
    type: Optional[str] = None,
    commons: dict = Depends(get_common_template_data)
):
    """Interactive map view"""
    locations = await content_service.get_map_locations(type)
    template_data = template_service.prepare_map_template_data(commons, locations, type)
    return templates.TemplateResponse("base/map.html", template_data)


# Legacy route - should be refactored to use services
@app.get("/archaeologicals", response_class=HTMLResponse)
async def list_archaeologicals(request: Request):
    """Legacy archaeological sites route - TODO: refactor to use services"""
    from app.api.wordpress import get_posts
    from app.utils.helpers import get_meta_data
    
    archaeological_posts = await get_posts("archaeological", per_page=10)
    
    meta_data = {
        "title": "Archäologische Stätten",
        "description": "Entdecken Sie die archäologischen Stätten in Veria."
    }
    
    return templates.TemplateResponse("archaeologicals/list.html", {
        "request": request,
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

@app.get("/health")
async def health_check():
    """Application health check endpoint"""
    redis_healthy = await CacheService.health_check()
    
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "version": APP_VERSION,
        "environment": config.__class__.__name__,
        "services": {
            "redis": "healthy" if redis_healthy else "unhealthy",
            "http": "healthy"
        }
    }


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
Disallow: /static/
Disallow: /favorites

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)