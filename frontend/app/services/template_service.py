"""
Template Service - Handles template data preparation and rendering logic
"""
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.utils.helpers import get_meta_data, get_google_maps_api_key, format_opening_hours, generate_schema_markup
from app.utils.favorites import get_favorites


class TemplateService:
    """Service class for handling template-related operations"""
    
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
    def prepare_home_template_data(
        commons: Dict[str, Any],
        featured_items: Dict[str, Any],
        locations: str
    ) -> Dict[str, Any]:
        """Prepare template data for home page"""
        return {
            **commons,
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
        return {
            **commons,
            "meta": get_meta_data(
                title=f"{category_name.replace('_', ' ').title()} in Veria",
                description=f"Discover the best {category_name.replace('_', ' ')} in Veria, Greece"
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
        location_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare template data for item detail pages"""
        item = item_data['item']
        acf_fields = item_data['acf_fields']
        
        # Format opening hours if available
        opening_hours = format_opening_hours(acf_fields.get("opening_hours", {}))
        
        # Generate schema markup
        schema_markup = generate_schema_markup(post_type_name, item)
        
        template_data = {
            **commons,
            "meta": get_meta_data(
                title=item_data['title'],
                description=item_data['description'],
                image=item_data['featured_image'],
                type="article"
            ),
            "category": category_name,
            "item": item,
            "content": item_data['content'],
            "schema_markup": schema_markup,
            "opening_hours": opening_hours,
            "featured_image": item_data['featured_image'],
            "acf": acf_fields
        }
        
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
                description=f"Search results for '{query}' in Veria Guide"
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
                description="Get in touch with the VeriaGuide team"
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
                description="Your saved favorite places in Veria"
            ),
            "favorites": favorites
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
                description="Explore Veria's attractions, restaurants, and more on our interactive map"
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
                title="Religious Sites Map",
                description="Explore religious sites in Veria on the map"
            ),
            "items": items,
            "locations": locations
        }