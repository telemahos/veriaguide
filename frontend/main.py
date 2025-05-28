import os
import json
from typing import Optional
from fastapi import FastAPI, Request, Response, Form, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime

from app.config import ITEMS_PER_PAGE, POST_TYPES
from app.api.wordpress import (
    get_posts, get_post, get_all_locations, clear_cache, submit_contact_form
)
from app.utils.helpers import (
    get_meta_data, get_featured_image, strip_tags, generate_schema_markup,
    format_opening_hours, get_google_maps_api_key
)
from app.utils.favorites import (
    get_favorites, add_favorite, remove_favorite, clear_favorites
)
import math

# Initialize FastAPI app
app = FastAPI(
    title="VeriaGuide",
    description="A tourism directory for Veria, Greece",
    version="1.0.0"
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 Templates
templates = Jinja2Templates(directory="templates")

# Add 'now' to Jinja2 globals
templates.env.globals.update(now=datetime.utcnow)

# Common dependencies
def get_common_template_data(request: Request):
    """Get common data for all templates"""
    return {
        "request": request,
        "meta": get_meta_data(),
        "favorites": get_favorites(request),
        "google_maps_api_key": get_google_maps_api_key()
    }

# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, commons: dict = Depends(get_common_template_data)):
    # Get featured items from each category
    featured_items = {}
    
    for category, post_type in POST_TYPES.items():
        featured_items[category] = get_posts(post_type, per_page=4)
    
    # Get all locations for the map
    locations = get_all_locations()
    
    # Prepare template data
    template_data = {
        **commons,
        "featured_items": featured_items,
        "locations": json.dumps(locations)
    }
    
    return templates.TemplateResponse("base/index.html", template_data)

# Special route for religious sites map (must come before other religious_sites routes)
@app.get("/religious_sites/map", response_class=HTMLResponse)
async def religious_sites_map_listing(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    # Fetch religious sites data
    religious_sites_items = get_posts("religious_site", per_page=100) # Fetch more items for the map view

    # Prepare template data
    template_data = {
        **commons,
        "meta": get_meta_data(
            title="Religious Sites Map",
            description="Explore religious sites in Veria on the map"
        ),
        "items": religious_sites_items,
        "locations": [
            {"id": item.get("id"), "title": item.get("title", {}).get("rendered", ""), "slug": item.get("slug"), "acf": item.get("acf", {}), "featured_image": get_featured_image(item), "excerpt": strip_tags(item.get("excerpt", {}).get("rendered", ""))}
            for item in religious_sites_items if item.get("acf", {}).get("location_map")
        ] # Pass location data for map markers, including image and excerpt
    }

    return templates.TemplateResponse("religious_sites/map-listings.html", template_data)


# Create routes for each location type
for category, post_type in POST_TYPES.items():
    
    # List page route
    @app.get(f"/{category}", response_class=HTMLResponse)
    async def list_items(
        request: Request,
        category_name=category,
        post_type_name=post_type,
        page: int = Query(1, ge=1),
        search: Optional[str] = None,
        commons: dict = Depends(get_common_template_data)
    ):
        # Get items from WordPress
        items = get_posts(
            post_type_name,
            page=page,
            per_page=ITEMS_PER_PAGE,
            search=search
        )
        
        # Get items again to build detailed location data for the map
        # (Alternatively, modify get_posts to return all necessary fields directly)
        all_items_for_map = get_posts(post_type_name, per_page=100) # Fetch more items for the map view

        # Prepare detailed location data for the map
        locations_for_map = [
            {"id": item.get("id"), "title": item.get("title", {}).get("rendered", ""), "slug": item.get("slug"), "acf": item.get("acf", {}), "featured_image": get_featured_image(item), "excerpt": strip_tags(item.get("excerpt", {}).get("rendered", ""))}
            for item in all_items_for_map if item.get("acf", {}).get("location_map")
        ]

        # Compute total count of items for this category (for header display)
        all_items = get_posts(post_type_name, per_page=100, search=search)
        total_count = len(all_items)

        # Compute total_pages for pagination
        total_pages = math.ceil(total_count / ITEMS_PER_PAGE) if total_count and ITEMS_PER_PAGE else 1

        # Prepare template data
        template_data = {
            **commons,
            "meta": get_meta_data(
                title=f"{category_name.replace('_', ' ').title()} in Veria",
                description=f"Discover the best {category_name.replace('_', ' ')} in Veria, Greece"
            ),
            "category": category_name,
            "items": items, # Use paginated items for the list view
            "page": page,
            "has_next": len(items) == ITEMS_PER_PAGE,
            "has_prev": page > 1,
            "search_term": search,
            "total_count": total_count,
            "per_page": ITEMS_PER_PAGE,
            "locations": locations_for_map, # Pass the detailed location data
            "total_pages": total_pages
        }
        
        return templates.TemplateResponse(f"{category_name}/list.html", template_data)
    
    # Detail page route
    @app.get(f"/{category}/{{slug}}", response_class=HTMLResponse)
    async def item_detail(
        request: Request,
        slug: str,
        category_name=category,
        post_type_name=post_type,
        commons: dict = Depends(get_common_template_data)
    ):
        print(f"--- item_detail route called for category: {category_name}, slug: {slug} ---") # DEBUG Line
        # Get item from WordPress
        item = get_post(post_type_name, slug)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Extract data from item
        title = item.get("title", {}).get("rendered", "")
        description = strip_tags(item.get("excerpt", {}).get("rendered", ""))
        content = item.get("content", {}).get("rendered", "")
        featured_image = get_featured_image(item)
        
        # Extract ACF fields
        acf_fields = item.get("acf", {})
        
        # Format opening hours if available
        opening_hours = format_opening_hours(acf_fields.get("opening_hours", {}))

        # Get tags - they come as an array of tag IDs
        # tag_ids = item.get("tags", [])
        # tag_names = [tag.get("name") for tag in tag_ids]
        
        # Generate schema markup
        schema_markup = generate_schema_markup(post_type_name, item)
        
        # Prepare template data
        template_data = {
            **commons,
            "meta": get_meta_data(
                title=title,
                description=description,
                image=featured_image,
                type="article"
            ),
            "category": category_name,
            "item": item,
            "content": content,
            "schema_markup": schema_markup,
            "opening_hours": opening_hours,
            "featured_image": featured_image,
            "acf": acf_fields
            # "tags": tag_names
        }
        
        # Add location data for map if available, prioritizing specific fields then general 'location_map'
        # The templates themselves will primarily use acf.location_map or acf.specific_map_field directly.
        # This 'location' variable is more of a fallback or for generic use if a template expects it.
        primary_map_field_name = None
        if category_name == "tours":
            primary_map_field_name = "meeting_point_map"
        elif category_name == "hiking_trails":
            primary_map_field_name = "trail_map"
        else:
            primary_map_field_name = "location_map" # Default for most CPTs

        map_data_to_use = None
        if primary_map_field_name and primary_map_field_name in acf_fields:
            map_data_to_use = acf_fields[primary_map_field_name]
        elif "location_map" in acf_fields: # Fallback to generic location_map
             map_data_to_use = acf_fields["location_map"]
        elif "location" in acf_fields: # Fallback to even older 'location'
            map_data_to_use = acf_fields["location"]

        if map_data_to_use and isinstance(map_data_to_use, dict) and "lat" in map_data_to_use and "lng" in map_data_to_use:
            template_data["location"] = {
                "lat": map_data_to_use.get("lat"),
                "lng": map_data_to_use.get("lng"),
                "address": map_data_to_use.get("address"), # Include address if available
                "zoom": map_data_to_use.get("zoom") # Include zoom if available
            }
        
        return templates.TemplateResponse(f"{category_name}/detail.html", template_data)
    

@app.get("/archaeologicals", response_class=HTMLResponse)
async def list_archaeologicals(request: Request):
    archaeological_posts = get_posts("archaeological", per_page=10)
    
    # Meta-Daten definieren
    meta_data = {
        "title": "Archäologische Stätten",
        "description": "Entdecken Sie die archäologischen Stätten in Veria."
    }
    
    return templates.TemplateResponse("archaeologicals/list.html", {
        "request": request,
        "posts": archaeological_posts,
        "meta": meta_data  # Hier die meta-Daten hinzufügen
    })

# Search page
@app.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: Optional[str] = None,
    type: Optional[str] = None,
    page: int = Query(1, ge=1),
    commons: dict = Depends(get_common_template_data)
):
    results = []
    
    if q:
        # If type is specified, search only in that type
        if type and type in POST_TYPES:
            post_type = POST_TYPES[type]
            results = get_posts(post_type, search=q, page=page, per_page=ITEMS_PER_PAGE)
        else:
            # Search in all post types
            for post_type in POST_TYPES.values():
                items = get_posts(post_type, search=q, per_page=10)
                results.extend(items)
    
    # Prepare template data
    template_data = {
        **commons,
        "meta": get_meta_data(
            title=f"Search results for '{q}'",
            description=f"Search results for '{q}' in Veria Guide"
        ),
        "results": results,
        "query": q,
        "type": type,
        "page": page,
        "has_next": len(results) == ITEMS_PER_PAGE,
        "has_prev": page > 1
    }
    
    return templates.TemplateResponse("search/results.html", template_data)

# Contact form
@app.get("/contact", response_class=HTMLResponse)
async def contact_form(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    template_data = {
        **commons,
        "meta": get_meta_data(
            title="Contact Us",
            description="Get in touch with the VeriaGuide team"
        )
    }
    
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
    # Submit contact form
    result = submit_contact_form(name, email, subject, message)
    
    template_data = {
        **commons,
        "meta": get_meta_data(
            title="Contact Us",
            description="Get in touch with the VeriaGuide team"
        ),
        "success": result.get("success", False),
        "message": result.get("message", "")
    }
    
    return templates.TemplateResponse("contact/form.html", template_data)

# Favorites
@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(
    request: Request,
    commons: dict = Depends(get_common_template_data)
):
    favorites = get_favorites(request)
    
    template_data = {
        **commons,
        "meta": get_meta_data(
            title="My Favorites",
            description="Your saved favorite places in Veria"
        ),
        "favorites": favorites
    }
    
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
    favorites = add_favorite(response, item_id, item_type, item_title, item_image)
    return {"success": True, "favorites": favorites}

@app.post("/favorites/remove")
async def remove_from_favorites(
    request: Request,
    response: Response,
    item_id: str = Form(...)
):
    favorites = remove_favorite(response, item_id)
    return {"success": True, "favorites": favorites}

@app.post("/favorites/clear")
async def clear_all_favorites(
    request: Request,
    response: Response
):
    clear_favorites(response)
    return {"success": True, "favorites": []}

# Map view
@app.get("/map", response_class=HTMLResponse)
async def map_view(
    request: Request,
    type: Optional[str] = None,
    commons: dict = Depends(get_common_template_data)
):
    # Get locations for map
    locations = get_all_locations(type)
    
    template_data = {
        **commons,
        "meta": get_meta_data(
            title="Interactive Map of Veria",
            description="Explore Veria's attractions, restaurants, and more on our interactive map"
        ),
        "locations": json.dumps(locations),
        "selected_type": type
    }
    
    return templates.TemplateResponse("base/map.html", template_data)

# Clear cache (admin only route in a real app)
@app.get("/admin/clear-cache")
async def admin_clear_cache():
    clear_cache()
    return {"success": True, "message": "Cache cleared successfully"}

# Sitemap
@app.get("/sitemap.xml")
async def sitemap():
    # In a real app, this would generate a proper XML sitemap
    return Response(
        content="<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'></urlset>",
        media_type="application/xml"
    )

# Robots.txt
@app.get("/robots.txt")
async def robots():
    return Response(
        content="""User-agent: *
Allow: /
Sitemap: https://veriaguide.com/sitemap.xml""",
        media_type="text/plain"
    )

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
