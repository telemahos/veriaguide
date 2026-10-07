"""
Sitemap Service - Generates dynamic XML sitemaps for SEO
"""
import asyncio
import html
from datetime import UTC, datetime

from app.api.wordpress import get_all_posts_for_type
from app.config import POST_TYPES, SITE_URL
from app.services.homepage_service import HOMEPAGE_SECTION_CATEGORIES
from app.utils.category_urls import get_category_url_path
from app.utils.helpers import usable_listing_slug
from app.utils.logging_config import get_logger

logger = get_logger("sitemap")

SITEMAP_CATEGORIES = (
    *HOMEPAGE_SECTION_CATEGORIES,
    "tours",
    "restaurants",
    "cafes",
    "accommodations",
    "ski_resorts",
    "hiking_trails",
    "hidden_gems",
)


class SitemapService:
    """Service for generating XML sitemaps"""

    @staticmethod
    def _format_lastmod(value: str | datetime | None = None) -> str | None:
        """Return W3C date (YYYY-MM-DD) for sitemap lastmod, or None if unknown."""
        if isinstance(value, datetime):
            return value.astimezone(UTC).strftime("%Y-%m-%d")

        if value:
            text = str(value).strip()
            if len(text) >= 10 and text[4] == "-" and text[7] == "-":
                return text[:10]

        return None
    
    @staticmethod
    async def generate_sitemap() -> str:
        """Generate complete sitemap.xml with all content"""
        logger.info("Generating sitemap...")
        
        urls = []
        urls.extend(SitemapService._get_static_urls())
        urls.extend(await SitemapService._get_content_and_hub_urls())
        
        xml = SitemapService._generate_xml(urls)
        logger.info(f"Sitemap generated with {len(urls)} URLs")
        
        return xml
    
    @staticmethod
    def _get_static_urls() -> list[dict]:
        """Get static page URLs aligned with primary navigation."""
        urls = [
            {
                "url": SITE_URL.rstrip("/"),
                "lastmod": None,
                "changefreq": "daily",
                "priority": "1.0",
            },
            {
                "url": f"{SITE_URL}/contact",
                "lastmod": None,
                "changefreq": "monthly",
                "priority": "0.6",
            },
            {
                "url": f"{SITE_URL}/about",
                "lastmod": None,
                "changefreq": "monthly",
                "priority": "0.6",
            },
            {
                "url": f"{SITE_URL}/map",
                "lastmod": None,
                "changefreq": "weekly",
                "priority": "0.8",
            },
        ]
        return urls
    
    @staticmethod
    async def _get_content_and_hub_urls() -> list[dict]:
        """Category hubs (only with published items) plus detail URLs."""
        tasks = []
        categories = []
        for category in SITEMAP_CATEGORIES:
            post_type = POST_TYPES.get(category)
            if not post_type:
                continue
            categories.append(category)
            tasks.append(SitemapService._fetch_and_process_posts(category, post_type))
        
        results = await asyncio.gather(*tasks)
        urls = []
        for result in results:
            urls.extend(result)
        return urls
    
    @staticmethod
    async def _fetch_and_process_posts(category: str, post_type: str) -> list[dict]:
        """Fetch posts for a category; skip empty hubs."""
        posts = await get_all_posts_for_type(post_type)
        urls = []
        lastmods = []

        for post in posts:
            slug = usable_listing_slug(post.get("slug"))
            if not slug:
                continue
            modified = SitemapService._format_lastmod(post.get("modified") or post.get("date"))
            if modified:
                lastmods.append(modified)
            urls.append({
                "url": f"{SITE_URL}/{get_category_url_path(category)}/{slug}",
                "lastmod": modified,
                "changefreq": "weekly",
                "priority": "0.7",
            })

        if not urls:
            logger.info(f"Skipping empty sitemap hub for {category}")
            return []

        hub_lastmod = max(lastmods) if lastmods else None
        urls.insert(0, {
            "url": f"{SITE_URL}/{get_category_url_path(category)}",
            "lastmod": hub_lastmod,
            "changefreq": "daily",
            "priority": "0.9",
        })
        logger.debug(f"Added {len(urls)} URLs for {category}")
        return urls
    
    @staticmethod
    def _localized_url(url: str, lang: str) -> str:
        from app.i18n import localized_path

        base = SITE_URL.rstrip("/")
        path = url[len(base):] or "/"
        return f"{base}{localized_path(path, lang)}"

    @staticmethod
    def _with_language_alternates(urls: list[dict]) -> list[dict]:
        from app.i18n import PREFIX_LANGS, SUPPORTED

        paired = []
        for url_data in urls:
            english = url_data["url"]
            by_lang = {"en": english}
            for lang in PREFIX_LANGS:
                by_lang[lang] = SitemapService._localized_url(english, lang)
            alternates = [(lang, by_lang[lang]) for lang in SUPPORTED]
            alternates.append(("x-default", english))
            for lang in SUPPORTED:
                paired.append({**url_data, "url": by_lang[lang], "alternates": alternates})
        return paired

    @staticmethod
    def _xml_escape(value: str) -> str:
        return html.escape(value or "", quote=True)

    @staticmethod
    def _generate_xml(urls: list[dict]) -> str:
        """Generate XML sitemap from URLs"""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'

        for url_data in SitemapService._with_language_alternates(urls):
            xml += '  <url>\n'
            xml += f'    <loc>{SitemapService._xml_escape(url_data["url"])}</loc>\n'
            for hreflang, href in url_data["alternates"]:
                xml += (
                    f'    <xhtml:link rel="alternate" hreflang="{SitemapService._xml_escape(hreflang)}" '
                    f'href="{SitemapService._xml_escape(href)}"/>\n'
                )
            lastmod = url_data.get("lastmod")
            if lastmod:
                xml += f'    <lastmod>{SitemapService._xml_escape(lastmod)}</lastmod>\n'
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
        xml += f'    <loc>{SitemapService._xml_escape(SITE_URL + "/sitemap.xml")}</loc>\n'
        xml += '  </sitemap>\n'
        xml += '</sitemapindex>'
        
        return xml
