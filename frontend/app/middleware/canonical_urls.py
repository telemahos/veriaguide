"""Single-hop 301/410 for locale, legacy categories, guides, slash, and favicon."""
from urllib.parse import parse_qsl, unquote, urlencode

from starlette.responses import RedirectResponse, Response

from app.utils.canonical import canonicalize_path

_PLACEHOLDER = "{search_term_string}"


def cleaned_query(query: str) -> tuple[str, bool]:
    """Drop the literal SearchAction placeholder and page=1. Other params stay."""
    pairs = parse_qsl(query or "", keep_blank_values=True)
    kept = []
    changed = False
    for key, value in pairs:
        if _PLACEHOLDER in unquote(key) or _PLACEHOLDER in unquote(value):
            changed = True
            continue
        if key == "page" and value == "1":
            changed = True
            continue
        kept.append((key, value))
    if not changed:
        return query or "", False
    return urlencode(kept), True


class CanonicalUrlMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or "/"
        action = canonicalize_path(path)
        query = (scope.get("query_string") or b"").decode("latin-1")
        new_query, query_changed = cleaned_query(query)
        if action is not None and action.status_code == 410:
            response = Response(status_code=410, content="Gone")
            await response(scope, receive, send)
            return
        target = path
        if action is not None and action.location and action.location != path:
            target = action.location
        if target == path and not query_changed:
            await self.app(scope, receive, send)
            return
        location = target
        if query_changed:
            if new_query:
                location = f"{location}?{new_query}"
        elif query:
            location = f"{location}?{query}"
        response = RedirectResponse(url=location, status_code=301)
        await response(scope, receive, send)
