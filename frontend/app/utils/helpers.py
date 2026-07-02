import os
import html
import re
import json
from datetime import datetime
from app.config import SITE_NAME, SITE_URL, SITE_DESCRIPTION, GOOGLE_MAPS_API_KEY

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

def get_page_url(path: str = "/") -> str:
    """Build canonical URL for a page path."""
    base = SITE_URL.rstrip("/")
    if not path or path == "/":
        return f"{base}/"
    return f"{base}{path if path.startswith('/') else '/' + path}"


def get_meta_data(title=None, description=None, image=None, type="website", url=None):
    """Generate meta data for SEO"""
    meta = {
        "title": title if title else SITE_NAME,
        "description": description if description else SITE_DESCRIPTION,
        "site_name": SITE_NAME,
        "url": url if url else get_page_url("/"),
        "image": image if image else f"{SITE_URL}/static/img/default-og.jpg",
        "type": type
    }
    
    # If title is provided, append site name
    if title:
        meta["title"] = f"{title} | {SITE_NAME}"
    
    return meta


def enhance_religious_site_description(title: str, description: str) -> str:
    """Ensure religious site pages have a useful meta description for SEO."""
    clean_title = strip_tags(title)
    if description and len(description.strip()) >= 80:
        return description.strip()
    return (
        f"Visit {clean_title} in Veria (Veroia), Imathia, Greece. "
        "Byzantine church guide with location, visiting hours and travel tips."
    )

def generate_google_maps_url(lat, lng):
    """Generate Google Maps URL for directions"""
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"

def generate_schema_markup(post_type, post_data):
    """Generate JSON-LD schema markup based on post type"""
    schema = {
        "@context": "https://schema.org",
    }
    
    # Common properties for all types
    common_props = {
        "name": post_data.get("title", {}).get("rendered", ""),
        "description": strip_tags(post_data.get("excerpt", {}).get("rendered", "")),
        "url": f"{SITE_URL}/{post_type}/{post_data.get('slug', '')}",
        "image": get_featured_image(post_data) or f"{SITE_URL}{get_category_placeholder_url(post_type)}",
    }
    
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