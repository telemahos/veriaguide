import os
import re
import json
from datetime import datetime
from app.config import SITE_NAME, SITE_URL, SITE_DESCRIPTION, GOOGLE_MAPS_API_KEY

def strip_tags(html_content):
    """Remove HTML tags from content"""
    return re.sub(r'<[^>]+>', '', html_content)

def format_date(date_string, format_str="%d %B %Y"):
    """Format date string"""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
        return date_obj.strftime(format_str)
    except:
        return date_string

def get_featured_image(post):
    """Extract featured image from WordPress post"""
    if "_embedded" in post and "wp:featuredmedia" in post["_embedded"]:
        media = post["_embedded"]["wp:featuredmedia"]
        if media and len(media) > 0:
            if "source_url" in media[0]:
                return media[0]["source_url"]
            elif "media_details" in media[0] and "sizes" in media[0]["media_details"]:
                sizes = media[0]["media_details"]["sizes"]
                if "large" in sizes:
                    return sizes["large"]["source_url"]
                elif "medium" in sizes:
                    return sizes["medium"]["source_url"]
                elif "full" in sizes:
                    return sizes["full"]["source_url"]
    return "/static/img/placeholder.jpg"

def get_meta_data(title=None, description=None, image=None, type="website"):
    """Generate meta data for SEO"""
    meta = {
        "title": title if title else SITE_NAME,
        "description": description if description else SITE_DESCRIPTION,
        "site_name": SITE_NAME,
        "url": SITE_URL,
        "image": image if image else f"{SITE_URL}/static/img/default-og.jpg",
        "type": type
    }
    
    # If title is provided, append site name
    if title:
        meta["title"] = f"{title} | {SITE_NAME}"
    
    return meta

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
        "image": get_featured_image(post_data),
    }
    
    # Add location data if available
    if "acf" in post_data and "location" in post_data["acf"]:
        common_props["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": post_data["acf"]["location"]["lat"],
            "longitude": post_data["acf"]["location"]["lng"]
        }
        
        # Add address if available
        if "address" in post_data["acf"]:
            common_props["address"] = {
                "@type": "PostalAddress",
                "streetAddress": post_data["acf"].get("address", ""),
                "addressLocality": "Veria",
                "addressRegion": "Central Macedonia",
                "addressCountry": "Greece"
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
        return "Information not available"
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    formatted = []
    
    for day in days:
        if day in hours_data:
            formatted.append(f"{day.capitalize()}: {hours_data[day]}")
    
    return formatted

def get_google_maps_api_key():
    """Return Google Maps API key for templates"""
    return os.environ.get("GOOGLE_MAPS_API_KEY")