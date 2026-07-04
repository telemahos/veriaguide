"""301 redirects from legacy underscore category URLs to hyphenated public URLs."""
from fastapi import Request
from starlette.responses import RedirectResponse

from app.utils.category_urls import resolve_legacy_category_path


class LegacyCategoryUrlMiddleware:
  """Redirect /religious_sites/* to /religious-sites/* (and similar)."""

  def __init__(self, app):
      self.app = app

  async def __call__(self, scope, receive, send):
      if scope["type"] != "http":
          await self.app(scope, receive, send)
          return

      request = Request(scope, receive)
      new_path = resolve_legacy_category_path(request.url.path)
      if new_path:
          query = request.url.query
          location = new_path + (f"?{query}" if query else "")
          response = RedirectResponse(url=location, status_code=301)
          await response(scope, receive, send)
          return

      await self.app(scope, receive, send)
