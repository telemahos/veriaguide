"""
Content Service - Handles all content-related business logic
"""
import asyncio
import json
from typing import Optional, List, Dict, Any
from collections import Counter
import math

from app.config import ITEMS_PER_PAGE, POST_TYPES
from app.api.wordpress import get_posts, get_post, get_all_locations
from app.utils.helpers import get_featured_image, strip_tags


class ContentService:
    """Service class for handling content operations"""
    
    @staticmethod
    async def get_featured_items() -> Dict[str, List[Dict]]:
        """Get featured items from all categories concurrently"""
        tasks = []
        categories = []
        
        for category, post_type in POST_TYPES.items():
            tasks.append(get_posts(post_type, per_page=4))
            categories.append(category)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results back to categories
        featured_items = {}
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                featured_items[categories[i]] = result
            else:
                print(f"Error fetching {categories[i]}: {result}")
                featured_items[categories[i]] = []
        
        return featured_items
    
    @staticmethod
    async def get_category_items(
        post_type: str,
        page: int = 1,
        search: Optional[str] = None,
        denomination: Optional[List[str]] = None,
        guest_rating: str = 'any'
    ) -> Dict[str, Any]:
        """Get items for a specific category with filtering and pagination"""
        
        # Fetch all items for filtering and statistics
        all_items = await get_posts(post_type, per_page=100, search=search)
        
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
                rating = float(item.get('acf', {}).get('ratings', 0) or 0)
            except (TypeError, ValueError):
                continue
            
            if rating >= 3.5:
                rating_counts['3.5'] += 1
            if rating >= 4:
                rating_counts['4'] += 1
            if rating >= 4.5:
                rating_counts['4.5'] += 1
        
        # Apply filters
        filtered_items = ContentService._apply_filters(
            all_items, guest_rating, denomination
        )
        
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
            'locations': locations_for_map
        }
    
    @staticmethod
    def _apply_filters(
        items: List[Dict],
        guest_rating: str,
        denomination: Optional[List[str]]
    ) -> List[Dict]:
        """Apply rating and denomination filters to items"""
        filtered_items = items
        
        # Filter by rating
        if guest_rating and guest_rating != 'any':
            try:
                rating_threshold = float(guest_rating)
                filtered_items = [
                    item for item in filtered_items
                    if float(item.get('acf', {}).get('ratings', 0) or 0) >= rating_threshold
                ]
            except ValueError:
                pass
        
        # Filter by denomination/tags
        if denomination:
            filtered_items = [
                item for item in filtered_items
                if any(tag in item.get('tag_names', []) for tag in denomination)
            ]
        
        return filtered_items
    
    @staticmethod
    def _paginate_items(items: List[Dict], page: int) -> Dict[str, Any]:
        """Paginate items and return pagination data"""
        total_count = len(items)
        total_pages = math.ceil(total_count / ITEMS_PER_PAGE) if total_count and ITEMS_PER_PAGE else 1
        
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        paginated_items = items[start_idx:end_idx]
        
        return {
            'items': paginated_items,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    
    @staticmethod
    def _prepare_location_data(items: List[Dict]) -> List[Dict]:
        """Prepare location data for map display"""
        return [
            {
                "id": item.get("id"),
                "title": item.get("title", {}).get("rendered", ""),
                "slug": item.get("slug"),
                "acf": item.get("acf", {}),
                "featured_image": get_featured_image(item),
                "excerpt": strip_tags(item.get("excerpt", {}).get("rendered", ""))
            }
            for item in items if item.get("acf", {}).get("location_map")
        ]
    
    @staticmethod
    async def get_item_detail(post_type: str, slug: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a single item"""
        item = await get_post(post_type, slug)
        
        if not item:
            return None
        
        return {
            'item': item,
            'title': item.get("title", {}).get("rendered", ""),
            'description': strip_tags(item.get("excerpt", {}).get("rendered", "")),
            'content': item.get("content", {}).get("rendered", ""),
            'featured_image': get_featured_image(item),
            'acf_fields': item.get("acf", {})
        }
    
    @staticmethod
    def get_location_data_for_item(item: Dict, category_name: str) -> Optional[Dict]:
        """Extract location data for a specific item based on category"""
        acf_fields = item.get("acf", {})
        
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
        content_type: Optional[str] = None,
        page: int = 1
    ) -> List[Dict]:
        """Search across content types"""
        results = []
        
        if content_type and content_type in POST_TYPES:
            # Search in specific type
            post_type = POST_TYPES[content_type]
            results = await get_posts(post_type, search=query, page=page, per_page=ITEMS_PER_PAGE)
        else:
            # Search in all post types concurrently
            tasks = [get_posts(post_type, search=query, per_page=10) for post_type in POST_TYPES.values()]
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in search_results:
                if not isinstance(result, Exception):
                    results.extend(result)
                else:
                    print(f"Error in search: {result}")
        
        return results
    
    @staticmethod
    async def get_map_locations(content_type: Optional[str] = None) -> str:
        """Get all locations for map display as JSON string"""
        locations = await get_all_locations(content_type)
        return json.dumps(locations)