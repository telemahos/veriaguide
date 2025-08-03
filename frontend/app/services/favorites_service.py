"""
Favorites Service - Handles favorites-related operations
"""
from typing import Dict, Any, Optional
from fastapi import Request, Response
from app.utils.favorites import get_favorites, add_favorite, remove_favorite, clear_favorites


class FavoritesService:
    """Service class for handling favorites operations"""
    
    @staticmethod
    def get_user_favorites(request: Request) -> list:
        """Get user's favorites"""
        return get_favorites(request)
    
    @staticmethod
    def add_to_favorites(
        response: Response,
        item_id: str,
        item_type: str,
        item_title: str,
        item_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add item to favorites"""
        favorites = add_favorite(response, item_id, item_type, item_title, item_image)
        return {"success": True, "favorites": favorites}
    
    @staticmethod
    def remove_from_favorites(response: Response, item_id: str) -> Dict[str, Any]:
        """Remove item from favorites"""
        favorites = remove_favorite(response, item_id)
        return {"success": True, "favorites": favorites}
    
    @staticmethod
    def clear_all_favorites(response: Response) -> Dict[str, Any]:
        """Clear all favorites"""
        clear_favorites(response)
        return {"success": True, "favorites": []}