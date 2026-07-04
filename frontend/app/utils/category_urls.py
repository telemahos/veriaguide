"""
Public URL paths for content categories (SEO-friendly hyphens).

Internal category keys (e.g. religious_sites) stay unchanged for WordPress/API.
Public paths use hyphens where the key contains underscores.
"""
from typing import Dict, Optional
from urllib.parse import urlencode

from app.config import POST_TYPES

# Internal category key -> public URL segment
PUBLIC_CATEGORY_PATHS: Dict[str, str] = {
    category: category.replace("_", "-")
    for category in POST_TYPES
}

# Paths that changed from legacy underscore URLs
LEGACY_CATEGORY_PREFIXES: Dict[str, str] = {
    f"/{key}": f"/{path}"
    for key, path in PUBLIC_CATEGORY_PATHS.items()
    if key != path
}

LEGACY_API_PREFIXES: Dict[str, str] = {
    f"/api/{key}": f"/api/{path}"
    for key, path in PUBLIC_CATEGORY_PATHS.items()
    if key != path
}


def get_category_url_path(category_key: str) -> str:
    """Return the public URL path segment for a category key."""
    return PUBLIC_CATEGORY_PATHS.get(category_key, category_key.replace("_", "-"))


def get_category_key_from_url_path(url_path: str) -> Optional[str]:
    """Map a public URL segment back to the internal category key."""
    for key, path in PUBLIC_CATEGORY_PATHS.items():
        if path == url_path:
            return key
    return None


def resolve_legacy_category_path(path: str) -> Optional[str]:
    """Return the new hyphenated path if path uses a legacy underscore URL."""
    for old_prefix, new_prefix in LEGACY_CATEGORY_PREFIXES.items():
        if path == old_prefix:
            return new_prefix
        if path.startswith(old_prefix + "/"):
            return new_prefix + path[len(old_prefix):]

    for old_prefix, new_prefix in LEGACY_API_PREFIXES.items():
        if path == old_prefix:
            return new_prefix
        if path.startswith(old_prefix + "/"):
            return new_prefix + path[len(old_prefix):]

    return None


def normalize_public_url(url: str) -> str:
    """Rewrite legacy underscore category paths in a URL or path."""
    if not url or url == "#":
        return url

    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    path = parsed.path if parsed.scheme or parsed.netloc else url.split("?", 1)[0]
    new_path = resolve_legacy_category_path(path)
    if not new_path:
        return url

    if parsed.scheme or parsed.netloc:
        return urlunparse(parsed._replace(path=new_path))

    query = url.split("?", 1)[1] if "?" in url else ""
    return new_path + (f"?{query}" if query else "")


def build_category_list_url(category_key: str, page: int = 1, query_params: Optional[dict] = None) -> str:
    """Build a public list URL for a category, preserving filter query params."""
    base = f"/{get_category_url_path(category_key)}"
    params = dict(query_params or {})
    params.pop("page", None)
    if page > 1:
        params["page"] = str(page)
    if params:
        return f"{base}?{urlencode(params)}"
    return base
