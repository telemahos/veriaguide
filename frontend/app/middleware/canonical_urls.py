"""Single-hop 301/410 for locale, legacy categories, guides, slash, and favicon."""
from urllib.parse import parse_qsl, unquote, urlencode

from starlette.responses import RedirectResponse, Response

from app.utils.canonical import canonicalize_path

_PLACEHOLDER = "{search_term_string}"
_LANG_REDIRECTS = {"el", "de", "en"}
# lang= on these paths is an API argument, not a locale switch.
_LANG_REDIRECT_SKIP = ("/api/", "/static/", "/admin", "/health", "/sitemap", "/robots", "/favicon", "/wp-")


def _strip_locale_prefix(path: str) -> str:
    for code in ("el", "de"):
        prefix = f"/{code}"
        if path == prefix or path.startswith(prefix + "/"):
            rest = path[len(prefix):] or "/"
            return rest if rest.startswith("/") else "/" + rest
    return path or "/"


def lang_query_redirect(path: str, query: str) -> str | None:
    """301 ?lang=el|de|en to the clean locale path. Other params stay. No loop once lang is gone."""
    if any(path == item.rstrip("/") or path.startswith(item) for item in _LANG_REDIRECT_SKIP):
        return None
    pairs = parse_qsl(query or "", keep_blank_values=True)
    lang = None
    kept = []
    for key, value in pairs:
        if key == "lang":
            if lang is None:
                lang = value
            continue
        kept.append((key, value))
    if lang not in _LANG_REDIRECTS:
        return None
    bare = _strip_locale_prefix(path or "/")
    if len(bare) > 1:
        bare = bare.rstrip("/") or "/"
    if lang in {"el", "de"}:
        target = f"/{lang}/" if bare == "/" else f"/{lang}{bare}"
    else:
        target = bare or "/"
    new_query = urlencode(kept)
    location = f"{target}?{new_query}" if new_query else target
    original = path or "/"
    if query:
        original = f"{original}?{query}"
    if location == original:
        return None
    return location


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
        query = (scope.get("query_string") or b"").decode("latin-1")
        method = scope.get("method") or "GET"
        if method in {"GET", "HEAD"}:
            lang_location = lang_query_redirect(path, query)
            if lang_location:
                response = RedirectResponse(url=lang_location, status_code=301)
                await response(scope, receive, send)
                return
        action = canonicalize_path(path)
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
