"""
Accommodation Service - Handles accommodation data and ACF fields
"""
from typing import Dict, List, Any, Optional
from app.services.content_service import ContentService
from app.services.cache_service import CacheService
from app.utils.logging_config import get_logger

logger = get_logger("accommodation")


class AccommodationService:
    """Service for managing accommodation data with ACF fields"""
    
    # ACF field names for accommodations
    ACF_FIELDS = {
        "seo_title": "seo_tittle",
        "seo_description": "seo_description",
        "ratings": "ratings",
        "reviews": "reviews",
        "category": "category",
        "price_range": "price_range",
        "amenities": "amenities",
        "check_in": "check_in",
        "check_out": "check_out",
        "rooms": "rooms",
        "phone": "phone",
        "email": "email",
        "website": "website",
        "address": "address",
        "location_map": "location_map",
    }
    
    @classmethod
    async def get_accommodations(
        cls,
        page: int = 1,
        per_page: int = 12,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of accommodations with ACF fields"""
        try:
            # Get accommodations from content service
            accommodations = await ContentService.get_category_items(
                post_type="accommodation",
                page=page,
                search=search
            )
            
            # Enrich with ACF fields
            if accommodations.get("items"):
                for item in accommodations["items"]:
                    item["acf"] = await cls._extract_acf_fields(item)
            
            return accommodations
            
        except Exception as e:
            logger.error(f"Error getting accommodations: {e}")
            return {"items": [], "total_count": 0, "total_pages": 0}
    
    @classmethod
    async def get_accommodation_detail(cls, slug: str) -> Optional[Dict[str, Any]]:
        """Get single accommodation with full ACF data"""
        try:
            # Get accommodation from content service
            accommodation = await ContentService.get_item_by_slug(
                post_type="accommodation",
                slug=slug
            )
            
            if not accommodation:
                return None
            
            # Extract and enrich ACF fields
            accommodation["acf"] = await cls._extract_acf_fields(accommodation)
            
            # Cache the result
            cache_key = f"accommodation:{slug}"
            await CacheService.set(cache_key, accommodation, ttl=3600)
            
            return accommodation
            
        except Exception as e:
            logger.error(f"Error getting accommodation detail: {e}")
            return None
    
    @classmethod
    async def _extract_acf_fields(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ACF fields from WordPress item"""
        acf_data = {}
        
        # Get ACF data from the item
        if "acf" in item:
            acf_raw = item["acf"]
            
            # Map ACF fields
            for display_name, field_name in cls.ACF_FIELDS.items():
                if field_name in acf_raw:
                    acf_data[display_name] = acf_raw[field_name]
        
        return acf_data
    
    @classmethod
    async def get_accommodation_amenities(cls, accommodation_id: int) -> List[str]:
        """Get amenities for an accommodation"""
        try:
            cache_key = f"accommodation:amenities:{accommodation_id}"
            cached = await CacheService.get(cache_key)
            
            if cached:
                return cached
            
            # Get from WordPress API
            from app.services.http_service import HTTPService
            from app.config import WP_API_URL
            
            response = await HTTPService.get(
                f"{WP_API_URL}/accommodation/{accommodation_id}?_fields=acf.amenities"
            )
            
            if response.status_code == 200:
                data = response.json()
                amenities = data.get("acf", {}).get("amenities", [])
                
                # Cache the result
                await CacheService.set(cache_key, amenities, ttl=3600)
                
                return amenities if isinstance(amenities, list) else []
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting amenities: {e}")
            return []
    
    @classmethod
    async def get_accommodation_location(cls, accommodation_id: int) -> Optional[Dict[str, Any]]:
        """Get location map data for an accommodation"""
        try:
            cache_key = f"accommodation:location:{accommodation_id}"
            cached = await CacheService.get(cache_key)
            
            if cached:
                return cached
            
            # Get from WordPress API
            from app.services.http_service import HTTPService
            from app.config import WP_API_URL
            
            response = await HTTPService.get(
                f"{WP_API_URL}/accommodation/{accommodation_id}?_fields=acf.location_map"
            )
            
            if response.status_code == 200:
                data = response.json()
                location = data.get("acf", {}).get("location_map")
                
                if location:
                    # Cache the result
                    await CacheService.set(cache_key, location, ttl=3600)
                    return location
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting location: {e}")
            return None
    
    @classmethod
    async def search_accommodations(
        cls,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search accommodations with optional filters"""
        try:
            # Build search parameters
            params = {
                "search": query,
                "per_page": 50
            }
            
            # Add category filter if provided
            if filters and "category" in filters:
                params["category"] = filters["category"]
            
            # Get accommodations
            accommodations = await ContentService.get_items(
                post_type="accommodation",
                **params
            )
            
            # Enrich with ACF fields
            if accommodations.get("items"):
                for item in accommodations["items"]:
                    item["acf"] = await cls._extract_acf_fields(item)
            
            return accommodations.get("items", [])
            
        except Exception as e:
            logger.error(f"Error searching accommodations: {e}")
            return []
