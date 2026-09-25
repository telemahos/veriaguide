"""301 redirects from legacy underscore category URLs to hyphenated public URLs."""
from fastapi import Request
from starlette.responses import RedirectResponse

from app.i18n import current_lang, localized_path
from app.utils.category_urls import resolve_legacy_category_path

CATEGORY_MAP_REDIRECTS = {
    "/restaurants/map": "restaurant",
    "/cafes/map": "cafe",
    "/museums/map": "museum",
    "/archaeological-sites/map": "archaeological_site",
    "/ski-resorts/map": "ski_resort",
    "/accommodations/map": "accommodation",
}


class LegacyCategoryUrlMiddleware:
  """Redirect /religious_sites/* to /religious-sites/* (and similar)."""

  def __init__(self, app):
      self.app = app

  async def __call__(self, scope, receive, send):
      if scope["type"] != "http":
          await self.app(scope, receive, send)
          return

      request = Request(scope, receive)
      map_type = CATEGORY_MAP_REDIRECTS.get(request.url.path.rstrip("/"))
      if map_type:
          target = localized_path("/map", current_lang()) + f"?type={map_type}"
          await RedirectResponse(url=target, status_code=301)(scope, receive, send)
          return

      new_path = resolve_legacy_category_path(request.url.path)
      if new_path:
          if current_lang() == "el":
              new_path = localized_path(new_path, "el")
          query = request.url.query
          location = new_path + (f"?{query}" if query else "")
          response = RedirectResponse(url=location, status_code=301)
          await response(scope, receive, send)
          return

      await self.app(scope, receive, send)
