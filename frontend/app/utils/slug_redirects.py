"""301 maps for listing slugs that will change in WordPress.

Look these up in canonicalize_path *before* any WordPress request so old URLs
start redirecting as soon as this frontend is deployed, even while WP still
serves the old slug and the new slug 404s.
"""
from __future__ import annotations

from urllib.parse import quote, unquote

# type, old WP slug (lowercase %-encoding as in sitemaps), decoded, new latin slug
LISTING_SLUG_CHANGES: tuple[tuple[str, str, str, str], ...] = (
    ("accommodations", "%ce%ba%cf%8c%ce%ba%ce%ba%ce%b9%ce%bd%ce%bf-%cf%83%cf%80%ce%af%cf%84%ce%b9-boutique-hotel", "κόκκινο-σπίτι-boutique-hotel", "kokkino-spiti-boutique-hotel"),
    ("accommodations", "olympia-guesthouse-%ce%be%ce%b5%ce%bd%ce%bf%ce%b4%ce%bf%cf%87%ce%b5%ce%af%ce%bf", "olympia-guesthouse-ξενοδοχείο", "olympia-guesthouse"),
    ("restaurants", "bergi%e1%b9%93tiko", "bergiṓtiko", "vergiotiko"),
    ("restaurants", "volcano-%d0%b2%d1%83%d0%bb%d0%ba%d0%b0%d0%bd", "volcano-вулкан", "volcano"),
    ("restaurants", "813-va%cf%8anas-vas-georgios-deli-n-street-food", "813-vaϊnas-vas-georgios-deli-n-street-food", "813-vainas-deli-street-food"),
    ("cafes", "kochl%ce%afas", "kochlίas", "kochlias"),
    ("cafes", "big-time-v%ce%adroias", "big-time-vέroias", "big-time-veroias"),
    ("cafes", "coffee-island-v%ce%adroia", "coffee-island-vέroia", "coffee-island-veroia"),
    ("cafes", "coffee-island-v%ce%adroia-cream-ike", "coffee-island-vέroia-cream-ike", "coffee-island-veroia-cream-ike"),
    ("cafes", "panorama-kaf%ce%ad-anapsykt%ce%aerio", "panorama-kafέ-anapsyktήrio", "panorama-kafe-anapsyktirio"),
    ("cafes", "snack-bar-ap%cf%8claysi", "snack-bar-apόlaysi", "snack-bar-apolaysi"),
    ("cafes", "afr%cf%8cs-bar", "afrόs-bar", "afros-bar"),
    ("cafes", "cafe-l%ce%ackis", "cafe-lάkis", "cafe-lakis"),
    ("cafes", "kafene%ce%afo-verg%ce%afna", "kafeneίo-vergίna", "kafeneio-vergina"),
    ("cafes", "mikr%cf%8c-kafe", "mikrό-kafe", "mikro-kafe"),
    ("cafes", "fl%cf%8cou-microroastery", "flόou-microroastery", "floou-microroastery"),
)

# Exact public paths (no locale prefix) that move to another category/slug.
PATH_REDIRECTS: dict[str, str] = {
    "/hidden-gems/vlachogianneio-museum-folklore-museum": (
        "/archaeological-sites/vlachogianneio-museum-of-the-macedonian-struggle-in-veria"
    ),
}

# WP term slugs that the frontend should treat as aliases of the corrected slug.
TAG_SLUG_REDIRECTS: dict[str, str] = {
    "archeological-site": "archaeological-site",
    "hicking": "hiking",
}

CATEGORY_PATH_ALIASES: dict[str, str] = {
    "/archeological-sites": "/archaeological-sites",
}


def _hex_case_variants(encoded: str) -> set[str]:
    """Lowercase and uppercase percent-escapes (sitemap vs some clients)."""
    out = {encoded, encoded.lower(), encoded.upper()}
    chars = list(encoded)
    i = 0
    while i < len(chars):
        if chars[i] == "%" and i + 2 < len(chars):
            chars[i + 1] = chars[i + 1].upper()
            chars[i + 2] = chars[i + 2].upper()
            i += 3
        else:
            i += 1
    out.add("".join(chars))
    chars = list(encoded)
    i = 0
    while i < len(chars):
        if chars[i] == "%" and i + 2 < len(chars):
            chars[i + 1] = chars[i + 1].lower()
            chars[i + 2] = chars[i + 2].lower()
            i += 3
        else:
            i += 1
    out.add("".join(chars))
    return out


def _slug_keys(encoded: str, decoded: str) -> set[str]:
    keys = {decoded, unquote(encoded), unquote(unquote(encoded))}
    keys.update(_hex_case_variants(encoded))
    quoted = quote(decoded, safe="-._~")
    keys.update(_hex_case_variants(quoted))
    keys.update(_hex_case_variants(quote(decoded, safe="-")))
    return {k for k in keys if k}


def _build_listing_lookup() -> dict[tuple[str, str], str]:
    lookup: dict[tuple[str, str], str] = {}
    for category, encoded, decoded, new_slug in LISTING_SLUG_CHANGES:
        for key in _slug_keys(encoded, decoded):
            if key == new_slug:
                continue
            lookup[(category, key)] = new_slug
    return lookup


_LISTING_LOOKUP = _build_listing_lookup()


def listing_redirect_target(category: str, slug: str) -> str | None:
    """Return the new latin slug, or None if this URL should not redirect."""
    if not category or not slug:
        return None
    slug = slug.rstrip("/")
    if not slug:
        return None
    target = _LISTING_LOOKUP.get((category, slug))
    if target and target != slug:
        return target
    decoded = unquote(slug)
    if decoded != slug:
        target = _LISTING_LOOKUP.get((category, decoded))
        if target and target != decoded:
            return target
    return None


def redirect_bare_path(rest: str) -> str | None:
    """Map a locale-stripped path to its canonical path, or None."""
    if not rest:
        return None
    path = rest if rest.startswith("/") else "/" + rest
    path = path.rstrip("/") or "/"

    exact = PATH_REDIRECTS.get(path)
    if exact:
        return exact

    for old_prefix, new_prefix in CATEGORY_PATH_ALIASES.items():
        if path == old_prefix:
            return new_prefix
        if path.startswith(old_prefix + "/"):
            path = new_prefix + path[len(old_prefix):]
            break

    parts = path.strip("/").split("/")
    if len(parts) == 2:
        category, slug = parts
        new_slug = listing_redirect_target(category, slug)
        if new_slug:
            return f"/{category}/{new_slug}"
    if len(parts) == 2 and parts[0] in ("tag", "tags"):
        new_tag = TAG_SLUG_REDIRECTS.get(parts[1]) or TAG_SLUG_REDIRECTS.get(unquote(parts[1]))
        if new_tag and new_tag != parts[1]:
            return f"/{parts[0]}/{new_tag}"
    return None if path == (rest.rstrip("/") or "/") else path
