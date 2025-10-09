import json
from fastapi import Request, Response

def get_favorites(request: Request):
    """Get favorites from cookie"""
    favorites_cookie = request.cookies.get("veriaguide_favorites")
    if not favorites_cookie:
        return []
    
    try:
        return json.loads(favorites_cookie)
    except:
        return []

def add_favorite(request: Request, response: Response, item_id: str, item_type: str, item_title: str, item_image: str = None):
    """Add an item to favorites"""
    # Get existing favorites from request
    favorites = get_favorites(request)
    
    # Check if already in favorites
    if not any(item["id"] == item_id for item in favorites):
        favorites.append({
            "id": item_id,
            "type": item_type,
            "title": item_title,
            "image": item_image
        })
    
    # Set cookie with updated favorites
    response.set_cookie(
        key="veriaguide_favorites",
        value=json.dumps(favorites),
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=False  # Changed to False so JavaScript can access it
    )
    
    return favorites

def remove_favorite(request: Request, response: Response, item_id: str):
    """Remove an item from favorites"""
    # Get existing favorites from request
    favorites = get_favorites(request)
    
    # Remove item if exists
    favorites = [item for item in favorites if item["id"] != item_id]
    
    # Set cookie with updated favorites
    response.set_cookie(
        key="veriaguide_favorites",
        value=json.dumps(favorites),
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=False  # Changed to False so JavaScript can access it
    )
    
    return favorites

def clear_favorites(response: Response):
    """Clear all favorites"""
    response.delete_cookie(key="veriaguide_favorites")
    return [] 