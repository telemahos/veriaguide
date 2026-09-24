"""
Pagination Service - Optimized pagination for large datasets
"""
import math
from typing import Any

from app.config import ITEMS_PER_PAGE
from app.utils.logging_config import get_logger

logger = get_logger("pagination")


class PaginationService:
    """Service for handling optimized pagination"""
    
    @staticmethod
    def paginate_items(
        items: list[dict],
        page: int = 1,
        per_page: int | None = None
    ) -> dict[str, Any]:
        """
        Paginate items with metadata
        
        Args:
            items: List of items to paginate
            page: Page number (1-indexed)
            per_page: Items per page (defaults to ITEMS_PER_PAGE)
        
        Returns:
            Dict with paginated items and metadata
        """
        if per_page is None:
            per_page = ITEMS_PER_PAGE
        
        # Validate inputs
        page = max(1, int(page))
        per_page = max(1, min(int(per_page), 100))  # Max 100 items per page
        
        total_items = len(items)
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        
        # Validate page number
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        # Calculate slice indices
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get paginated items
        paginated_items = items[start_idx:end_idx]
        
        return {
            "items": paginated_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "start_item": start_idx + 1 if total_items > 0 else 0,
                "end_item": min(end_idx, total_items)
            }
        }
    
    @staticmethod
    def get_pagination_links(
        base_url: str,
        current_page: int,
        total_pages: int,
        query_params: dict[str, str] | None = None
    ) -> dict[str, str | None]:
        """
        Generate pagination links for templates
        
        Args:
            base_url: Base URL for pagination links
            current_page: Current page number
            total_pages: Total number of pages
            query_params: Additional query parameters
        
        Returns:
            Dict with first, prev, next, last links
        """
        query_string = ""
        if query_params:
            params = "&".join([f"{k}={v}" for k, v in query_params.items()])
            query_string = f"&{params}" if params else ""
        
        links = {
            "first": f"{base_url}?page=1{query_string}" if total_pages > 1 else None,
            "prev": f"{base_url}?page={current_page - 1}{query_string}" if current_page > 1 else None,
            "next": f"{base_url}?page={current_page + 1}{query_string}" if current_page < total_pages else None,
            "last": f"{base_url}?page={total_pages}{query_string}" if total_pages > 1 else None
        }
        
        return links
    
    @staticmethod
    def get_page_range(
        current_page: int,
        total_pages: int,
        window_size: int = 5
    ) -> list[int]:
        """
        Get range of page numbers to display in pagination UI
        
        Args:
            current_page: Current page number
            total_pages: Total number of pages
            window_size: Number of pages to show around current page
        
        Returns:
            List of page numbers to display
        """
        if total_pages <= window_size:
            return list(range(1, total_pages + 1))
        
        half_window = window_size // 2
        
        # Calculate start and end
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        # Adjust if near boundaries
        if start == 1:
            end = min(total_pages, window_size)
        elif end == total_pages:
            start = max(1, total_pages - window_size + 1)
        
        return list(range(start, end + 1))
    
    @staticmethod
    def optimize_query_for_pagination(
        items: list[dict],
        sort_by: str | None = None,
        sort_order: str = "asc"
    ) -> list[dict]:
        """
        Optimize items for pagination by sorting
        
        Args:
            items: List of items
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
        
        Returns:
            Sorted items
        """
        if not sort_by or sort_by not in items[0] if items else False:
            return items
        
        reverse = sort_order.lower() == "desc"
        
        try:
            return sorted(items, key=lambda x: x.get(sort_by, ""), reverse=reverse)
        except Exception as e:
            logger.warning(f"Error sorting items by {sort_by}: {e}")
            return items
    
    @staticmethod
    def get_pagination_stats(
        total_items: int,
        per_page: int
    ) -> dict[str, Any]:
        """
        Get pagination statistics
        
        Args:
            total_items: Total number of items
            per_page: Items per page
        
        Returns:
            Dict with pagination stats
        """
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        
        return {
            "total_items": total_items,
            "per_page": per_page,
            "total_pages": total_pages,
            "avg_items_per_page": per_page,
            "last_page_items": total_items % per_page if total_items % per_page != 0 else per_page
        }
