"""
Homepage Service - Fetches homepage section & hero settings from WordPress
"""
from typing import List, Dict, Any, Optional, Tuple
from app.config import WP_API_URL
from app.services.http_service import HTTPService
from app.services.cache_service import CacheService
from app.utils.logging_config import get_logger
from app.utils.helpers import (
    HOME_HERO_TITLE,
    HOME_HERO_SUBTITLE,
    HOME_ABOUT_TEXT,
    apply_homepage_seo_content,
)

logger = get_logger("homepage")

# Categories shown on the homepage (heritage & culture focus)
HOMEPAGE_SECTION_CATEGORIES = (
    "religious_sites",
    "museums",
    "archaeological_sites",
)

HOMEPAGE_SECTION_ORDER = {
    "religious_sites": 1,
    "museums": 2,
    "archaeological_sites": 3,
}

EXCLUDED_HOMEPAGE_CATEGORIES = frozenset({
    "restaurants",
    "cafes",
    "accommodations",
    "ski_resorts",
})

# Default sections if WordPress settings are unavailable
DEFAULT_SECTIONS = [
    {"category": "religious_sites", "post_type": "religious_site", "title": "Churches & Monasteries", "enabled": True, "items_count": 4, "order": 1, "view_all_link": "/religious_sites"},
    {"category": "museums", "post_type": "museum", "title": "Museums", "enabled": True, "items_count": 4, "order": 2, "view_all_link": "/museums"},
    {"category": "archaeological_sites", "post_type": "archaeological_site", "title": "Archaeological Sites", "enabled": True, "items_count": 4, "order": 3, "view_all_link": "/archaeological_sites"},
]

DEFAULT_HERO = {
    "slides": [{
        "image_url": "/static/img/veria-hero2.webp",
        "title": HOME_HERO_TITLE,
        "subtitle": HOME_HERO_SUBTITLE,
    }],
    "speed": 6,
}

DEFAULT_ABOUT_TEXT = HOME_ABOUT_TEXT


class HomepageService:
    """Service for fetching and caching homepage settings from WordPress"""

    CACHE_KEY = "homepage_settings_v4"
    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    def filter_homepage_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep only enabled heritage sections for the homepage."""
        filtered = [
            section for section in sections
            if section.get("enabled", True)
            and section.get("category") not in EXCLUDED_HOMEPAGE_CATEGORIES
        ]
        filtered.sort(
            key=lambda section: HOMEPAGE_SECTION_ORDER.get(section.get("category"), 99)
        )
        return filtered

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
            cached["sections"] = HomepageService.filter_homepage_sections(cached.get("sections", []))
            return apply_homepage_seo_content(cached)

        try:
            wp_base = WP_API_URL.split("/wp-json")[0]
            url = f"{wp_base}/wp-json/veriaguide/v1/homepage-settings"
            response = await HTTPService.get(url, use_wp_client=True)

            if response.status_code == 200:
                data = response.json()

                if data and isinstance(data, dict):
                    # Extract sections (filter enabled)
                    sections = data.get("sections", [])
                    enabled_sections = HomepageService.filter_homepage_sections(sections)

                    # Extract hero
                    hero = data.get("hero", DEFAULT_HERO)
                    if not hero.get("slides"):
                        hero = DEFAULT_HERO

                    result = {
                        "sections": enabled_sections,
                        "hero": hero,
                        "about_text": data.get("about_text", ""),
                    }

                    # Cache the result
                    await CacheService.set(
                        HomepageService.CACHE_KEY,
                        result,
                        HomepageService.CACHE_TTL
                    )

                    logger.info(f"Fetched {len(enabled_sections)} sections, {len(hero.get('slides', []))} hero slides")
                    return apply_homepage_seo_content(result)

            logger.warning(f"WordPress homepage settings API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to fetch homepage settings from WordPress: {e}")

        # Fallback to defaults
        logger.info("Using default homepage settings")
        return apply_homepage_seo_content({
            "sections": HomepageService.filter_homepage_sections(DEFAULT_SECTIONS),
            "hero": DEFAULT_HERO,
            "about_text": DEFAULT_ABOUT_TEXT,
        })
