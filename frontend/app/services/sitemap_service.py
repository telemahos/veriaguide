"""
Sitemap Service - Generates dynamic XML sitemaps for SEO
"""
from datetime import datetime
from typing import List, Dict
from app.config import POST_TYPES, SITE_URL
from app.services.homepage_service import HOMEPAGE_SECTION_CATEGORIES
from app.api.wordpress import get_all_posts_for_type
from app.utils.logging_config import get_logger
import asyncio

logger = get_logger("sitemap")


class SitemapService:
    """Service for generating XML sitemaps"""
    
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
    def _get_static_urls() -> List[Dict]:
        """Get static page URLs aligned with primary navigation."""
        now = datetime.now().isoformat()
        urls = [
            {
                "url": SITE_URL,
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
                "url": f"{SITE_URL}/map",
                "lastmod": now,
                "changefreq": "weekly",
                "priority": "0.8",
            },
        ]
        return urls
    
    @staticmethod
    def _get_category_urls() -> List[Dict]:
        """Get category listing page URLs for active menu categories only."""
        urls = []
        for category in HOMEPAGE_SECTION_CATEGORIES:
            if category not in POST_TYPES:
                continue
            urls.append({
                "url": f"{SITE_URL}/{category}",
                "lastmod": datetime.now().isoformat(),
                "changefreq": "daily",
                "priority": "0.9",
            })
        return urls
    
    @staticmethod
    async def _get_content_urls() -> List[Dict]:
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
    async def _fetch_and_process_posts(category: str, post_type: str) -> List[Dict]:
        """Fetch posts for a category and convert to sitemap URLs"""
        try:
            posts = await get_all_posts_for_type(post_type)
            urls = []
            
            for post in posts:
                # Get modified date from post
                modified = post.get("modified", datetime.now().isoformat())
                
                urls.append({
                    "url": f"{SITE_URL}/{category}/{post.get('slug')}",
                    "lastmod": modified,
                    "changefreq": "weekly",
                    "priority": "0.7"
                })
            
            logger.debug(f"Added {len(urls)} URLs for {category}")
            return urls
            
        except Exception as e:
            logger.error(f"Error processing posts for {category}: {e}")
            return []
    
    @staticmethod
    def _generate_xml(urls: List[Dict]) -> str:
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
        xml += f'  <sitemap>\n'
        xml += f'    <loc>{SITE_URL}/sitemap.xml</loc>\n'
        xml += f'    <lastmod>{datetime.now().isoformat()}</lastmod>\n'
        xml += f'  </sitemap>\n'
        xml += '</sitemapindex>'
        
        return xml
