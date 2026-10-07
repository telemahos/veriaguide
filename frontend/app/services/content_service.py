"""
Content Service - Handles all content-related business logic
"""
import asyncio
import json
from collections import Counter
from typing import Any

from app.api.wordpress import get_all_locations, get_all_posts_for_type, get_post, get_posts
from app.config import ITEMS_PER_PAGE, POST_TYPES
from app.i18n import tr
from app.services.homepage_service import HOMEPAGE_SECTION_CATEGORIES
from app.services.pagination_service import PaginationService
from app.utils.category_urls import get_category_url_path
from app.utils.helpers import get_category_placeholder_url, get_featured_image, haversine_distance_km, listing_has_photo, listing_map_point, strip_tags, usable_listing_slug
from app.utils.logging_config import get_logger

logger = get_logger("content")

POST_TYPE_LABELS = {
    "museum": "Museum",
    "archaeological_site": "Archaeological Site",
    "religious_site": "Religious Site",
    "restaurant": "Restaurant",
    "cafe": "Café",
    "accommodation": "Accommodation",
    "ski_resort": "Ski Resort",
    "hiking_trail": "Hiking Trail",
    "hidden_gem": "Hidden Gem",
    "tour": "Tour",
}

MAP_FIELD_NAMES = ("location_map", "meeting_point_map", "trail_map")


class ContentService:
    """Service class for handling content operations"""
    
    @staticmethod
    async def get_featured_items(homepage_sections=None) -> dict[str, list[dict]]:
        """Get featured homepage items that have photos; prefer is_featured, else random with photos.
        
        Args:
            homepage_sections: Optional list of section configs from WordPress.
                Each dict has: category, post_type, title, enabled, items_count, order, view_all_link
                When provided, only fetches enabled categories with specified item counts.
        """
        tasks = []
        categories = []
        items_counts = {}
        
        if homepage_sections:
            # Use WordPress-configured sections (already filtered to enabled, sorted by order)
            for section in homepage_sections:
                category = section.get('category')
                post_type = section.get('post_type')
                if category and post_type:
                    tasks.append(get_all_posts_for_type(post_type))
                    categories.append(category)
                    items_counts[category] = section.get('items_count', 4)
        else:
            # Fallback: fetch homepage heritage categories only
            for category in HOMEPAGE_SECTION_CATEGORIES:
                post_type = POST_TYPES.get(category)
                if not post_type:
                    continue
                tasks.append(get_all_posts_for_type(post_type))
                categories.append(category)
                items_counts[category] = 4
        
        all_items_by_category = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Use OrderedDict to preserve section order
        from collections import OrderedDict
        featured_items = OrderedDict()
        import random

        for i, category_items in enumerate(all_items_by_category):
            category_name = categories[i]
            max_items = items_counts.get(category_name, 4)
            
            if isinstance(category_items, Exception) or not category_items:
                print(f"Error or no items for {category_name}: {category_items}")
                featured_items[category_name] = []
                continue

            # Homepage cards must have a real photo (featured image or gallery).
            with_photos = [item for item in category_items if listing_has_photo(item)]
            if not with_photos:
                featured_items[category_name] = []
                continue

            truly_featured = []
            for item in with_photos:
                acf = item.get('acf', {})
                if not isinstance(acf, dict):
                    continue
                is_featured_val = acf.get('is_featured')
                if isinstance(is_featured_val, list) and "Is Featured" in is_featured_val:
                    truly_featured.append(item)

            # Prefer featured+photo items; fill remaining slots from other photo listings.
            if truly_featured:
                selected = list(truly_featured[:max_items])
                if len(selected) < max_items:
                    selected_ids = {id(x) for x in selected}
                    remainder = [item for item in with_photos if id(item) not in selected_ids]
                    random.shuffle(remainder)
                    selected.extend(remainder[: max_items - len(selected)])
                featured_items[category_name] = selected
            else:
                random.shuffle(with_photos)
                featured_items[category_name] = with_photos[:max_items]
        
        return featured_items
    
    @staticmethod
    async def get_category_items(
        post_type: str,
        page: int = 1,
        search: str | None = None,
        denomination: list[str] | None = None,
        guest_rating: str = 'any',
        city: str | None = None,
        property_type: str | None = None,
        price_range: str | None = None,
        amenities: list[str] | None = None,
        religious_affiliation: str | None = None,
        site_type: str | None = None
    ) -> dict[str, Any]:
        """Get items for a specific category with filtering and pagination"""
        
        # Fetch all items for filtering and statistics
        all_items = await get_all_posts_for_type(post_type, search=search)
        
        # Compute tag counts for sidebar
        tag_counts = Counter()
        for item in all_items:
            for tag in item.get('tag_names', []):
                tag_counts[tag] += 1
        
        # Compute visitor rating counts for sidebar
        rating_counts = {
            'any': len(all_items),
            '4.5': 0,
            '4': 0,
            '3.5': 0
        }
        
        for item in all_items:
            try:
                if not isinstance(item, dict):
                    continue
                acf_fields = item.get('acf', {})

                # Guard against cases where ACF returns an empty list instead of a dict
                if not isinstance(acf_fields, dict):
                    acf_fields = {}

                rating_value = acf_fields.get('ratings') or acf_fields.get('rating') or 0
                rating = float(rating_value)
            except (TypeError, ValueError):
                rating = 0
            
            if rating >= 3.5:
                rating_counts['3.5'] += 1
            if rating >= 4:
                rating_counts['4'] += 1
            if rating >= 4.5:
                rating_counts['4.5'] += 1
        
        # Compute accommodation-specific filter aggregations
        filter_aggregations = ContentService._compute_filter_aggregations(all_items, post_type)
        
        # Apply filters
        filtered_items = ContentService._apply_filters(
            all_items, guest_rating, denomination, city, property_type, price_range, amenities, religious_affiliation, site_type
        )

        # Photos first (stable) after filters (site_type/city/etc.), then no-photo,
        # then paginate. Same photo bar as homepage / listing cards (placeholders last).
        ContentService.sort_listings_photos_first(filtered_items)
        
        # Paginate results
        pagination_data = ContentService._paginate_items(filtered_items, page)
        
        # Prepare location data for map
        locations_for_map = ContentService._prepare_location_data(filtered_items)
        
        return {
            'items': pagination_data['items'],
            'total_count': pagination_data['total_count'],
            'total_pages': pagination_data['total_pages'],
            'has_next': pagination_data['has_next'],
            'has_prev': pagination_data['has_prev'],
            'tag_counts': dict(tag_counts),
            'rating_counts': rating_counts,
            'locations': locations_for_map,
            'filter_aggregations': filter_aggregations
        }
    
    @staticmethod
    def _compute_filter_aggregations(items: list[dict], post_type: str) -> dict[str, Any]:
        """Compute filter aggregations for sidebar filters"""
        aggregations = {
            'cities': Counter(),
            'property_types': Counter(),
            'price_ranges': Counter(),
            'amenities': Counter(),
            'religious_affiliations': Counter(),
            'tags': Counter(),
            'site_types': Counter()  # For religious site types (dynamically detected)
        }
        
        # Tags that indicate site types for religious sites (exclude generic tags)
        generic_tags = {'Christianity', 'Religious Site', 'Veria', 'Vergina', 'Historical'}
        
        for item in items:
            if not isinstance(item, dict):
                continue
            acf_fields = item.get('acf', {})
            if not isinstance(acf_fields, dict):
                continue
            
            # City aggregation
            city = acf_fields.get('city')
            if city:
                aggregations['cities'][city] += 1
            
            # Property type / category aggregation
            category = acf_fields.get('category')
            if category:
                aggregations['property_types'][category] += 1
            
            # Price range aggregation
            price_range = acf_fields.get('price_range')
            if price_range and price_range not in [False, None, '']:
                aggregations['price_ranges'][price_range] += 1
            
            # Amenities aggregation
            amenities_list = acf_fields.get('amenities', [])
            if isinstance(amenities_list, list):
                for amenity in amenities_list:
                    if amenity:
                        aggregations['amenities'][amenity] += 1
            
            # Religious affiliation aggregation (from ACF field)
            affiliation = acf_fields.get('religious_affiliation')
            if affiliation and affiliation not in [False, None, '']:
                aggregations['religious_affiliations'][affiliation] += 1
            
            # Tags aggregation (from WordPress tags)
            tag_names = item.get('tag_names', [])
            for tag in tag_names:
                if tag:
                    aggregations['tags'][tag] += 1
                    # Site types are tags that are NOT generic (like Christianity, Religious Site, etc.)
                    if tag not in generic_tags:
                        aggregations['site_types'][tag] += 1
        
        # Sort property types in logical order (by star rating, then alphabetically)
        def property_type_sort_key(item):
            name = item[0].lower()
            if '4-star' in name:
                return (0, name)
            elif '3-star' in name:
                return (1, name)
            elif '2-star' in name:
                return (2, name)
            elif 'guest house' in name:
                return (3, name)
            elif 'hotel' in name:
                return (4, name)
            else:
                return (5, name)
        
        sorted_property_types = dict(sorted(
            aggregations['property_types'].items(),
            key=property_type_sort_key
        ))
        
        # Sort price ranges in logical order
        price_order = {'Budget': 0, 'Mid-Range': 1, 'Luxury': 2}
        sorted_price_ranges = dict(sorted(
            aggregations['price_ranges'].items(),
            key=lambda x: price_order.get(x[0], 99)
        ))
        
        return {
            'cities': dict(aggregations['cities'].most_common()),
            'property_types': sorted_property_types,
            'price_ranges': sorted_price_ranges,
            'amenities': dict(aggregations['amenities'].most_common()),
            'religious_affiliations': dict(aggregations['religious_affiliations'].most_common()),
            'tags': dict(aggregations['tags'].most_common()),
            'site_types': dict(aggregations['site_types'].most_common())
        }
    
    @staticmethod
    def _apply_filters(
        items: list[dict],
        guest_rating: str,
        denomination: list[str] | None,
        city: str | None = None,
        property_type: str | None = None,
        price_range: str | None = None,
        amenities: list[str] | None = None,
        religious_affiliation: str | None = None,
        site_type: str | None = None
    ) -> list[dict]:
        """Apply rating and denomination filters to items"""
        filtered_items = items
        
        # Filter by rating
        if guest_rating and guest_rating != 'any':
            try:
                rating_threshold = float(guest_rating)
                
                def rating_filter(item):
                    if not isinstance(item, dict):
                        return False
                    acf_fields = item.get('acf', {})
                    if not isinstance(acf_fields, dict):
                        acf_fields = {}
                    rating_value = acf_fields.get('ratings') or acf_fields.get('rating') or 0
                    try:
                        return float(rating_value) >= rating_threshold
                    except (ValueError, TypeError):
                        return False

                filtered_items = [item for item in filtered_items if rating_filter(item)]
            except ValueError:
                pass
        
        # Filter by denomination/tags
        if denomination:
            # Filter out empty strings that might come from "All" options in forms
            denominations_to_filter = [d for d in denomination if d]
            if denominations_to_filter:
                filtered_items = [
                    item for item in filtered_items
                    if any(tag in item.get('tag_names', []) for tag in denominations_to_filter)
                ]
        
        # Filter by city
        if city and city != 'all':
            filtered_items = [
                item for item in filtered_items
                if isinstance(item.get('acf', {}), dict) and 
                   item.get('acf', {}).get('city') == city
            ]
        
        # Filter by property type (category)
        if property_type and property_type != 'all':
            filtered_items = [
                item for item in filtered_items
                if isinstance(item.get('acf', {}), dict) and 
                   item.get('acf', {}).get('category') == property_type
            ]
        
        # Filter by price range
        if price_range and price_range != 'all':
            filtered_items = [
                item for item in filtered_items
                if isinstance(item.get('acf', {}), dict) and 
                   item.get('acf', {}).get('price_range') == price_range
            ]
        
        # Filter by amenities
        if amenities:
            amenities_to_filter = [a for a in amenities if a]
            if amenities_to_filter:
                filtered_items = [
                    item for item in filtered_items
                    if isinstance(item.get('acf', {}), dict) and 
                       isinstance(item.get('acf', {}).get('amenities', []), list) and
                       any(amenity in item.get('acf', {}).get('amenities', []) for amenity in amenities_to_filter)
                ]
        
        # Filter by religious affiliation
        if religious_affiliation and religious_affiliation != 'all':
            filtered_items = [
                item for item in filtered_items
                if isinstance(item.get('acf', {}), dict) and 
                   item.get('acf', {}).get('religious_affiliation') == religious_affiliation
            ]
        
        # Filter by site type (WordPress tag for religious sites)
        if site_type and site_type != 'all':
            filtered_items = [
                item for item in filtered_items
                if site_type in item.get('tag_names', [])
            ]
        
        return filtered_items

    @staticmethod
    def sort_listings_photos_first(items: list[dict]) -> list[dict]:
        """Stable-sort in place: real-photo cards first, placeholder cards last.

        Used for every category grid *after* filters (Monastery, city, …) so a
        filtered view cannot keep WordPress' default order when that order
        starts with photo-less posts (e.g. newest monasteries).
        """
        items.sort(key=lambda item: not listing_has_photo(item))
        return items
    
    @staticmethod
    def _paginate_items(items: list[dict], page: int) -> dict[str, Any]:
        """Paginate items and return pagination data"""
        result = PaginationService.paginate_items(items, page, ITEMS_PER_PAGE)
        
        return {
            'items': result['items'],
            'total_count': result['pagination']['total_items'],
            'total_pages': result['pagination']['total_pages'],
            'has_next': result['pagination']['has_next'],
            'has_prev': result['pagination']['has_prev']
        }
    
    @staticmethod
    def _prepare_location_data(items: list[dict]) -> list[dict]:
        """Prepare location data for map display"""
        locations = []
        for item in items:
            acf_fields = item.get("acf", {})
            if not isinstance(acf_fields, dict):
                acf_fields = {}

            slug = usable_listing_slug(item.get("slug"))
            if not slug:
                continue
            location_map = listing_map_point(item)
            if location_map:
                locations.append({
                    "id": item.get("id"),
                    "title": item.get("title", {}).get("rendered", ""),
                    "slug": slug,
                    "lat": location_map.get("lat"),
                    "lng": location_map.get("lng"),
                    "featured_image": get_featured_image(item),
                    "excerpt": strip_tags(item.get("excerpt", {}).get("rendered", ""))
                })
        return locations
    
    @staticmethod
    async def get_item_detail(post_type: str, slug: str) -> dict[str, Any] | None:
        """Get detailed information for a single item"""
        item = await get_post(post_type, slug)
        
        if not item:
            return None
        
        # Ensure acf_fields is a dictionary, not a list
        raw_acf = item.get("acf")
        acf_fields = raw_acf if isinstance(raw_acf, dict) else {}

        return {
            'item': item,
            'title': item.get("title", {}).get("rendered", ""),
            'description': strip_tags(item.get("excerpt", {}).get("rendered", "")),
            'content': item.get("content", {}).get("rendered", ""),
            'featured_image': get_featured_image(item),
            'acf_fields': acf_fields
        }

    @staticmethod
    def get_category_slug(post_type: str) -> str:
        for category, pt in POST_TYPES.items():
            if pt == post_type:
                return get_category_url_path(category)
        return post_type.replace("_", "-") + "s"

    @staticmethod
    async def get_related_items(post_type: str, current_slug: str, limit: int = 4) -> list:
        """Return other items from the same post type for sidebar recommendations."""
        all_items = await get_all_posts_for_type(post_type)
        related = []
        for item in all_items:
            if item.get("slug") == current_slug:
                continue
            related.append(item)
            if len(related) >= limit:
                break
        return related

    @staticmethod
    async def get_nearby_items(
        location_data: dict[str, Any],
        current_slug: str,
        current_id: int | None = None,
        limit: int = 4,
        max_distance_km: float = 12.0,
    ) -> list:
        """Return the closest listings across all categories within a radius."""
        try:
            origin_lat = float(location_data["lat"])
            origin_lng = float(location_data["lng"])
        except (KeyError, TypeError, ValueError):
            return []

        locations = await get_all_locations()
        nearby = []

        for loc in locations:
            if loc.get("slug") == current_slug:
                continue
            if current_id is not None and loc.get("id") == current_id:
                continue
            try:
                distance_km = haversine_distance_km(
                    origin_lat,
                    origin_lng,
                    float(loc["lat"]),
                    float(loc["lng"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

            if distance_km > max_distance_km:
                continue

            post_type = loc.get("type", "")
            nearby.append({
                "id": loc.get("id"),
                "title": strip_tags(loc.get("title", "")),
                "slug": loc.get("slug"),
                "type": post_type,
                "category": ContentService.get_category_slug(post_type),
                "type_label": tr(POST_TYPE_LABELS.get(
                    post_type, post_type.replace("_", " ").title()
                )),
                "distance_km": round(distance_km, 1),
                "featured_image": loc.get("featured_image") or get_category_placeholder_url(loc.get("type", "default")),
            })

        nearby.sort(key=lambda item: item["distance_km"])
        return nearby[:limit]
    
    @staticmethod
    def get_location_data_for_item(item: dict, category_name: str) -> dict | None:
        """Extract location data for a specific item based on category"""
        acf_fields = item.get("acf", {})
        if not isinstance(acf_fields, dict):
            acf_fields = {}
        
        # Determine the primary map field based on category
        primary_map_field_name = "location_map"  # Default
        if category_name == "tours":
            primary_map_field_name = "meeting_point_map"
        elif category_name == "hiking_trails":
            primary_map_field_name = "trail_map"
        
        # Try to get map data from various fields
        map_data_to_use = None
        if primary_map_field_name and primary_map_field_name in acf_fields:
            map_data_to_use = acf_fields[primary_map_field_name]
        elif "location_map" in acf_fields:
            map_data_to_use = acf_fields["location_map"]
        elif "location" in acf_fields:
            map_data_to_use = acf_fields["location"]
        
        # Validate and return location data
        if (map_data_to_use and isinstance(map_data_to_use, dict) and
            "lat" in map_data_to_use and "lng" in map_data_to_use):
            return {
                "lat": map_data_to_use.get("lat"),
                "lng": map_data_to_use.get("lng"),
                "address": map_data_to_use.get("address"),
                "zoom": map_data_to_use.get("zoom")
            }
        
        return None
    
    @staticmethod
    async def search_content(
        query: str,
        content_type: str | None = None,
        page: int = 1,
        per_page: int = 10
    ) -> dict:
        """Search across content types with pagination"""
        results = []
        total_results = 0
        
        if content_type and str(content_type).strip().casefold() in {"all", ""}:
            content_type = None
        if content_type and content_type in POST_TYPES:
            # Search in specific type (local match includes title_el / content_el)
            post_type = POST_TYPES[content_type]
            matched = await get_all_posts_for_type(post_type, search=query)
            total_results = len(matched)
            start_idx = (page - 1) * per_page
            results = matched[start_idx:start_idx + per_page]
        else:
            # Search in all post types concurrently
            tasks = [
                get_all_posts_for_type(post_type, search=query)
                for post_type in POST_TYPES.values()
            ]
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in search_results:
                if not isinstance(result, Exception):
                    results.extend(result)
                else:
                    print(f"Error in search: {result}")
            
            total_results = len(results)
            
            # Apply pagination manually for all-category search
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            results = results[start_idx:end_idx]
        
        # Calculate pagination info
        has_prev = page > 1
        has_next = len(results) == per_page
        
        return {
            'results': results,
            'total': total_results,
            'page': page,
            'has_prev': has_prev,
            'has_next': has_next,
            'per_page': per_page
        }
    
    @staticmethod
    async def get_map_locations(content_type: str | None = None) -> str:
        """Get all locations for map display as JSON string"""
        locations = await get_all_locations(content_type)
        return json.dumps(locations)