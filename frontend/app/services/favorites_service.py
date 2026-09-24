"""
Favorites Service - Handles favorites-related operations
"""
import asyncio
import re
from typing import Any

from fastapi import Request, Response

from app.api.wordpress import get_post_by_id
from app.services.content_service import ContentService
from app.utils.favorites import add_favorite, clear_favorites, get_favorites, remove_favorite


class FavoritesService:
    """Service class for handling favorites operations"""
    
    @staticmethod
    def get_user_favorites(request: Request) -> list:
        """Get user's favorites"""
        return get_favorites(request)

    @staticmethod
    async def enrich_favorites(favorites: list[dict]) -> list[dict]:
        """Attach slug, category path, coordinates and excerpt from WordPress."""
        if not favorites:
            return []

        async def enrich_one(fav: dict) -> dict:
            item = dict(fav)
            post_type = item.get("type", "")
            item["category_slug"] = ContentService.get_category_slug(post_type)

            post = None
            post_id = item.get("id")
            if post_id:
                try:
                    post = await get_post_by_id(post_type, int(post_id))
                except (TypeError, ValueError):
                    post = None

            if post:
                item["slug"] = post.get("slug", item.get("slug", ""))
                acf = post.get("acf") or {}
                location = acf.get("location_map") or {}
                item["lat"] = location.get("lat")
                item["lng"] = location.get("lng")
                raw_excerpt = post.get("excerpt", {}).get("rendered", "")
                item["excerpt"] = re.sub(r"<[^>]+>", "", raw_excerpt).strip()
            else:
                item.setdefault("slug", "")

            return item

        return list(await asyncio.gather(*[enrich_one(fav) for fav in favorites]))
    
    @staticmethod
    def add_to_favorites(
        request: Request,
        response: Response,
        item_id: str,
        item_type: str,
        item_title: str,
        item_image: str | None = None
    ) -> dict[str, Any]:
        """Add item to favorites"""
        favorites = add_favorite(request, response, item_id, item_type, item_title, item_image)
        return {"success": True, "favorites": favorites}
    
    @staticmethod
    def remove_from_favorites(request: Request, response: Response, item_id: str) -> dict[str, Any]:
        """Remove item from favorites"""
        favorites = remove_favorite(request, response, item_id)
        return {"success": True, "favorites": favorites}
    
    @staticmethod
    def clear_all_favorites(response: Response) -> dict[str, Any]:
        """Clear all favorites"""
        clear_favorites(response)
        return {"success": True, "favorites": []}