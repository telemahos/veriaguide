"""
Template Service - Handles template data preparation and rendering logic
"""
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import SITE_URL
from app.i18n import current_lang, tr
from app.services.homepage_service import get_active_category_filters
from app.utils.cookie_consent import analytics_allowed, has_consent
from app.utils.favorites import get_favorites
from app.utils.helpers import (
    HOME_SEO_DESCRIPTION,
    HOME_SEO_TITLE,
    build_pagination_seo_urls,
    content_canonical_url,
    enhance_religious_site_description,
    format_opening_hours,
    generate_homepage_schema,
    get_google_maps_api_key,
    get_homepage_og_image_url,
    get_meta_data,
    get_page_url,
    get_religious_site_seo_intro,
)
from app.utils.seo import (
    DESCRIPTION_LIMIT,
    clamp_text,
    detail_structured_data,
    item_list_jsonld,
    listing_meta,
    webpage_jsonld,
)


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
        "museums": {
            "title": "Museums in Veria, Greece",
            "description": (
                "Discover the history of Veria: from Byzantine treasures to the Archaeological Museum. "
                "Opening hours, admission and insider tips for your visit in Imathia, Macedonia."
            ),
        },
        "archaeological_sites": {
            "title": "Archaeological Sites in Veria, Greece",
            "description": (
                "Explore ancient Veria and Vergina: archaeological sites, ruins and heritage landmarks "
                "in Imathia. Maps, visiting tips and travel guide for history lovers."
            ),
        },
        "restaurants": {
            "title": "Restaurants & Tavernas in Veria, Greece",
            "description": (
                "The best restaurants, tavernas and meze places in Veria, Greece, with opening hours, map, phone numbers and reviews, from traditional to modern Greek."
            ),
            # Real photo used on the page (hero) and as the social card; new URL, 1200x630.
            "image": "/static/img/og/restaurants-veria-1200x630.jpg",
            "image_alt": "Barbouta, the old Jewish quarter of Veria",
            "image_width": 1200,
            "image_height": 630,
        },
    }
    
    def __init__(self, templates: Jinja2Templates):
        self.templates = templates
    
    @staticmethod
    def get_common_template_data(request: Request) -> dict[str, Any]:
        """Get common data for all templates"""
        return {
            "request": request,
            "meta": get_meta_data(),
            "favorites": get_favorites(request),
            "google_maps_api_key": get_google_maps_api_key(),
            "needs_leaflet": False,
            "cookie_consent": has_consent(request),
            "cookie_analytics": analytics_allowed(request),
        }
    
    @staticmethod
    def _category_list_meta(category_name: str, request: Request) -> dict[str, str]:
        """Category-specific SEO meta for listing pages."""
        seo = TemplateService.CATEGORY_SEO.get(category_name)
        if seo:
            return {
                "title": seo["title"],
                "description": seo["description"],
                "url": get_page_url(request.url.path),
                "image": seo.get("image"),
                "image_alt": seo.get("image_alt"),
                "image_width": seo.get("image_width"),
                "image_height": seo.get("image_height"),
            }
        label = category_name.replace("_", " ")
        return {
            "title": f"{label.title()} in Veria, Greece",
            "description": f"Discover the best {label} in Veria (Veroia), Imathia, Greece.",
            "url": get_page_url(request.url.path),
        }

    @staticmethod
    def prepare_home_template_data(
        commons: dict[str, Any],
        featured_items: dict[str, Any],
        locations: str
    ) -> dict[str, Any]:
        """Prepare template data for home page"""
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
            "locations": locations,
            "needs_leaflet": False,
        }
    
    @staticmethod
    def prepare_category_list_template_data(
        commons: dict[str, Any],
        category_name: str,
        content_data: dict[str, Any],
        page: int,
        search_term: str | None,
        denominations_selected: list,
        rating_selected: str
    ) -> dict[str, Any]:
        """Prepare template data for category listing pages"""
        request = commons["request"]
        list_meta = TemplateService._category_list_meta(category_name, request)
        total_pages = content_data.get("total_pages", 1)
        query_params = dict(request.query_params)
        query_params.pop("page", None)
        pagination_seo = build_pagination_seo_urls(
            request.url.path, page, total_pages, dict(query_params)
        )
        meta = get_meta_data(
            title=list_meta["title"],
            description=list_meta["description"],
            url=pagination_seo["canonical"],
        )
        if list_meta.get("image"):
            meta["image"] = f"{SITE_URL.rstrip('/')}{list_meta['image']}"
            meta["image_alt"] = tr(list_meta["image_alt"]) if list_meta.get("image_alt") else None
            meta["image_width"] = list_meta.get("image_width")
            meta["image_height"] = list_meta.get("image_height")
            meta["image_type"] = "image/jpeg"
        catalog_size = (content_data.get("rating_counts") or {}).get("any", 0)
        if not search_term and catalog_size == 0:
            meta["robots"] = "noindex, follow"
        meta["pagination_prev"] = pagination_seo["prev"]
        meta["pagination_next"] = pagination_seo["next"]
        hub_name = tr(list_meta["title"])
        hub_description = tr(list_meta["description"])
        crumbs = [
            (tr("Home"), get_page_url("/")),
            (hub_name, pagination_seo["canonical"]),
        ]
        return {
            **commons,
            "meta": meta,
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
            "total_pages": content_data['total_pages'],
            "needs_leaflet": True,
            "schema_markup": webpage_jsonld(
                "CollectionPage",
                hub_name,
                hub_description,
                pagination_seo["canonical"],
                crumbs,
                main_entity=item_list_jsonld(content_data.get("items") or [], category_name, page,
                                             content_data.get("per_page", 12)),
                image=meta["image"] if list_meta.get("image") else None,
            ),
        }
    
    @staticmethod
    def prepare_item_detail_template_data(
        commons: dict[str, Any],
        category_name: str,
        post_type_name: str,
        item_data: dict[str, Any],
        location_data: dict[str, Any] | None = None,
        related_items: list | None = None,
        nearby_items: list | None = None,
    ) -> dict[str, Any]:
        """Prepare template data for item detail pages"""
        item = item_data['item']
        acf_fields = item_data['acf_fields']
        request = commons["request"]

        lang = current_lang()
        doc_title, description, place, verbatim_title = listing_meta(item, lang, post_type_name)
        seo_intro = None
        if post_type_name == "religious_site" and lang == "en":
            description = enhance_religious_site_description(place or item_data["title"], description)
            description = clamp_text(description, DESCRIPTION_LIMIT)
            seo_intro = get_religious_site_seo_intro(
                item_data["title"], item_data["description"], item_data["content"]
            )

        # Format opening hours if available
        opening_hours = format_opening_hours(acf_fields.get("opening_hours", {}))

        page_url = get_page_url(request.url.path)
        schema_markup = detail_structured_data(
            post_type_name, item, category_name, place, description
        )

        template_data = {
            **commons,
            "meta": get_meta_data(
                title=doc_title,
                description=description,
                image=item_data['featured_image'],
                type="article",
                url=page_url,
                append_site_name=False,
                verbatim_title=verbatim_title,
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
        
        # Add location data if available
        if location_data:
            template_data["location"] = location_data

        location_map = acf_fields.get("location_map") or {}
        template_data["needs_leaflet"] = bool(location_map.get("lat") and location_map.get("lng"))
        
        return template_data
    
    @staticmethod
    def prepare_search_template_data(
        commons: dict[str, Any],
        query: str | None,
        content_type: str | None,
        search_data: dict,
        page: int,
        items_per_page: int
    ) -> dict[str, Any]:
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
                title=(
                    f"Αποτελέσματα αναζήτησης για «{query}»"
                    if current_lang() == "el"
                    else f"Suchergebnisse für „{query}“"
                    if current_lang() == "de"
                    else f"Search results for '{query}'"
                ),
                description=(
                    f"Αποτελέσματα αναζήτησης για «{query}» στον Veria Guide"
                    if current_lang() == "el"
                    else f"Suchergebnisse für „{query}“ im Veria Guide"
                    if current_lang() == "de"
                    else f"Search results for '{query}' in Veria Guide"
                ),
                url=content_canonical_url(
                    commons["request"].url.path,
                    dict(commons["request"].query_params),
                    ("q", "type", "page"),
                ),
                robots="noindex, follow",
            ),
            "results": results,
            "query": query,
            "type": content_type,
            "page": page,
            "has_next": has_next,
            "has_prev": has_prev,
            "total_results": total,
            "per_page": items_per_page,
            "needs_leaflet": bool(query),
        }
    
    @staticmethod
    def prepare_contact_template_data(
        commons: dict[str, Any],
        success: bool | None = None,
        message: str | None = None
    ) -> dict[str, Any]:
        """Prepare template data for contact form"""
        contact_url = get_page_url(commons["request"].url.path)
        contact_name = tr("Contact Us")
        contact_description = tr("Get in touch with the VeriaGuide team")
        template_data = {
            **commons,
            "meta": get_meta_data(
                title="Contact Us",
                description="Get in touch with the VeriaGuide team",
                url=contact_url,
            ),
            "schema_markup": webpage_jsonld(
                "ContactPage",
                contact_name,
                contact_description,
                contact_url,
                [(tr("Home"), get_page_url("/")), (contact_name, contact_url)],
            ),
        }
        
        if success is not None:
            template_data["success"] = success
            template_data["message"] = message
        
        return template_data
    
    @staticmethod
    def prepare_favorites_template_data(
        commons: dict[str, Any],
        favorites: list
    ) -> dict[str, Any]:
        """Prepare template data for favorites page"""
        return {
            **commons,
            "meta": get_meta_data(
                title="My Favorites",
                description="Your saved favorite places in Veria",
                url=get_page_url(commons["request"].url.path),
                robots="noindex, follow",
            ),
            "favorites": favorites,
            "active_category_filters": get_active_category_filters(),
            "needs_leaflet": True,
        }
    
    @staticmethod
    def prepare_legal_template_data(
        commons: dict[str, Any],
        page_key: str,
        title: str,
        description: str,
    ) -> dict[str, Any]:
        """Cookies, terms or imprint. `page_key` selects the copy block."""
        url = get_page_url(f"/{page_key}")
        name = tr(title)
        summary = tr(description)
        return {
            **commons,
            "meta": get_meta_data(title=title, description=description, url=url),
            "legal_key": page_key,
            "legal_lang": current_lang() if current_lang() in ("en", "el", "de") else "en",
            "schema_markup": webpage_jsonld(
                "WebPage", name, summary, url,
                [(tr("Home"), get_page_url("/")), (name, url)],
            ),
        }

    @staticmethod
    def prepare_privacy_template_data(
        commons: dict[str, Any],
        lang: str,
    ) -> dict[str, Any]:
        """Prepare template data for the Privacy Policy page."""
        url = get_page_url("/privacy-policy")
        name = tr("Privacy Policy")
        description = "Privacy Policy of VeriaGuide (veriaguide.gr): cookies, analytics, AI Trip Planner, forms and Google API data."
        return {
            **commons,
            "meta": get_meta_data(title="Privacy Policy", description=description, url=url),
            "privacy_lang": lang if lang in ("en", "el", "de") else "en",
            "schema_markup": webpage_jsonld(
                "WebPage", name, description, url,
                [(tr("Home"), get_page_url("/")), (name, url)],
            ),
        }

    @staticmethod
    def prepare_about_template_data(
        commons: dict[str, Any],
        about_text: str,
    ) -> dict[str, Any]:
        """Prepare template data for the About page."""
        about_url = get_page_url("/about")
        about_name = tr("About VeriaGuide")
        about_description = tr(
            "Learn about VeriaGuide — your local travel guide to Veria (Veroia), Imathia, Greece. "
            "Byzantine churches, museums, archaeological sites and Macedonian heritage."
        )
        return {
            **commons,
            "meta": get_meta_data(
                title="About VeriaGuide",
                description=(
                    "Learn about VeriaGuide — your local travel guide to Veria (Veroia), Imathia, Greece. "
                    "Byzantine churches, museums, archaeological sites and Macedonian heritage."
                ),
                url=about_url,
            ),
            "about_text": about_text,
            "schema_markup": webpage_jsonld(
                "AboutPage",
                about_name,
                about_description,
                about_url,
                [(tr("Home"), get_page_url("/")), (about_name, about_url)],
            ),
        }

    @staticmethod
    def prepare_map_template_data(
        commons: dict[str, Any],
        locations: str,
        selected_type: str | None = None
    ) -> dict[str, Any]:
        """Prepare template data for map view"""
        map_request = commons["request"]
        map_url = content_canonical_url(map_request.url.path, dict(map_request.query_params), ("q", "type"))
        map_name = tr("Interactive Map of Veria")
        map_description = tr("Explore Veria's attractions, restaurants, and more on our interactive map")
        return {
            **commons,
            "meta": get_meta_data(
                title="Interactive Map of Veria",
                description="Explore Veria's attractions, restaurants, and more on our interactive map",
                url=map_url,
            ),
            "locations": locations,
            "selected_type": selected_type,
            "needs_leaflet": True,
            "schema_markup": webpage_jsonld(
                "WebPage",
                map_name,
                map_description,
                map_url,
                [(tr("Home"), get_page_url("/")), (tr("Map"), map_url)],
            ),
        }
    
    @staticmethod
    def prepare_religious_sites_map_template_data(
        commons: dict[str, Any],
        items: list,
        locations: list
    ) -> dict[str, Any]:
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
            "locations": locations,
            "needs_leaflet": True,
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
    def get_item_image_url(item: dict[str, Any], category: str = 'default') -> str:
        """Get item image URL with fallback to category-specific placeholder"""
        # Try to get featured media from WordPress
        if (item.get('_embedded') and 
            'wp:featuredmedia' in item['_embedded'] and 
            item['_embedded']['wp:featuredmedia']):
            return item['_embedded']['wp:featuredmedia'][0].get('source_url', '')
        
        # Fallback to category-specific placeholder
        return TemplateService.get_placeholder_image_url(category)