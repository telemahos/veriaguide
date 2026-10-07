import html
import json
import os
import re
import unicodedata
from datetime import datetime

from app.config import POST_TYPES, SITE_DESCRIPTION, SITE_NAME, SITE_URL
from app.utils.category_urls import get_category_url_path


def strip_tags(html_content):
    """Remove HTML tags from content"""
    return re.sub(r'<[^>]+>', '', html_content)

def fold_search_text(text: str) -> str:
    """Lowercase and strip combining marks so έ matches ε, etc."""
    normalized = unicodedata.normalize("NFD", (text or "").casefold())
    stripped = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    # Greek final sigma (ς) should match medial σ in queries and titles.
    return stripped.replace("ς", "σ")


def _rendered_plain_text(value) -> str:
    if isinstance(value, dict):
        value = value.get("rendered") or ""
    if not isinstance(value, str):
        return ""
    return strip_tags(value)


def _flatten_search_strings(value) -> list[str]:
    """WP REST meta is a string, a list of strings, or nested lists."""
    if isinstance(value, str):
        text = strip_tags(value).strip()
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        chunks = []
        for entry in value:
            chunks.extend(_flatten_search_strings(entry))
        return chunks
    if isinstance(value, dict):
        rendered = value.get("rendered")
        if isinstance(rendered, str) and rendered.strip():
            return _flatten_search_strings(rendered)
        chunks = []
        for entry in value.values():
            if isinstance(entry, (str, list, tuple, dict)):
                chunks.extend(_flatten_search_strings(entry))
        return chunks
    return []


def listing_search_text(item: dict) -> str:
    """Text WordPress REST search misses: Greek/German meta plus displayed fields."""
    if not isinstance(item, dict):
        return ""
    chunks = [
        _rendered_plain_text(item.get("title")),
        _rendered_plain_text(item.get("excerpt")),
        _rendered_plain_text(item.get("content")),
        str(item.get("slug") or ""),
    ]
    meta = item.get("meta")
    if isinstance(meta, dict):
        for key, value in meta.items():
            if key.startswith("_"):
                continue
            chunks.extend(_flatten_search_strings(value))
        # Always include translation keys even if a cached payload nested them oddly.
        for key in (
            "title_el", "excerpt_el", "content_el",
            "title_de", "excerpt_de", "content_de",
        ):
            chunks.extend(_flatten_search_strings(meta.get(key)))
    acf = item.get("acf")
    if isinstance(acf, dict):
        for key in ("address", "city", "location_city"):
            chunks.extend(_flatten_search_strings(acf.get(key)))
        location_map = acf.get("location_map")
        if isinstance(location_map, dict):
            chunks.extend(_flatten_search_strings(location_map.get("address")))
    return " ".join(chunks)


def listing_matches_query(item: dict, query: str | None) -> bool:
    """True when every query token appears in listing search text (accent-insensitive)."""
    if not query or not str(query).strip():
        return True
    haystack = fold_search_text(listing_search_text(item))
    tokens = fold_search_text(str(query)).split()
    return bool(tokens) and all(token in haystack for token in tokens)


def listing_title_candidates(item: dict) -> list[str]:
    """English rendered title plus translated title meta fields."""
    titles = []
    rendered = decode_entities(_rendered_plain_text((item or {}).get("title"))).strip()
    if rendered:
        titles.append(rendered)
    meta = (item or {}).get("meta")
    if isinstance(meta, dict):
        for key in ("title_el", "title_de"):
            for chunk in _flatten_search_strings(meta.get(key)):
                clean = decode_entities(chunk).strip()
                if clean and clean not in titles:
                    titles.append(clean)
    return titles


def listing_localized_title(item: dict, lang: str | None = None) -> str:
    """Public listing title for autocomplete and similar UI."""
    from app.i18n import PREFIX_LANGS, current_lang

    lang = lang or current_lang()
    meta = (item or {}).get("meta") if isinstance(item, dict) else None
    if lang in PREFIX_LANGS and isinstance(meta, dict):
        for chunk in _flatten_search_strings(meta.get(f"title_{lang}")):
            clean = decode_entities(chunk).strip()
            if clean:
                return clean
    rendered = decode_entities(_rendered_plain_text((item or {}).get("title"))).strip()
    return rendered


def title_query_relevance_score(title: str, query: str) -> float:
    """Rank autocomplete hits: exact, prefix, word, then substring."""
    needle = fold_search_text(query)
    hay = fold_search_text(title)
    if not needle or not hay:
        return 0
    score = 0
    if hay == needle:
        score = 100
    elif hay.startswith(needle):
        score = 50
    elif f" {needle} " in f" {hay} ":
        score = 25
    elif needle in hay:
        score = 10
    if score:
        length_penalty = min(len(title) * 0.1, 5)
        return score - length_penalty
    return 0


def autocomplete_relevance_score(item: dict, query: str) -> float:
    return max(
        (title_query_relevance_score(title, query) for title in listing_title_candidates(item)),
        default=0,
    )


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates in kilometres."""
    from math import atan2, cos, radians, sin, sqrt

    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))

def decode_entities(text: str) -> str:
    """Decode HTML entities and strip tags when needed."""
    if not text:
        return ""
    raw = strip_tags(text) if "<" in str(text) else str(text)
    return html.unescape(raw)


def split_display_title(title: str) -> dict:
    """Split SEO-style titles into a short heading and optional subtitle."""
    clean = decode_entities(title)
    clean = re.sub(r"\s+", " ", clean).strip()
    if ":" in clean:
        main, subtitle = clean.split(":", 1)
        return {"title": main.strip(), "subtitle": subtitle.strip()}
    return {"title": clean, "subtitle": ""}

def format_date(date_string, format_str="%d %B %Y"):
    """Format date string"""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
        return date_obj.strftime(format_str)
    except (ValueError, TypeError):
        return date_string

CATEGORY_PLACEHOLDER_URLS = {
    "religious_site": "/static/img/placeholder-church.svg",
    "museum": "/static/img/placeholder-museum.svg",
    "archaeological_site": "/static/img/placeholder-museum.svg",
    "restaurant": "/static/img/placeholder-restaurant.svg",
    "cafe": "/static/img/placeholder-restaurant.svg",
    "accommodation": "/static/img/placeholder-default.svg",
    "ski_resort": "/static/img/placeholder-default.svg",
    "hiking_trail": "/static/img/placeholder-default.svg",
    "tour": "/static/img/placeholder-default.svg",
    "hidden_gem": "/static/img/placeholder-default.svg",
    "default": "/static/img/placeholder-default.svg",
}

CATEGORY_GALLERY_ICONS = {
    "religious_site": "fa-place-of-worship",
    "museum": "fa-landmark",
    "archaeological_site": "fa-monument",
    "restaurant": "fa-utensils",
    "cafe": "fa-mug-hot",
    "accommodation": "fa-bed",
    "ski_resort": "fa-person-skiing",
    "hiking_trail": "fa-person-hiking",
    "tour": "fa-route",
    "hidden_gem": "fa-gem",
    "default": "fa-camera",
}


def is_placeholder_image(url) -> bool:
    """True when the URL is missing or a generic placeholder asset."""
    if not url:
        return True
    lower = str(url).lower()
    return (
        "placeholder.jpg" in lower
        or "placeholder-" in lower  # placeholder-museum.svg, placeholder-church.svg, …
        or lower.endswith("placeholder.svg")
        or "placeholder-default.svg" in lower
    )


def get_category_placeholder_url(post_type: str = "default") -> str:
    return CATEGORY_PLACEHOLDER_URLS.get(post_type, CATEGORY_PLACEHOLDER_URLS["default"])


def get_category_gallery_icon(post_type: str = "default") -> str:
    return CATEGORY_GALLERY_ICONS.get(post_type, CATEGORY_GALLERY_ICONS["default"])


def _real_image_url(url) -> str | None:
    """Return url if it looks like a real photo, else None."""
    if not url or not isinstance(url, str):
        return None
    text = url.strip()
    if not text or text.lower() in {"none", "null", "false", "0"}:
        return None
    if not text.startswith(("http://", "https://", "/")):
        return None
    if is_placeholder_image(text):
        return None
    return text


def get_featured_image(post):
    """Extract featured image from WordPress post"""
    if not isinstance(post, dict):
        return None
    embedded = post.get("_embedded")
    if not isinstance(embedded, dict):
        return None
    media_list = embedded.get("wp:featuredmedia")
    if not isinstance(media_list, list) or not media_list:
        return None
    media = media_list[0]
    if not isinstance(media, dict) or media.get("code"):
        return None
    url = _real_image_url(media.get("source_url"))
    if url:
        return url
    details = media.get("media_details") if isinstance(media.get("media_details"), dict) else {}
    sizes = details.get("sizes") if isinstance(details.get("sizes"), dict) else {}
    for size in ("large", "medium", "full"):
        sized = sizes.get(size)
        if isinstance(sized, dict):
            url = _real_image_url(sized.get("source_url"))
            if url:
                return url
        elif isinstance(sized, str):
            url = _real_image_url(sized)
            if url:
                return url
    return None


_GALLERY_IMAGE_FIELDS = ("photo_gallery", "gallery", "photos", "images")


def _acf_field_first_photo_url(value) -> str | None:
    """First real (non-placeholder) URL inside an ACF image/gallery field."""
    if isinstance(value, str):
        return _real_image_url(value)
    if isinstance(value, dict):
        if value.get("code"):
            return None
        url = value.get("url") or value.get("source_url") or ""
        sizes = value.get("sizes") if isinstance(value.get("sizes"), dict) else {}
        for sized in sizes.values():
            if isinstance(sized, str) and sized:
                url = url or sized
            elif isinstance(sized, dict) and (sized.get("source_url") or sized.get("url")):
                url = url or sized.get("source_url") or sized.get("url")
        return _real_image_url(str(url) if url else None)
    if isinstance(value, list):
        for entry in value:
            found = _acf_field_first_photo_url(entry)
            if found:
                return found
    return None


def _acf_field_has_photo(value) -> bool:
    """True when an ACF image/gallery field holds a real (non-placeholder) URL."""
    return _acf_field_first_photo_url(value) is not None


def listing_gallery_photo_url(item: dict) -> str | None:
    acf = item.get("acf") if isinstance(item.get("acf"), dict) else {}
    for field in _GALLERY_IMAGE_FIELDS:
        url = _acf_field_first_photo_url(acf.get(field))
        if url:
            return url
    return None


def listing_has_photo(item: dict) -> bool:
    """True when a listing would show a real photo on cards (not a category placeholder)."""
    if not isinstance(item, dict):
        return False
    card = get_item_listing_card_image(item)
    return not is_placeholder_image(card.get("url"))


def get_listing_card_image(media) -> dict:
    """Return a reasonably sized image dict for listing cards (PageSpeed-friendly)."""
    default = {
        "url": "/static/img/placeholder-default.svg",
        "width": 400,
        "height": 300,
    }
    if not media:
        return default
    if isinstance(media, list):
        media = media[0] if media else None
    if not isinstance(media, dict) or media.get("code"):
        return default

    details = media.get("media_details") if isinstance(media.get("media_details"), dict) else {}
    sizes = details.get("sizes") if isinstance(details.get("sizes"), dict) else {}
    srcset = ", ".join(
        f"{sizes[key]['source_url']} {sizes[key]['width']}w"
        for key in ("medium", "medium_large")
        if _real_image_url((sizes.get(key) or {}).get("source_url")) and (sizes.get(key) or {}).get("width")
    )
    for key in ("medium_large", "medium", "thumbnail"):
        sized = sizes.get(key) or {}
        url = _real_image_url(sized.get("source_url")) if isinstance(sized, dict) else None
        if url:
            return {
                "url": url,
                "width": sized.get("width", 400),
                "height": sized.get("height", 300),
                "srcset": srcset,
            }

    source_url = _real_image_url(media.get("source_url"))
    if source_url:
        return {
            "url": source_url,
            "width": details.get("width", 800),
            "height": details.get("height", 600),
        }
    return default


def get_item_listing_card_image(item) -> dict:
    """Card image for a listing: real featured media, else first gallery photo, else placeholder."""
    default = {
        "url": "/static/img/placeholder-default.svg",
        "width": 400,
        "height": 300,
    }
    if not isinstance(item, dict):
        return default
    embedded = item.get("_embedded") if isinstance(item.get("_embedded"), dict) else {}
    media = embedded.get("wp:featuredmedia")
    card = get_listing_card_image(media)
    if not is_placeholder_image(card.get("url")):
        return card
    gallery_url = listing_gallery_photo_url(item)
    if gallery_url:
        return {
            "url": gallery_url,
            "width": 400,
            "height": 300,
        }
    return default


HERO_MOBILE_VARIANTS = {
    "/static/img/veria-hero2.webp": "/static/img/veria-hero2-640.webp",
    "/static/img/veria-hero1.webp": "/static/img/veria-hero2-640.webp",
}


def get_hero_image_sources(image_url: str) -> dict:
    """Map hero slide URLs to desktop/mobile sources for responsive LCP."""
    mobile = HERO_MOBILE_VARIANTS.get(image_url, image_url)
    return {
        "desktop": image_url,
        "mobile": mobile,
        "use_picture": mobile != image_url,
    }

CATEGORY_PATH_BY_POST_TYPE = {
    post_type: get_category_url_path(category)
    for category, post_type in POST_TYPES.items()
}

VERIA_LOCATION_PHRASE = "Veria (Veroia), Imathia, Greece"

HOME_SEO_TITLE = "Veria Greece Travel Guide – Churches, Museums & Vergina"
HOME_SEO_DESCRIPTION = (
    "Plan your trip to Veria (Veroia), Imathia, Greece: Byzantine churches, "
    "museums, Royal Tombs of Vergina, archaeological sites and Apostle Paul's legacy in Macedonia."
)
HOME_HERO_TITLE = "Veria, Greece: Byzantine Churches & Macedonian Heritage"
HOME_HERO_SUBTITLE = (
    "Explore Veria (Veroia) in Imathia — 60+ Byzantine churches, museums, "
    "Royal Tombs of Vergina and the Vema where Apostle Paul preached."
)
HOME_ABOUT_TEXT = (
    "<p>Discover Veria (Veroia), a historic city in Imathia, northern Greece, "
    "where Byzantine churches, museums and archaeological treasures meet Macedonian heritage. "
    "Use Veria Guide to explore churches linked to Apostle Paul, the Royal Tombs of Vergina "
    "and hidden gems across the region.</p>"
)
HOME_OG_IMAGE = "/static/img/veria-hero2.webp"
LEGACY_HOME_HERO_TITLE = "Veria: Where History Meets Hospitality"


def get_homepage_og_image_url() -> str:
    """Absolute URL for homepage Open Graph image."""
    return f"{SITE_URL.rstrip('/')}{HOME_OG_IMAGE}"


def get_homepage_listing_alt(category_slug: str, title: str) -> str:
    """SEO-friendly alt text for homepage listing card images."""
    clean = decode_entities(strip_tags(title)) if title else ""
    clean = re.sub(r"\s+", " ", clean).strip()
    if ":" in clean:
        clean = clean.split(":", 1)[0].strip()
    from app.i18n import tr

    if category_slug == "religious_sites":
        suffix = tr("Byzantine church in Veria, Greece")
        return f"{clean} – {suffix}" if clean else suffix
    if category_slug == "museums":
        suffix = tr("museum in Veria, Imathia, Greece")
        return f"{clean} – {suffix}" if clean else suffix
    if category_slug == "archaeological_sites":
        suffix = tr("archaeological site near Veria, Greece")
        return f"{clean} – {suffix}" if clean else suffix
    return clean or tr("Veria Guide listing")


def apply_homepage_seo_content(settings: dict) -> dict:
    """Upgrade legacy WordPress homepage copy to SEO-focused heritage text."""
    hero = settings.get("hero") or {}
    slides = list(hero.get("slides") or [])
    for slide in slides:
        title = (slide.get("title") or "").strip()
        if not title or title == LEGACY_HOME_HERO_TITLE:
            slide["title"] = HOME_HERO_TITLE
        subtitle = (slide.get("subtitle") or "").strip()
        if not subtitle or "legendary revani" in subtitle.lower() or "48 byzantine" in subtitle.lower():
            slide["subtitle"] = HOME_HERO_SUBTITLE
    hero["slides"] = slides
    settings["hero"] = hero

    about = settings.get("about_text") or ""
    about_lower = about.lower()
    if (
        not about.strip()
        or "restaurants" in about_lower
        or "cafés" in about_lower
        or "cafes" in about_lower
        or "accommodations" in about_lower
    ):
        settings["about_text"] = HOME_ABOUT_TEXT
    return settings


def generate_homepage_schema(description: str = None) -> str:
    """JSON-LD for homepage: WebSite, Organization and TouristDestination."""
    from app.i18n import current_lang, localized_path, tr

    lang = current_lang()
    desc = tr(description or HOME_SEO_DESCRIPTION, lang)
    base = SITE_URL.rstrip("/")
    home_url = get_page_url("/")
    search_url = f"{base}{localized_path('/search')}?q={{search_term_string}}"
    logo_url = f"{base}/static/img/veria-guide-logo.png"
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{home_url.rstrip('/')}/#website",
                "url": home_url,
                "name": SITE_NAME,
                "description": desc,
                "inLanguage": lang,
                "publisher": {"@id": f"{base}/#organization"},
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": search_url,
                    "query-input": "required name=search_term_string",
                },
            },
            {
                "@type": "Organization",
                "@id": f"{base}/#organization",
                "name": SITE_NAME,
                "url": f"{base}/",
                "email": "info@veriaguide.gr",
                "logo": {
                    "@type": "ImageObject",
                    "url": logo_url,
                    "width": 1718,
                    "height": 737,
                },
                "image": logo_url,
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Veria",
                    "addressRegion": "Imathia",
                    "addressCountry": "GR",
                },
                "areaServed": [
                    {
                        "@type": "City",
                        "name": "Veria",
                        "alternateName": ["Veroia", "Βέροια"],
                    },
                    {
                        "@type": "AdministrativeArea",
                        "name": "Imathia",
                    },
                ],
                "contactPoint": {
                    "@type": "ContactPoint",
                    "contactType": "customer support",
                    "email": "info@veriaguide.gr",
                    "availableLanguage": ["English", "Greek", "German"],
                    "areaServed": "GR",
                },
            },
            {
                "@type": "TouristDestination",
                "@id": f"{base}/#veria",
                "name": "Veria",
                "alternateName": ["Veroia", "Βέροια"],
                "description": desc,
                "url": f"{base}/",
                "touristType": ["Cultural tourism", "Religious tourism", "Heritage tourism"],
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Veria",
                    "addressRegion": "Imathia",
                    "addressCountry": "GR",
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": 40.5246,
                    "longitude": 22.2022,
                },
            },
        ],
    }
    return json.dumps(schema, ensure_ascii=False)


def get_page_url(path: str = "/") -> str:
    """Build canonical URL for a page path, including /el or /de when localized."""
    from app.i18n import localized_path

    base = SITE_URL.rstrip("/")
    path = localized_path(path)
    if path == "/":
        return f"{base}/"
    return f"{base}{path}"


def build_pagination_seo_urls(
    path: str,
    page: int,
    total_pages: int,
    query_params: dict | None = None,
) -> dict[str, str | None]:
    """Build canonical, prev and next URLs for paginated listing pages."""
    from urllib.parse import urlencode

    base = get_page_url(path)
    params = {k: v for k, v in (query_params or {}).items() if k != "page" and v}

    def page_url(page_number: int) -> str:
        page_params = dict(params)
        if page_number > 1:
            page_params["page"] = str(page_number)
        if page_params:
            return f"{base}?{urlencode(page_params)}"
        return base

    canonical = page_url(page)
    prev_url = page_url(page - 1) if page > 1 else None
    next_url = page_url(page + 1) if page < total_pages else None
    return {"canonical": canonical, "prev": prev_url, "next": next_url}


def get_meta_data(title=None, description=None, image=None, type="website", url=None, robots=None):
    """Generate meta data for SEO"""
    from app.i18n import tr

    meta = {
        "title": tr(title) if title else SITE_NAME,
        "description": tr(description) if description else tr(SITE_DESCRIPTION),
        "site_name": SITE_NAME,
        "url": url if url else get_page_url("/"),
        "image": image if image else f"{SITE_URL}/static/img/default-og.jpg",
        "type": type,
        "robots": robots,
        "pagination_prev": None,
        "pagination_next": None,
    }
    
    # If title is provided, append site name
    if title:
        meta["title"] = f"{tr(title)} | {SITE_NAME}"
    
    return meta


def _religious_site_short_title(title: str) -> str:
    """Return the primary name from an SEO-style church title."""
    clean = decode_entities(strip_tags(title))
    return split_display_title(clean)["title"]


def enhance_religious_site_meta_title(title: str) -> str:
    """Add location context to church page titles when missing."""
    clean = strip_tags(title)
    lower = clean.lower()
    if any(token in lower for token in ("veria", "veroia", "imathia", "vergina", "greece")):
        return clean
    short = _religious_site_short_title(clean)
    return f"{short} – Byzantine Church in Veria, Greece"


def enhance_religious_site_description(title: str, description: str) -> str:
    """Ensure religious site pages have a useful meta description for SEO."""
    clean_title = _religious_site_short_title(title)
    desc = description.strip() if description else ""

    if not desc:
        desc = (
            f"Visit {clean_title}, a Byzantine church in {VERIA_LOCATION_PHRASE}. "
            "Visiting hours, map and travel guide."
        )
    elif not any(token in desc.lower() for token in ("veria", "veroia", "imathia", "greece")):
        desc = f"{desc} Located in {VERIA_LOCATION_PHRASE}."

    if len(desc) > 160:
        desc = desc[:157].rsplit(" ", 1)[0] + "..."
    return desc


def get_religious_site_seo_intro(title: str, description: str = "", content: str = "") -> str | None:
    """On-page intro only when the detail body is thin — avoids duplicating WP content."""
    excerpt = decode_entities(strip_tags(description)).strip() if description else ""
    body = decode_entities(strip_tags(content)).strip() if content else ""

    if body and len(body) >= 80:
        return None

    if excerpt and body and len(excerpt) >= 30:
        excerpt_start = excerpt[:80].lower()
        if body.lower().startswith(excerpt_start.rstrip(".…")):
            return None

    clean_title = _religious_site_short_title(title)
    if excerpt and len(excerpt) >= 40:
        if not any(token in excerpt.lower() for token in ("veria", "veroia", "imathia")):
            return f"{excerpt} This Byzantine church is in {VERIA_LOCATION_PHRASE}."
        return excerpt

    return (
        f"{clean_title} is a Byzantine church in {VERIA_LOCATION_PHRASE}. "
        "Discover its history, visiting hours and how to get there."
    )


def get_religious_site_listing_excerpt(title: str, excerpt: str) -> str:
    """SEO-friendly excerpt fallback for church listing cards."""
    text = excerpt.strip() if excerpt else ""
    if text and len(text) >= 40:
        return text
    short = _religious_site_short_title(title)
    return (
        f"{short} is a Byzantine church in {VERIA_LOCATION_PHRASE}. "
        "View visiting hours, location and travel tips."
    )


def generate_religious_site_breadcrumb_schema(title: str, slug: str) -> str:
    """JSON-LD breadcrumbs for church detail pages."""
    from app.i18n import tr

    clean_title = _religious_site_short_title(title)
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": tr("Home"),
                "item": get_page_url("/"),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": tr("Byzantine Churches in Veria"),
                "item": get_page_url(f"/{get_category_url_path('religious_sites')}"),
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": clean_title,
                "item": get_page_url(f"/{get_category_url_path('religious_sites')}/{slug}"),
            },
        ],
    }
    return json.dumps(schema, ensure_ascii=False)


def generate_google_maps_url(lat, lng):
    """Generate Google Maps URL for directions"""
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"

def generate_schema_markup(post_type, post_data):
    """Generate JSON-LD schema markup based on post type"""
    schema = {
        "@context": "https://schema.org",
    }
    
    category_path = CATEGORY_PATH_BY_POST_TYPE.get(post_type, post_type)
    slug = post_data.get("slug", "")
    excerpt = strip_tags(post_data.get("excerpt", {}).get("rendered", ""))
    page_title = post_data.get("title", {}).get("rendered", "")

    # Common properties for all types
    common_props = {
        "name": strip_tags(page_title),
        "description": excerpt,
        "url": get_page_url(f"/{category_path}/{slug}"),
        "image": get_featured_image(post_data) or f"{SITE_URL}{get_category_placeholder_url(post_type)}",
    }

    if post_data.get("date"):
        common_props["datePublished"] = post_data["date"]
    if post_data.get("modified"):
        common_props["dateModified"] = post_data["modified"]

    from app.i18n import current_lang

    if post_type == "religious_site" and current_lang() == "en":
        common_props["description"] = enhance_religious_site_description(page_title, excerpt)
    
    # Add location data if available
    # WP/ACF may return acf as [] when no field group is active — guard before .get()
    if "acf" in post_data and isinstance(post_data["acf"], dict):
        location = post_data["acf"].get("location_map") or post_data["acf"].get("location")
        if location and isinstance(location, dict) and location.get("lat") and location.get("lng"):
            common_props["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": location["lat"],
                "longitude": location["lng"]
            }

            address_text = location.get("address") or post_data["acf"].get("address", "")
            if address_text:
                common_props["address"] = {
                    "@type": "PostalAddress",
                    "streetAddress": address_text,
                    "addressLocality": "Veria",
                    "addressRegion": "Imathia, Central Macedonia",
                    "addressCountry": "GR"
                }
            else:
                common_props["address"] = {
                    "@type": "PostalAddress",
                    "addressLocality": "Veria",
                    "addressRegion": "Imathia, Central Macedonia",
                    "addressCountry": "GR"
                }
    
    # Add opening hours if available
    if isinstance(post_data.get("acf"), dict) and "opening_hours" in post_data["acf"]:
        common_props["openingHoursSpecification"] = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days:
            day_key = day.lower()
            if day_key in post_data["acf"]["opening_hours"]:
                hours = post_data["acf"]["opening_hours"][day_key]
                if hours and hours != "Closed":
                    common_props["openingHoursSpecification"].append({
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": day,
                        "opens": hours.split("-")[0].strip() if "-" in hours else "",
                        "closes": hours.split("-")[1].strip() if "-" in hours else ""
                    })
    
    # Type-specific schema
    if post_type == "museum":
        schema["@type"] = "Museum"
        schema.update(common_props)
        
        # Add museum-specific properties
        if "acf" in post_data and "admission_fee" in post_data["acf"]:
            schema["ticketPrice"] = post_data["acf"]["admission_fee"]
    
    elif post_type == "restaurant" or post_type == "cafe" or post_type == "bar_club":
        if post_type == "restaurant":
            schema["@type"] = "Restaurant"
        elif post_type == "cafe":
            schema["@type"] = "CafeOrCoffeeShop"
        else:
            schema["@type"] = "BarOrPub"
            
        schema.update(common_props)
        
        # Add food establishment specific properties
        if "acf" in post_data:
            if "price_range" in post_data["acf"]:
                schema["priceRange"] = post_data["acf"]["price_range"]
            if "cuisine" in post_data["acf"]:
                schema["servesCuisine"] = post_data["acf"]["cuisine"]
    
    elif post_type == "religious_site":
        schema["@type"] = "Church"
        schema.update(common_props)
        schema["address"] = common_props.get("address", {
            "@type": "PostalAddress",
            "addressLocality": "Veria",
            "addressRegion": "Imathia, Central Macedonia",
            "addressCountry": "GR"
        })

    elif post_type == "archaeological_site":
        schema["@type"] = "TouristAttraction"
        schema.update(common_props)

    elif post_type == "hiking_trail":
        schema["@type"] = "TouristAttraction"
        schema["additionalType"] = "https://schema.org/TrailSystem"
        schema.update(common_props)
        
        # Add trail-specific properties
        if "acf" in post_data:
            if "difficulty" in post_data["acf"]:
                schema["additionalProperty"] = {
                    "@type": "PropertyValue",
                    "name": "difficulty",
                    "value": post_data["acf"]["difficulty"]
                }
            if "length" in post_data["acf"]:
                schema["additionalProperty"] = {
                    "@type": "PropertyValue",
                    "name": "length",
                    "value": post_data["acf"]["length"]
                }
    else:
        # Default to TouristAttraction for other types
        schema["@type"] = "TouristAttraction"
        schema.update(common_props)
    
    return json.dumps(schema, ensure_ascii=False)

def paginate(items, page, per_page):
    """Simple pagination helper"""
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_items = items[start:end]
    total_pages = (len(items) + per_page - 1) // per_page
    
    return {
        "items": paginated_items,
        "page": page,
        "per_page": per_page,
        "total": len(items),
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

def format_opening_hours(hours_data):
    """Format opening hours for display"""
    if not hours_data:
        return []
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    formatted = []
    
    for day in days:
        if day in hours_data:
            formatted.append(f"{day.capitalize()}: {hours_data[day]}")
    
    return formatted

def get_google_maps_api_key():
    """Return Google Maps API key for templates"""
    return os.environ.get("GOOGLE_MAPS_API_KEY")


_INVALID_SLUGS = frozenset({"", "null", "none", "undefined", "nan"})
MAP_COORD_FIELDS = ("location_map", "meeting_point_map", "trail_map", "location")


def usable_listing_slug(slug) -> str | None:
    """Return a slug safe for URL building, or None if empty/placeholder."""
    if slug is None:
        return None
    text = str(slug).strip()
    if not text or text.lower() in _INVALID_SLUGS:
        return None
    return text


def listing_map_point(item) -> dict | None:
    """First ACF map field on a listing that has lat/lng."""
    if not isinstance(item, dict):
        return None
    acf = item.get("acf")
    if not isinstance(acf, dict):
        return None
    for field in MAP_COORD_FIELDS:
        data = acf.get(field)
        if (
            isinstance(data, dict)
            and data.get("lat") not in (None, "")
            and data.get("lng") not in (None, "")
            and str(data.get("lat")).strip() != ""
            and str(data.get("lng")).strip() != ""
        ):
            return data
    return None


def listing_detail_href(item, category_path: str) -> str:
    """Public detail path, or empty string when the slug is unusable."""
    slug = usable_listing_slug(item.get("slug") if isinstance(item, dict) else None)
    if not slug or not category_path:
        return ""
    path = str(category_path).strip("/")
    return f"/{path}/{slug}"