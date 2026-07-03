"""
Template Service - Handles template data preparation and rendering logic
"""
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.utils.helpers import (
    get_meta_data,
    get_page_url,
    enhance_religious_site_description,
    enhance_religious_site_meta_title,
    get_religious_site_seo_intro,
    generate_religious_site_breadcrumb_schema,
    get_google_maps_api_key,
    format_opening_hours,
    generate_schema_markup,
    HOME_SEO_TITLE,
    HOME_SEO_DESCRIPTION,
    get_homepage_og_image_url,
    generate_homepage_schema,
)
from app.services.homepage_service import get_active_category_filters
from app.utils.favorites import get_favorites


class TemplateService:
    """Service class for handling template-related operations"""

    HOME_SEO = {
        "title": HOME_SEO_TITLE,
        "description": HOME_SEO_DESCRIPTION,
    }

    CATEGORY_SEO = {
        "religious_sites": {
            "title": "Byzantine Churches & Monasteries in Veria, Greece",
            "description": (
                "Explore Byzantine churches and monasteries in Veria (Veroia), Imathia — "
                "including sites linked to Apostle Paul. Visiting hours, maps and travel guide."
            ),
        },
    }
    
    def __init__(self, templates: Jinja2Templates):
        self.templates = templates
    
    @staticmethod
    def get_common_template_data(request: Request) -> Dict[str, Any]:
        """Get common data for all templates"""
        return {
            "request": request,
            "meta": get_meta_data(),
            "favorites": get_favorites(request),
            "google_maps_api_key": get_google_maps_api_key()
        }
    
    @staticmethod
    def _category_list_meta(category_name: str, request: Request) -> Dict[str, str]:
        """Category-specific SEO meta for listing pages."""
        seo = TemplateService.CATEGORY_SEO.get(category_name)
        if seo:
            return {
                "title": seo["title"],
                "description": seo["description"],
                "url": get_page_url(request.url.path),
            }
        label = category_name.replace("_", " ")
        return {
            "title": f"{label.title()} in Veria, Greece",
            "description": f"Discover the best {label} in Veria (Veroia), Imathia, Greece.",
            "url": get_page_url(request.url.path),
        }

    @staticmethod
    def prepare_home_template_data(
        commons: Dict[str, Any],
        featured_items: Dict[str, Any],
        locations: str
    ) -> Dict[str, Any]:
        """Prepare template data for home page"""
        request = commons["request"]
        return {
            **commons,
            "meta": get_meta_data(
                title=TemplateService.HOME_SEO["title"],
                description=TemplateService.HOME_SEO["description"],
                image=get_homepage_og_image_url(),
                url=get_page_url("/"),
            ),
            "schema_markup": generate_homepage_schema(TemplateService.HOME_SEO["description"]),
            "featured_items": featured_items,
            "locations": locations
        }
    
    @staticmethod
    def prepare_category_list_template_data(
        commons: Dict[str, Any],
        category_name: str,
        content_data: Dict[str, Any],
        page: int,
        search_term: Optional[str],
        denominations_selected: list,
        rating_selected: str
    ) -> Dict[str, Any]:
        """Prepare template data for category listing pages"""
        request = commons["request"]
        list_meta = TemplateService._category_list_meta(category_name, request)
        return {
            **commons,
            "meta": get_meta_data(
                title=list_meta["title"],
                description=list_meta["description"],
                url=list_meta["url"],
            ),
            "category": category_name,
            "items": content_data['items'],
            "page": page,
            "has_next": content_data['has_next'],
            "has_prev": content_data['has_prev'],
            "search_term": search_term,
            "denominations_selected": denominations_selected,
            "rating_selected": rating_selected,
            "rating_counts": content_data['rating_counts'],
            "total_count": content_data['total_count'],
            "per_page": content_data.get('per_page', 12),
            "locations": content_data['locations'],
            "tag_counts": content_data['tag_counts'],
            "total_pages": content_data['total_pages']
        }
    
    @staticmethod
    def prepare_item_detail_template_data(
        commons: Dict[str, Any],
        category_name: str,
        post_type_name: str,
        item_data: Dict[str, Any],
        location_data: Optional[Dict[str, Any]] = None,
        related_items: Optional[list] = None,
        nearby_items: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Prepare template data for item detail pages"""
        item = item_data['item']
        acf_fields = item_data['acf_fields']
        request = commons["request"]

        description = item_data['description']
        meta_title = item_data['title']
        breadcrumb_schema = None
        seo_intro = None
        if post_type_name == "religious_site":
            description = enhance_religious_site_description(item_data['title'], description)
            meta_title = enhance_religious_site_meta_title(item_data['title'])
            seo_intro = get_religious_site_seo_intro(
                item_data['title'], item_data['description'], item_data['content']
            )
            breadcrumb_schema = generate_religious_site_breadcrumb_schema(
                item_data['title'], item.get("slug", "")
            )
        
        # Format opening hours if available
        opening_hours = format_opening_hours(acf_fields.get("opening_hours", {}))
        
        # Generate schema markup
        schema_markup = generate_schema_markup(post_type_name, item)
        
        template_data = {
            **commons,
            "meta": get_meta_data(
                title=meta_title,
                description=description,
                image=item_data['featured_image'],
                type="article",
                url=get_page_url(request.url.path),
            ),
            "category": category_name,
            "post_type": post_type_name,
            "item": item,
            "content": item_data['content'],
            "schema_markup": schema_markup,
            "opening_hours": opening_hours,
            "featured_image": item_data['featured_image'],
            "acf": acf_fields,
            "related_items": related_items or [],
            "nearby_items": nearby_items or [],
        }

        if post_type_name == "religious_site":
            template_data["seo_intro"] = seo_intro
            template_data["breadcrumb_schema"] = breadcrumb_schema
        
        # Add location data if available
        if location_data:
            template_data["location"] = location_data
        
        return template_data
    
    @staticmethod
    def prepare_search_template_data(
        commons: Dict[str, Any],
        query: Optional[str],
        content_type: Optional[str],
        search_data: Dict,
        page: int,
        items_per_page: int
    ) -> Dict[str, Any]:
        """Prepare template data for search results"""
        # Handle both old list format and new dict format
        if isinstance(search_data, dict):
            results = search_data.get('results', [])
            has_next = search_data.get('has_next', False)
            has_prev = search_data.get('has_prev', False)
            total = search_data.get('total', 0)
        else:
            # Fallback for old format
            results = search_data
            has_next = len(results) == items_per_page
            has_prev = page > 1
            total = len(results)
        
        return {
            **commons,
            "meta": get_meta_data(
                title=f"Search results for '{query}'",
                description=f"Search results for '{query}' in Veria Guide",
                url=get_page_url(commons["request"].url.path),
            ),
            "results": results,
            "query": query,
            "type": content_type,
            "page": page,
            "has_next": has_next,
            "has_prev": has_prev,
            "total_results": total,
            "per_page": items_per_page
        }
    
    @staticmethod
    def prepare_contact_template_data(
        commons: Dict[str, Any],
        success: Optional[bool] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare template data for contact form"""
        template_data = {
            **commons,
            "meta": get_meta_data(
                title="Contact Us",
                description="Get in touch with the VeriaGuide team",
                url=get_page_url(commons["request"].url.path),
            )
        }
        
        if success is not None:
            template_data["success"] = success
            template_data["message"] = message
        
        return template_data
    
    @staticmethod
    def prepare_favorites_template_data(
        commons: Dict[str, Any],
        favorites: list
    ) -> Dict[str, Any]:
        """Prepare template data for favorites page"""
        return {
            **commons,
            "meta": get_meta_data(
                title="My Favorites",
                description="Your saved favorite places in Veria",
                url=get_page_url(commons["request"].url.path),
            ),
            "favorites": favorites,
            "active_category_filters": get_active_category_filters(),
        }
    
    @staticmethod
    def prepare_map_template_data(
        commons: Dict[str, Any],
        locations: str,
        selected_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepare template data for map view"""
        return {
            **commons,
            "meta": get_meta_data(
                title="Interactive Map of Veria",
                description="Explore Veria's attractions, restaurants, and more on our interactive map",
                url=get_page_url(commons["request"].url.path),
            ),
            "locations": locations,
            "selected_type": selected_type
        }
    
    @staticmethod
    def prepare_religious_sites_map_template_data(
        commons: Dict[str, Any],
        items: list,
        locations: list
    ) -> Dict[str, Any]:
        """Prepare template data for religious sites map"""
        return {
            **commons,
            "meta": get_meta_data(
                title="Byzantine Churches Map – Veria, Greece",
                description=(
                    "Map of Byzantine churches and monasteries in Veria (Veroia), Imathia, Greece. "
                    "Find sacred sites, plan visits and explore Apostle Paul's legacy."
                ),
                url=get_page_url(commons["request"].url.path),
            ),
            "items": items,
            "locations": locations
        }

    @staticmethod
    def get_placeholder_image_url(category: str) -> str:
        """Get appropriate placeholder image URL for category"""
        placeholders = {
            'restaurant': '/static/img/placeholder-restaurant.svg',
            'museum': '/static/img/placeholder-museum.svg',
            'religious_site': '/static/img/placeholder-church.svg',
            'archaeological_site': '/static/img/placeholder-museum.svg',
            'hiking_trail': '/static/img/placeholder-default.svg',
            'cafe': '/static/img/placeholder-restaurant.svg',
            'accommodation': '/static/img/placeholder-default.svg',
            'ski_resort': '/static/img/placeholder-default.svg',
            'tour': '/static/img/placeholder-default.svg',
            'hidden_gem': '/static/img/placeholder-default.svg',
            'default': '/static/img/placeholder-default.svg'
        }
        
        return placeholders.get(category, placeholders['default'])
    
    @staticmethod
    def get_item_image_url(item: Dict[str, Any], category: str = 'default') -> str:
        """Get item image URL with fallback to category-specific placeholder"""
        # Try to get featured media from WordPress
        if (item.get('_embedded') and 
            'wp:featuredmedia' in item['_embedded'] and 
            item['_embedded']['wp:featuredmedia']):
            return item['_embedded']['wp:featuredmedia'][0].get('source_url', '')
        
        # Fallback to category-specific placeholder
        return TemplateService.get_placeholder_image_url(category)