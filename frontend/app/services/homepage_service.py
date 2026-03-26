"""
Homepage Service - Fetches homepage section settings from WordPress
"""
from typing import List, Dict, Any, Optional
from app.services.http_service import HTTPService
from app.services.cache_service import CacheService
from app.utils.logging_config import get_logger

logger = get_logger("homepage")

# Default sections if WordPress settings are unavailable
DEFAULT_SECTIONS = [
    {"category": "museums", "post_type": "museum", "title": "Museums", "enabled": True, "items_count": 4, "order": 1, "view_all_link": "/museums"},
    {"category": "archaeological_sites", "post_type": "archaeological_site", "title": "Archaeological Sites", "enabled": True, "items_count": 4, "order": 2, "view_all_link": "/archaeological_sites"},
    {"category": "religious_sites", "post_type": "religious_site", "title": "Churches & Monasteries", "enabled": True, "items_count": 4, "order": 3, "view_all_link": "/religious_sites"},
    {"category": "restaurants", "post_type": "restaurant", "title": "Restaurants", "enabled": True, "items_count": 4, "order": 4, "view_all_link": "/restaurants"},
    {"category": "cafes", "post_type": "cafe", "title": "Cafés", "enabled": True, "items_count": 4, "order": 5, "view_all_link": "/cafes"},
    {"category": "accommodations", "post_type": "accommodation", "title": "Accommodations", "enabled": True, "items_count": 4, "order": 6, "view_all_link": "/accommodations"},
    {"category": "ski_resorts", "post_type": "ski_resort", "title": "Ski Resorts", "enabled": True, "items_count": 4, "order": 7, "view_all_link": "/ski_resorts"},
]


class HomepageService:
    """Service for fetching and caching homepage settings from WordPress"""

    CACHE_KEY = "homepage_settings"
    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    async def get_homepage_sections() -> List[Dict[str, Any]]:
        """
        Fetch homepage section settings from WordPress REST API.
        Returns only enabled sections, sorted by order.
        Falls back to defaults on failure.
        """
        # Try Redis cache first
        cached = await CacheService.get(HomepageService.CACHE_KEY)
        if cached is not None:
            logger.debug("Homepage settings cache hit")
            return cached

        try:
            url = "http://wordpress:80/wp-json/veriaguide/v1/homepage-settings"
            response = await HTTPService.get(url, use_wp_client=True)

            if response.status_code == 200:
                sections = response.json()

                if sections and isinstance(sections, list):
                    # Filter to only enabled sections (already sorted by order from WP)
                    enabled_sections = [s for s in sections if s.get("enabled", True)]

                    # Cache the result
                    await CacheService.set(
                        HomepageService.CACHE_KEY,
                        enabled_sections,
                        HomepageService.CACHE_TTL
                    )

                    logger.info(f"Fetched {len(enabled_sections)} enabled homepage sections from WordPress")
                    return enabled_sections

            logger.warning(f"WordPress homepage settings API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to fetch homepage settings from WordPress: {e}")

        # Fallback to defaults
        logger.info("Using default homepage sections")
        return [s for s in DEFAULT_SECTIONS if s.get("enabled", True)]
