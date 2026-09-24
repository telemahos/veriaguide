import asyncio
import time
from urllib.parse import urlparse

from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import CACHE_EXPIRY, POST_TYPES, WP_API_PASSWORD, WP_API_URL, WP_API_USERNAME
from app.services.cache_service import CacheService, cache_result
from app.services.http_service import HTTPService
from app.utils.helpers import get_featured_image

# Legacy in-memory cache for fallback (will be replaced by Redis)
cache = {}
_auth_token_cache = {"token": None, "expires": 0}

@cache_result("tag_name", ttl=7200)  # Cache for 2 hours
async def get_tag_name(tag_id):
    """Get tag name by ID"""
    try:
        tag_data = await api_request(f"tags/{tag_id}")
        return tag_data.get('name')
    except Exception:
        return None

async def get_auth_token():
    """Get authentication token from WordPress REST API (cached 1 hour)"""
    if _auth_token_cache["token"] and time.time() < _auth_token_cache["expires"]:
        return _auth_token_cache["token"]

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
        token = response.json().get("token")
        if token:
            _auth_token_cache["token"] = token
            _auth_token_cache["expires"] = time.time() + 3600
        return token
    return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def api_request(endpoint, params=None, use_cache=True):
    """Make a request to the WordPress REST API with Redis caching and authentication"""
    base_url = WP_API_URL.rstrip("/")
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
            import os
            if os.getenv("ENVIRONMENT") == "production":
                return []
            # Development sample data for museums/attractions only
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
        import os
        if os.getenv("ENVIRONMENT") == "production":
            return []
        # Development fallback only
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
        keys_to_remove = [k for k in cache if endpoint in k]
        for key in keys_to_remove:
            del cache[key]
    else:
        # Clear entire cache
        await CacheService.clear_all()
        cache = {}

async def get_posts(post_type, page=1, per_page=10, search=None, category=None, meta_key=None, meta_value=None):
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

    if meta_key and meta_value is not None:
        params["meta_key"] = meta_key
        params["meta_value"] = meta_value
    
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

async def get_all_posts_for_type(post_type, search=None, category=None):
    """
    Get all posts of a specific type by fetching all pages from the WordPress API.
    This is useful when client-side filtering is required on the full dataset.
    """
    cache_key = f"all_posts_{post_type}"
    cache_params = {"search": search, "category": category}
    cached = await CacheService.get(cache_key, cache_params)
    if cached is not None:
        print(f"Redis cache hit for all posts: {post_type}")
        return cached

    all_posts = []
    page = 1
    per_page = 100  # Fetch 100 items per page (maximum allowed by WordPress)

    while True:
        print(f"Fetching page {page} for post type {post_type}...")
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

        # We set use_cache=False because we are paginating and don't want
        # to cache partial results. Caching should be done on the final aggregated result.
        data = await api_request(endpoint, params, use_cache=False)

        if not data:
            print(f"No more data found for {post_type}. Exiting loop.")
            break

        all_posts.extend(data)

        # If the number of returned items is less than per_page, we've reached the last page
        if len(data) < per_page:
            print(f"Last page reached for {post_type}. Total posts fetched: {len(all_posts)}")
            break
        
        page += 1

    # Process posts to extract tag names from embedded data
    for post in all_posts:
        post['tag_names'] = []
        if '_embedded' in post and 'wp:term' in post['_embedded']:
            terms = post['_embedded']['wp:term']
            for taxonomy in terms:
                for term in taxonomy:
                    if term.get('taxonomy') == 'post_tag':
                        post['tag_names'].append(term['name'])
    
    print(f"Finished fetching all posts for {post_type}. Total: {len(all_posts)}")
    await CacheService.set(cache_key, all_posts, CACHE_EXPIRY, cache_params)
    return all_posts

def _wp_rest_collection(post_type: str) -> str:
    """Map internal post_type slug to WordPress REST collection name."""
    mapping = {
        "museum": "museums",
        "archaeological_site": "archaeological_sites",
        "religious_site": "religious_sites",
        "restaurant": "restaurants",
        "cafe": "cafes",
        "accommodation": "accommodations",
        "ski_resort": "ski_resorts",
        "hiking_trail": "hiking_trails",
        "tour": "tours",
        "hidden_gem": "hidden_gems",
    }
    return mapping.get(post_type, f"{post_type}s")


async def get_post_by_id(post_type: str, post_id: int):
    """Get a single post by WordPress ID."""
    collection = _wp_rest_collection(post_type)
    try:
        data = await api_request(f"{collection}/{post_id}", {"_embed": "true"})
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"Error fetching post {post_id} ({post_type}): {e}")
        return None


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

            # Guard against cases where ACF returns an empty list instead of a dict
            if not isinstance(acf_data, dict):
                continue
            
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
                        'excerpt': post.get('excerpt', {}).get('rendered', ''),
                        'featured_image': get_featured_image(post),
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
    """Send a contact message through the veriaguide/v1/contact WordPress endpoint (wp_mail)."""
    from app.utils.logging_config import get_logger

    logger = get_logger("contact_form")

    if not all([name.strip(), email.strip(), subject.strip(), message.strip()]):
        return {"success": False, "message": "All fields are required. Please fill out the complete form."}

    if not (WP_API_USERNAME and WP_API_PASSWORD):
        logger.error("Contact form: WP_API_USERNAME/WP_API_PASSWORD not configured")
        return {"success": False, "message": "The contact form is temporarily unavailable. Please email us directly."}

    url = f"{WP_API_URL.split('/wp-json')[0]}/wp-json/veriaguide/v1/contact"
    # Credentials must not travel over plain HTTP, and WordPress redirects HTTP POSTs to HTTPS as GETs.
    if url.startswith("http://") and urlparse(url).hostname not in ("localhost", "127.0.0.1"):
        url = "https://" + url[len("http://"):]
    try:
        response = await HTTPService.post(
            url,
            json={"name": name, "email": email, "subject": subject, "message": message},
            auth=(WP_API_USERNAME, WP_API_PASSWORD),
            use_wp_client=True,
        )
    except Exception as e:
        logger.error(f"Contact form request failed: {e}")
        response = None

    if response is not None and response.status_code == 200:
        logger.info("Contact form message sent")
        return {"success": True, "message": "Thank you for your message! We'll get back to you within 24 hours."}

    status = response.status_code if response is not None else "no response"
    logger.error(f"Contact form delivery failed: {status}")
    return {
        "success": False,
        "message": "Sorry, there was a temporary issue sending your message. Please try again.",
    }


@cache_result("navigation_menu", ttl=1800)  # Cache for 30 minutes
async def get_navigation_menu(location="primary"):
    """Get navigation menu from WordPress"""
    wp_base = WP_API_URL.split("/wp-json")[0]
    base_url = f"{wp_base}/wp-json/veriaguide/v1"
    url = f"{base_url}/menus"
    
    try:
        response = await HTTPService.get(url, use_wp_client=True)
        
        if response.status_code == 200:
            menus = response.json()
            for menu in menus:
                if menu.get('location') == location:
                    return menu
            for menu in menus:
                if location.lower() in menu.get('name', '').lower() or \
                   location.lower() in menu.get('slug', '').lower():
                    return menu
            return menus[0] if menus else None
        return None
    except Exception as e:
        print(f"Error fetching navigation menu: {e}")
        return None
