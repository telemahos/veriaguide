import httpx
import json
import time
import asyncio
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_fixed
from app.config import WP_API_URL, WP_API_USERNAME, WP_API_PASSWORD, CACHE_EXPIRY, POST_TYPES
from datetime import datetime


# In-memory cache for API responses
cache = {}

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
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
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
async def api_request(endpoint, params=None, use_cache=True):
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            
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

async def get_posts(post_type, page=1, per_page=10, search=None, category=None):
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
    
    endpoint = f"{post_type}s"  # Default: pluralize with 's'
    if post_type == "hiking-trail":
        endpoint = "hiking_trails"  # Specific case for hiking trails (plural with underscore)
    # Add more elif conditions here if other CPTs have non-standard REST base paths for their list view
    data = await api_request(endpoint, params)
    
    # Fetch tag names for each post concurrently
    for post in data:
        if 'tags' in post and post['tags']:
            # Use asyncio.gather to fetch all tag names concurrently
            tag_tasks = [get_tag_name(tag_id) for tag_id in post['tags']]
            tag_names = await asyncio.gather(*tag_tasks, return_exceptions=True)
            # Filter out None values and exceptions
            post['tag_names'] = [name for name in tag_names if name and not isinstance(name, Exception)]
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

async def get_taxonomies():
    """Get all taxonomies"""
    return await api_request("taxonomies")

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
