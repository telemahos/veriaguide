"""
Sitemap Service - Generates dynamic XML sitemaps for SEO
"""
import asyncio
from datetime import UTC, datetime

from app.api.wordpress import get_all_posts_for_type
from app.config import POST_TYPES, SITE_URL
from app.services.homepage_service import HOMEPAGE_SECTION_CATEGORIES
from app.utils.category_urls import get_category_url_path
from app.utils.logging_config import get_logger

logger = get_logger("sitemap")


class SitemapService:
    """Service for generating XML sitemaps"""

    @staticmethod
    def _format_lastmod(value: str | datetime | None = None) -> str:
        """Return W3C date (YYYY-MM-DD) for sitemap lastmod — required by Google."""
        if isinstance(value, datetime):
            return value.astimezone(UTC).strftime("%Y-%m-%d")

        if value:
            text = str(value).strip()
            if len(text) >= 10 and text[4] == "-" and text[7] == "-":
                return text[:10]

        return datetime.now(UTC).strftime("%Y-%m-%d")
    
    @staticmethod
    async def generate_sitemap() -> str:
        """Generate complete sitemap.xml with all content"""
        logger.info("Generating sitemap...")
        
        urls = []
        
        # Add static pages
        urls.extend(SitemapService._get_static_urls())
        
        # Add category listing pages
        urls.extend(SitemapService._get_category_urls())
        
        # Add dynamic content pages
        urls.extend(await SitemapService._get_content_urls())
        
        # Generate XML
        xml = SitemapService._generate_xml(urls)
        logger.info(f"Sitemap generated with {len(urls)} URLs")
        
        return xml
    
    @staticmethod
    def _get_static_urls() -> list[dict]:
        """Get static page URLs aligned with primary navigation."""
        now = SitemapService._format_lastmod()
        urls = [
            {
                "url": SITE_URL.rstrip("/"),
                "lastmod": now,
                "changefreq": "daily",
                "priority": "1.0",
            },
            {
                "url": f"{SITE_URL}/contact",
                "lastmod": now,
                "changefreq": "monthly",
                "priority": "0.6",
            },
            {
                "url": f"{SITE_URL}/about",
                "lastmod": now,
                "changefreq": "monthly",
                "priority": "0.6",
            },
            {
                "url": f"{SITE_URL}/map",
                "lastmod": now,
                "changefreq": "weekly",
                "priority": "0.8",
            },
        ]
        return urls
    
    @staticmethod
    def _get_category_urls() -> list[dict]:
        """Get category listing page URLs for active menu categories only."""
        urls = []
        for category in HOMEPAGE_SECTION_CATEGORIES:
            if category not in POST_TYPES:
                continue
            urls.append({
                "url": f"{SITE_URL}/{get_category_url_path(category)}",
                "lastmod": SitemapService._format_lastmod(),
                "changefreq": "daily",
                "priority": "0.9",
            })
        return urls
    
    @staticmethod
    async def _get_content_urls() -> list[dict]:
        """Get all content item URLs"""
        urls = []
        
        # Fetch all posts for each post type concurrently
        tasks = []
        for category in HOMEPAGE_SECTION_CATEGORIES:
            post_type = POST_TYPES.get(category)
            if not post_type:
                continue
            tasks.append(SitemapService._fetch_and_process_posts(category, post_type))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching posts for sitemap: {result}")
                continue
            urls.extend(result)
        
        return urls
    
    @staticmethod
    async def _fetch_and_process_posts(category: str, post_type: str) -> list[dict]:
        """Fetch posts for a category and convert to sitemap URLs"""
        try:
            posts = await get_all_posts_for_type(post_type)
            urls = []
            
            for post in posts:
                # Get modified date from post
                modified = post.get("modified")
                
                urls.append({
                    "url": f"{SITE_URL}/{get_category_url_path(category)}/{post.get('slug')}",
                    "lastmod": SitemapService._format_lastmod(modified),
                    "changefreq": "weekly",
                    "priority": "0.7"
                })
            
            logger.debug(f"Added {len(urls)} URLs for {category}")
            return urls
            
        except Exception as e:
            logger.error(f"Error processing posts for {category}: {e}")
            return []
    
    @staticmethod
    def _generate_xml(urls: list[dict]) -> str:
        """Generate XML sitemap from URLs"""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for url_data in urls:
            xml += '  <url>\n'
            xml += f'    <loc>{url_data["url"]}</loc>\n'
            xml += f'    <lastmod>{url_data["lastmod"]}</lastmod>\n'
            xml += f'    <changefreq>{url_data["changefreq"]}</changefreq>\n'
            xml += f'    <priority>{url_data["priority"]}</priority>\n'
            xml += '  </url>\n'
        
        xml += '</urlset>'
        
        return xml
    
    @staticmethod
    async def generate_sitemap_index() -> str:
        """Generate sitemap index (for future multi-file sitemaps)"""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        xml += '  <sitemap>\n'
        xml += f'    <loc>{SITE_URL}/sitemap.xml</loc>\n'
        xml += f'    <lastmod>{SitemapService._format_lastmod()}</lastmod>\n'
        xml += '  </sitemap>\n'
        xml += '</sitemapindex>'
        
        return xml
