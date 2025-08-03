"""
Refactored main.py using service classes for better separation of concerns
"""
import os
import json
from typing import Optional, List
from fastapi import FastAPI, Request, Response, Form, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.config import ITEMS_PER_PAGE, POST_TYPES
from app.api.wordpress import clear_cache
from app.services.cache_service import CacheService
from app.services.content_service import ContentService
from app.services.template_service import TemplateService
from app.services.contact_service import ContactService
from app.services.favorites_service import FavoritesService

# Initialize FastAPI app
app = FastAPI(
    title="VeriaGuide",
    description="A tourism directory for Veria, Greece",
    version="1.0.0"
)

# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Test Redis connection
    redis_healthy = await CacheService.health_check()
    if redis_healthy:
        print("✅ Redis connection established successfully")
    else:
        print("⚠️ Redis connection failed - caching will be disabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await CacheService.close_redis()
    print("🔌 Redis connection closed")

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


@app.get("/religious_sites/map", response_class=HTMLResponse)
async def religious_sites_map_listing(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    """Special route for religious sites map"""
    from app.api.wordpress import get_posts
    
    religious_sites_items = await get_posts("religious_site", per_page=100)
    locations = ContentService._prepare_location_data(religious_sites_items)
    
    template_data = template_service.prepare_religious_sites_map_template_data(
        commons, religious_sites_items, locations
    )
    
    return templates.TemplateResponse("religious_sites/map-listings.html", template_data)


# Dynamic routes for each content type
for category, post_type in POST_TYPES.items():
    
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


@app.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: Optional[str] = None,
    type: Optional[str] = None,
    page: int = Query(1, ge=1),
    commons: dict = Depends(get_common_template_data)
):
    """Search across content types"""
    results = []
    
    if q:
        results = await content_service.search_content(q, type, page)
    
    template_data = template_service.prepare_search_template_data(
        commons, q, type, results, page, ITEMS_PER_PAGE
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
    commons: dict = Depends(get_common_template_data)
):
    """Submit contact form"""
    result = await contact_service.submit_contact_form(name, email, subject, message)
    
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
        response, item_id, item_type, item_title, item_image
    )


@app.post("/favorites/remove")
async def remove_from_favorites(
    request: Request,
    response: Response,
    item_id: str = Form(...)
):
    """Remove item from favorites"""
    return favorites_service.remove_from_favorites(response, item_id)


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


# Admin and utility routes
@app.get("/admin/clear-cache")
async def admin_clear_cache():
    """Clear application cache"""
    await clear_cache()
    return {"success": True, "message": "Cache cleared successfully"}

@app.get("/admin/cache-info")
async def admin_cache_info():
    """Get cache information and statistics"""
    cache_info = await CacheService.get_cache_info()
    return cache_info

@app.get("/admin/cache-health")
async def admin_cache_health():
    """Check cache health"""
    is_healthy = await CacheService.health_check()
    return {"healthy": is_healthy, "service": "Redis"}

@app.post("/admin/clear-cache/{pattern}")
async def admin_clear_cache_pattern(pattern: str):
    """Clear cache entries matching a pattern"""
    deleted_count = await CacheService.delete_pattern(pattern)
    return {"success": True, "deleted_keys": deleted_count, "pattern": pattern}


@app.get("/sitemap.xml")
async def sitemap():
    """Generate sitemap"""
    return Response(
        content="<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'></urlset>",
        media_type="application/xml"
    )


@app.get("/robots.txt")
async def robots():
    """Generate robots.txt"""
    return Response(
        content="""User-agent: *
Allow: /
Sitemap: https://veriaguide.com/sitemap.xml""",
        media_type="text/plain"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)