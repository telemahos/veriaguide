"""301 trailing-slash URLs to the canonical non-slash form.

Locale homepages (/el/, /de/) keep a trailing slash to match localized_path('/').
Listing hubs and detail pages use no trailing slash in canonical tags.
"""
from starlette.responses import RedirectResponse

# Canonical homepage URLs that keep a trailing slash.
_KEEP_TRAILING_SLASH = frozenset({"/", "/el/", "/de/"})


class TrailingSlashRedirectMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or "/"
        if path.endswith("/") and path not in _KEEP_TRAILING_SLASH:
            location = path.rstrip("/") or "/"
            query = scope.get("query_string") or b""
            if query:
                location = f"{location}?{query.decode('latin-1')}"
            response = RedirectResponse(url=location, status_code=301)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
