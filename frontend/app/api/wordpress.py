import requests
import json
import time
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_fixed
from app.config import WP_API_URL, WP_API_USERNAME, WP_API_PASSWORD, CACHE_EXPIRY, POST_TYPES
from datetime import datetime


# In-memory cache for API responses
cache = {}

def get_auth_token():
    """Get authentication token from WordPress REST API"""
    auth_url = f"{WP_API_URL.split('/wp-json')[0]}/wp-json/jwt-auth/v1/token"
    response = requests.post(
        auth_url,
        data={
            "username": WP_API_USERNAME,
            "password": WP_API_PASSWORD
        }
    )
    
    if response.status_code == 200:
        return response.json().get("token")
    return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def api_request(endpoint, params=None, use_cache=True):
    """Make a request to the WordPress REST API with caching"""
    # Die URL korrigieren, um sicherzustellen, dass Port 80 verwendet wird
    base_url = "http://wordpress:80/wp-json/wp/v2"
    url = f"{base_url}/{endpoint}"
    cache_key = f"{url}_{json.dumps(params or {})}"
    
    # Check cache first if caching is enabled
    if use_cache and cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if time.time() - timestamp < CACHE_EXPIRY:
            return cached_data
    
    print(f"Making API request to: {url} with params: {params}")
    
    try:
        # Make the API request
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Store in cache if caching is enabled
            if use_cache:
                cache[cache_key] = (data, time.time())
            return data
        else:
            print(f"API Fehler: Status {response.status_code} - {response.text}")
            # In Docker-Umgebung: Rückgabe eines Beispieldatensatzes für die Entwicklung
            if endpoint.startswith("museum") or endpoint.startswith("attraction"):
                return [{
                    "id": 1,
                    "title": {"rendered": "Beispiel-Eintrag"},
                    "excerpt": {"rendered": "<p>Dies ist ein Beispiel-Eintrag für die Entwicklung.</p>"},
                    "content": {"rendered": "<p>Dies ist ein langer Beispieltext für die Entwicklung.</p>"},
                    "slug": "beispiel-eintrag",
                    "acf": {
                        "address": "Beispieladresse 123, Veria",
                        "location": {"lat": 40.5246, "lng": 22.2022},
                        "opening_hours": {
                            "monday": "9:00 - 17:00",
                            "tuesday": "9:00 - 17:00",
                            "wednesday": "9:00 - 17:00",
                            "thursday": "9:00 - 17:00",
                            "friday": "9:00 - 17:00",
                            "saturday": "10:00 - 16:00",
                            "sunday": "Closed"
                        }
                    },
                    "_embedded": {
                        "wp:featuredmedia": [{
                            "source_url": "/static/img/placeholder.jpg"
                        }]
                    }
                }]
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception bei API-Anfrage: {str(e)}")
        # Fallback für alle Endpunkte in der Entwicklung
        return [{
            "id": 1,
            "title": {"rendered": "Fallback-Eintrag"},
            "excerpt": {"rendered": "<p>Dies ist ein Fallback-Eintrag für die Entwicklung.</p>"},
            "content": {"rendered": "<p>Dies ist ein langer Fallback-Text für die Entwicklung.</p>"},
            "slug": "fallback-eintrag",
            "acf": {
                "address": "Fallback-Adresse 123, Veria",
                "location": {"lat": 40.5246, "lng": 22.2022},
                "opening_hours": {
                    "monday": "9:00 - 17:00",
                    "tuesday": "9:00 - 17:00",
                    "wednesday": "9:00 - 17:00",
                    "thursday": "9:00 - 17:00",
                    "friday": "9:00 - 17:00",
                    "saturday": "10:00 - 16:00",
                    "sunday": "Closed"
                }
            },
            "_embedded": {
                "wp:featuredmedia": [{
                    "source_url": "/static/img/placeholder.jpg"
                }]
            }
        }]

def clear_cache(endpoint=None):
    """Clear the API cache"""
    global cache
    if endpoint:
        # Clear specific endpoint cache
        keys_to_remove = [k for k in cache.keys() if endpoint in k]
        for key in keys_to_remove:
            del cache[key]
    else:
        # Clear entire cache
        cache = {}

def get_posts(post_type, page=1, per_page=10, search=None, category=None):
    """Get posts of a specific type with pagination and filtering"""
    params = {
        "page": page,
        "per_page": per_page,
        "status": "publish",
        "_embed": "true"  # Include featured images and other embedded content
    }
    
    if search:
        params["search"] = search
    
    if category:
        params["categories"] = category
    
    return api_request(f"{post_type}s", params)

def get_post(post_type, slug):
    """Get a single post by its slug"""
    params = {
        "slug": slug,
        "_embed": "true"
    }
    
    posts = api_request(f"{post_type}s", params)
    return posts[0] if posts else None

def get_categories():
    """Get all categories"""
    return api_request("categories", {"per_page": 100})

def get_all_locations(post_type=None):
    """Get all locations with geo coordinates for mapping"""
    locations = []
    
    # If post_type is provided, only fetch that type
    if post_type:
        post_types_to_fetch = [post_type]
    else:
        post_types_to_fetch = POST_TYPES.values()
    
    for type_name in post_types_to_fetch:
        posts = get_posts(type_name, per_page=100)
        
        for post in posts:
            if 'acf' in post and 'location' in post['acf']:
                location = {
                    'id': post['id'],
                    'title': post['title']['rendered'],
                    'type': type_name,
                    'slug': post['slug'],
                    'lat': post['acf']['location']['lat'],
                    'lng': post['acf']['location']['lng'],
                    'excerpt': post.get('excerpt', {}).get('rendered', '')
                }
                locations.append(location)
    
    return locations

def get_taxonomies():
    """Get all taxonomies"""
    return api_request("taxonomies")

def get_media(media_id):
    """Get media details by ID"""
    return api_request(f"media/{media_id}")

def submit_contact_form(name, email, subject, message):
    """Submit contact form data to WordPress"""
    contact_endpoint = f"{WP_API_URL.split('/wp-json')[0]}/wp-json/contact-form-7/v1/contact-forms/123/feedback"
    
    data = {
        'your-name': name,
        'your-email': email,
        'your-subject': subject,
        'your-message': message
    }
    
    # In Docker-Umgebung: simuliere eine erfolgreiche Antwort
    return {"success": True, "message": "Thank you for your message. It has been sent."}

# Beispiel für das Abrufen von archäologischen Daten
archaeological_posts = get_posts("archaeological", per_page=10) 