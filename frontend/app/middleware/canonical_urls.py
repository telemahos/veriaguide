"""Single-hop 301/410 for locale, legacy categories, guides, slash, and favicon."""
from starlette.responses import RedirectResponse, Response

from app.utils.canonical import canonicalize_path


class CanonicalUrlMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or "/"
        action = canonicalize_path(path)
        if action is None:
            await self.app(scope, receive, send)
            return

        query = scope.get("query_string") or b""
        if action.status_code == 410:
            response = Response(status_code=410, content="Gone")
        else:
            location = action.location or "/"
            if query and action.status_code == 301:
                location = f"{location}?{query.decode('latin-1')}"
            response = RedirectResponse(url=location, status_code=301)
        await response(scope, receive, send)
