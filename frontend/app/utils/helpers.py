import os
import html
import re
import json
from datetime import datetime
from typing import Dict, Optional
from app.config import SITE_NAME, SITE_URL, SITE_DESCRIPTION, GOOGLE_MAPS_API_KEY, POST_TYPES
from app.utils.category_urls import get_category_url_path

def strip_tags(html_content):
    """Remove HTML tags from content"""
    return re.sub(r'<[^>]+>', '', html_content)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates in kilometres."""
    from math import radians, sin, cos, sqrt, atan2

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
    except:
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
        or lower.endswith("placeholder.svg")
        or "placeholder-default.svg" in lower
    )


def get_category_placeholder_url(post_type: str = "default") -> str:
    return CATEGORY_PLACEHOLDER_URLS.get(post_type, CATEGORY_PLACEHOLDER_URLS["default"])


def get_category_gallery_icon(post_type: str = "default") -> str:
    return CATEGORY_GALLERY_ICONS.get(post_type, CATEGORY_GALLERY_ICONS["default"])


def get_featured_image(post):
    """Extract featured image from WordPress post"""
    if "_embedded" in post and "wp:featuredmedia" in post["_embedded"]:
        media = post["_embedded"]["wp:featuredmedia"]
        if media and len(media) > 0:
            if "source_url" in media[0]:
                url = media[0]["source_url"]
                return None if is_placeholder_image(url) else url
            elif "media_details" in media[0] and "sizes" in media[0]["media_details"]:
                sizes = media[0]["media_details"]["sizes"]
                for size in ("large", "medium", "full"):
                    if size in sizes:
                        url = sizes[size]["source_url"]
                        return None if is_placeholder_image(url) else url
    return None


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
    if not media:
        return default

    details = media.get("media_details") or {}
    sizes = details.get("sizes") or {}
    for key in ("medium_large", "medium", "thumbnail"):
        sized = sizes.get(key) or {}
        if sized.get("source_url"):
            return {
                "url": sized["source_url"],
                "width": sized.get("width", 400),
                "height": sized.get("height", 300),
            }

    source_url = media.get("source_url")
    if source_url and not is_placeholder_image(source_url):
        return {
            "url": source_url,
            "width": details.get("width", 800),
            "height": details.get("height", 600),
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
    if category_slug == "religious_sites":
        return f"{clean} – Byzantine church in Veria, Greece" if clean else "Byzantine church in Veria, Greece"
    if category_slug == "museums":
        return f"{clean} – museum in Veria, Imathia, Greece" if clean else "Museum in Veria, Imathia, Greece"
    if category_slug == "archaeological_sites":
        return f"{clean} – archaeological site near Veria, Greece" if clean else "Archaeological site near Veria, Greece"
    return clean or "Veria Guide listing"


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
    desc = description or HOME_SEO_DESCRIPTION
    base = SITE_URL.rstrip("/")
    og_image = get_homepage_og_image_url()
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{base}/#website",
                "url": f"{base}/",
                "name": SITE_NAME,
                "description": desc,
                "publisher": {"@id": f"{base}/#organization"},
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{base}/search?q={{search_term_string}}",
                    "query-input": "required name=search_term_string",
                },
            },
            {
                "@type": "Organization",
                "@id": f"{base}/#organization",
                "name": SITE_NAME,
                "url": f"{base}/",
                "logo": og_image,
            },
            {
                "@type": "TouristDestination",
                "name": "Veria",
                "alternateName": ["Veroia", "Βέροια"],
                "description": desc,
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Veria",
                    "addressRegion": "Imathia",
                    "addressCountry": "GR",
                },
            },
        ],
    }
    return json.dumps(schema, ensure_ascii=False)


def get_page_url(path: str = "/") -> str:
    """Build canonical URL for a page path."""
    base = SITE_URL.rstrip("/")
    if not path or path == "/":
        return f"{base}/"
    return f"{base}{path if path.startswith('/') else '/' + path}"


def build_pagination_seo_urls(
    path: str,
    page: int,
    total_pages: int,
    query_params: Optional[dict] = None,
) -> Dict[str, Optional[str]]:
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
    meta = {
        "title": title if title else SITE_NAME,
        "description": description if description else SITE_DESCRIPTION,
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
        meta["title"] = f"{title} | {SITE_NAME}"
    
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
    clean_title = _religious_site_short_title(title)
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": get_page_url("/"),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Byzantine Churches in Veria",
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
        "url": f"{SITE_URL.rstrip('/')}/{category_path}/{slug}",
        "image": get_featured_image(post_data) or f"{SITE_URL}{get_category_placeholder_url(post_type)}",
    }

    if post_data.get("date"):
        common_props["datePublished"] = post_data["date"]
    if post_data.get("modified"):
        common_props["dateModified"] = post_data["modified"]

    if post_type == "religious_site":
        common_props["description"] = enhance_religious_site_description(page_title, excerpt)
    
    # Add location data if available
    if "acf" in post_data:
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
    if "acf" in post_data and "opening_hours" in post_data["acf"]:
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