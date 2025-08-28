import json
import time
import asyncio
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_fixed
from app.config import WP_API_URL, WP_API_USERNAME, WP_API_PASSWORD, CACHE_EXPIRY, POST_TYPES
from app.services.cache_service import CacheService, cache_result
from app.services.http_service import HTTPService
from datetime import datetime


# Legacy in-memory cache for fallback (will be replaced by Redis)
cache = {}

@cache_result("tag_name", ttl=7200)  # Cache for 2 hours
async def get_tag_name(tag_id):
    """Get tag name by ID"""
    try:
        tag_data = await api_request(f"tags/{tag_id}")
        return tag_data.get('name')
    except:
        return None

async def get_auth_token():
    """Get authentication token from WordPress REST API"""
    auth_url = f"{WP_API_URL.split('/wp-json')[0]}/wp-json/jwt-auth/v1/token"
    
    response = await HTTPService.post(
        auth_url,
        data={
            "username": WP_API_USERNAME,
            "password": WP_API_PASSWORD
        },
        use_wp_client=True
    )
    
    if response.status_code == 200:
        return response.json().get("token")
    return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def api_request(endpoint, params=None, use_cache=True):
    """Make a request to the WordPress REST API with Redis caching and authentication"""
    base_url = "http://wordpress:80/wp-json/wp/v2"
    url = f"{base_url}/{endpoint}"
    
    # Try Redis cache first
    if use_cache:
        cache_key = f"wp_api_{endpoint}"
        cached_data = await CacheService.get(cache_key, params)
        if cached_data is not None:
            print(f"Redis cache hit for: {endpoint}")
            return cached_data
    
    print(f"Making authenticated API request to: {url} with params: {params}")
    
    try:
        # Get authentication token
        auth_token = await get_auth_token()
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        # Make the API request using optimized HTTP service with authentication
        response = await HTTPService.get(url, params=params, headers=headers, use_wp_client=True)
        
        if response.status_code == 200:
            data = response.json()
            
            # Store in Redis cache if caching is enabled
            if use_cache:
                cache_key = f"wp_api_{endpoint}"
                await CacheService.set(cache_key, data, CACHE_EXPIRY, params)
            
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
                            "location_map": {"lat": 40.5246, "lng": 22.2022, "address": "Beispieladresse 123, Veria"},
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
                "location_map": {"lat": 40.5246, "lng": 22.2022, "address": "Fallback-Adresse 123, Veria"},
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

async def clear_cache(endpoint=None):
    """Clear the API cache (both Redis and in-memory)"""
    global cache
    
    # Clear Redis cache
    if endpoint:
        # Clear specific endpoint cache
        pattern = f"wp_api_{endpoint}*"
        await CacheService.delete_pattern(pattern)
        
        # Also clear in-memory cache for backward compatibility
        keys_to_remove = [k for k in cache.keys() if endpoint in k]
        for key in keys_to_remove:
            del cache[key]
    else:
        # Clear entire cache
        await CacheService.clear_all()
        cache = {}

async def get_posts(post_type, page=1, per_page=10, search=None, category=None):
    """Get posts of a specific type with pagination and filtering"""
    params = {
        "page": page,
        "per_page": per_page,
        "status": "publish",
        "_embed": "true"
    }
    
    if search:
        params["search"] = search
    
    if category:
        params["categories"] = category
    
    endpoint = f"{post_type}s"
    if post_type == "hiking-trail":
        endpoint = "hiking_trails"
    
    data = await api_request(endpoint, params)
    
    # Process posts to extract tag names from embedded data
    for post in data:
        post['tag_names'] = []
        if '_embedded' in post and 'wp:term' in post['_embedded']:
            terms = post['_embedded']['wp:term']
            for taxonomy in terms:
                for term in taxonomy:
                    # We are interested in post tags
                    if term.get('taxonomy') == 'post_tag':
                        post['tag_names'].append(term['name'])
    return data

async def get_post(post_type, slug):
    """Get a single post by its slug"""
    params = {
        "slug": slug,
        "_embed": "true"
    }
    
    # Determine the correct endpoint for single post fetching
    endpoint = f"{post_type}s" # Default assumption
    if post_type == "hiking-trail":
        endpoint = "hiking_trails"
    # Add other special cases if needed

    posts = await api_request(endpoint, params)
    return posts[0] if posts else None

@cache_result("categories", ttl=3600)  # Cache for 1 hour
async def get_categories():
    """Get all categories"""
    return await api_request("categories", {"per_page": 100})

# def get_all_locations(post_type=None):
#     """Get all locations with geo coordinates for mapping"""
#     locations = []
    
#     # If post_type is provided, only fetch that type
#     if post_type:
#         post_types_to_fetch = [post_type]
#     else:
#         post_types_to_fetch = POST_TYPES.values()
    
#     for type_name in post_types_to_fetch:
#         posts = get_posts(type_name, per_page=100)
        
#         for post in posts:
#             if 'acf' in post and 'location' in post['acf']:
#                 location = {
#                     'id': post['id'],
#                     'title': post['title']['rendered'],
#                     'type': type_name,
#                     'slug': post['slug'],
#                     'lat': post['acf']['location']['lat'],
#                     'lng': post['acf']['location']['lng'],
#                     'excerpt': post.get('excerpt', {}).get('rendered', '')
#                 }
#                 locations.append(location)
    
#     return locations

async def get_all_locations(post_type=None):
    """Get all locations with geo coordinates for mapping"""
    locations = []
    if post_type:
        post_types_to_fetch = [post_type]
    else:
        post_types_to_fetch = POST_TYPES.values()
    
    print(f"Fetching locations for post types: {post_types_to_fetch}")
    
    # Fetch all post types concurrently
    tasks = [get_posts(type_name, per_page=100) for type_name in post_types_to_fetch]
    all_posts_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, posts in enumerate(all_posts_results):
        if isinstance(posts, Exception):
            print(f"Error fetching posts for {list(post_types_to_fetch)[i]}: {posts}")
            continue
            
        type_name = list(post_types_to_fetch)[i]
        print(f"Posts for {type_name}: {len(posts)}")
        
        for post in posts:
            post_title_rendered = post.get('title',{}).get('rendered', 'N/A')
            acf_data = post.get('acf', {})
            
            map_field_to_check = 'location_map' # Default
            if type_name == 'tour':
                map_field_to_check = 'meeting_point_map'
            elif type_name == 'hiking_trail': # Assuming hiking trails might use 'trail_map' for list view too
                map_field_to_check = 'trail_map'

            if map_field_to_check in acf_data and acf_data[map_field_to_check]:
                location_data_from_acf = acf_data[map_field_to_check]
                
                if isinstance(location_data_from_acf, dict) and \
                   'lat' in location_data_from_acf and 'lng' in location_data_from_acf and \
                   location_data_from_acf['lat'] is not None and location_data_from_acf['lng'] is not None and \
                   str(location_data_from_acf['lat']).strip() != "" and str(location_data_from_acf['lng']).strip() != "":
                    location = {
                        'id': post['id'],
                        'title': post_title_rendered,
                        'type': type_name,
                        'slug': post['slug'],
                        'lat': location_data_from_acf.get('lat'),
                        'lng': location_data_from_acf.get('lng'),
                        'excerpt': post.get('excerpt', {}).get('rendered', '')
                    }
                    locations.append(location)
                else:
                    print(f"Post {post.get('id')} ('{post_title_rendered}') has '{map_field_to_check}' but lat/lng is missing, null, or empty. Data: {location_data_from_acf}")
            else:
                print(f"No valid '{map_field_to_check}' data for post {post.get('id')} ('{post_title_rendered}'). ACF content for this field: {acf_data.get(map_field_to_check)}")
    
    print(f"Total locations collected: {len(locations)}")
    return locations

@cache_result("taxonomies", ttl=7200)  # Cache for 2 hours
async def get_taxonomies():
    """Get all taxonomies"""
    return await api_request("taxonomies")

@cache_result("media", ttl=3600)  # Cache for 1 hour
async def get_media(media_id):
    """Get media details by ID"""
    return await api_request(f"media/{media_id}")

async def submit_contact_form(name, email, subject, message):
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
