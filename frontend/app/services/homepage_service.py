"""
Homepage Service - Fetches homepage section & hero settings from WordPress
"""
from typing import List, Dict, Any, Optional, Tuple
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

DEFAULT_HERO = {
    "slides": [{"image_url": "/static/img/veria-hero2.webp", "title": "", "subtitle": ""}],
    "speed": 6,
}


class HomepageService:
    """Service for fetching and caching homepage settings from WordPress"""

    CACHE_KEY = "homepage_settings_v2"
    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    async def get_homepage_settings() -> Dict[str, Any]:
        """
        Fetch all homepage settings from WordPress REST API.
        Returns dict with 'sections' (enabled only, ordered) and 'hero' (slides + speed).
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
                data = response.json()

                if data and isinstance(data, dict):
                    # Extract sections (filter enabled)
                    sections = data.get("sections", [])
                    enabled_sections = [s for s in sections if s.get("enabled", True)]

                    # Extract hero
                    hero = data.get("hero", DEFAULT_HERO)
                    if not hero.get("slides"):
                        hero = DEFAULT_HERO

                    result = {
                        "sections": enabled_sections,
                        "hero": hero,
                    }

                    # Cache the result
                    await CacheService.set(
                        HomepageService.CACHE_KEY,
                        result,
                        HomepageService.CACHE_TTL
                    )

                    logger.info(f"Fetched {len(enabled_sections)} sections, {len(hero.get('slides', []))} hero slides")
                    return result

            logger.warning(f"WordPress homepage settings API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to fetch homepage settings from WordPress: {e}")

        # Fallback to defaults
        logger.info("Using default homepage settings")
        return {
            "sections": [s for s in DEFAULT_SECTIONS if s.get("enabled", True)],
            "hero": DEFAULT_HERO,
        }
