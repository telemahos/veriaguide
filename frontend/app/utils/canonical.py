"""Compute a single canonical public path (locale, legacy categories, guides, slash)."""
from dataclasses import dataclass

from app.i18n import PREFIX_LANGS, localized_path
from app.utils.category_urls import resolve_legacy_category_path

# Old WordPress/guide URLs that have a clear replacement.
GUIDE_REDIRECTS: dict[str, str] = {
    "/guides": "/about",
    "/guides/kyriotissa": "/religious-sites",
    "/guides/neighborhoods": "/about",
    "/guides/one-day-in-veria": "/about",
    "/guides/vergina-half-day": "/archaeological-sites",
    "/guides/barbouta": "/archaeological-sites",
}

# Retired guide pages with no equivalent listing or article.
GUIDE_GONE: frozenset[str] = frozenset({
    "/guides/events",
    "/guides/thessaloniki-airport",
})

_KEEP_TRAILING_SLASH = frozenset({"/", "/el/", "/de/"})
_ALL_LANG_PREFIXES = ("en",) + PREFIX_LANGS


@dataclass(frozen=True)
class CanonicalAction:
    """Redirect or gone response for a request path."""

    status_code: int
    location: str | None = None


def split_locale_prefix(path: str) -> tuple[str | None, str]:
    """Return (lang_or_none, path_without_prefix). `en` is stripped like a prefix."""
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = "/" + path
    for code in _ALL_LANG_PREFIXES:
        prefix = f"/{code}"
        if path == prefix or path.startswith(prefix + "/"):
            rest = path[len(prefix):] or "/"
            if not rest.startswith("/"):
                rest = "/" + rest
            return code, rest
    return None, path


def _strip_trailing_slash(path: str, lang: str | None) -> str:
    if path in _KEEP_TRAILING_SLASH:
        return path
    if path.endswith("/") and path != "/":
        # Locale homepages are rebuilt later as /el/ — keep "/" here.
        return path.rstrip("/") or "/"
    return path


def canonicalize_path(path: str) -> CanonicalAction | None:
    """If the public URL should change, return 301/410; otherwise None."""
    original = path or "/"
    # Static assets must never enter redirect logic (the real favicon lives here).
    if original == "/static" or original.startswith("/static/"):
        return None

    lang, rest = split_locale_prefix(original)

    # Only the site-root favicon (and /el|/de|/en prefixed copies), never /static/...
    if rest == "/favicon.ico":
        return CanonicalAction(301, "/static/img/favicon.ico")

    rest = _strip_trailing_slash(rest, lang)

    legacy = resolve_legacy_category_path(rest)
    if legacy:
        rest = legacy

    if rest == "/guides" or rest.startswith("/guides/"):
        if rest in GUIDE_GONE:
            return CanonicalAction(410, None)
        target = GUIDE_REDIRECTS.get(rest)
        if target:
            rest = target
        else:
            return CanonicalAction(410, None)

    if lang in PREFIX_LANGS:
        final = localized_path(rest, lang)
    else:
        # English (including explicit /en) has no prefix.
        final = rest if rest else "/"

    if final != original:
        return CanonicalAction(301, final)
    return None
