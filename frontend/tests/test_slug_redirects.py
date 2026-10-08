from urllib.parse import quote

from app.utils.canonical import canonicalize_path
from app.utils.slug_redirects import LISTING_SLUG_CHANGES, listing_redirect_target

LOCALES = {
    "en": "",
    "el": "/el",
    "de": "/de",
}


def _encodings(encoded: str, decoded: str) -> list[str]:
    upper = "".join(
        ch.upper() if i > 0 and encoded[i - 1] == "%" or (i > 1 and encoded[i - 2] == "%") else ch
        for i, ch in enumerate(encoded)
    )
    # Standard library quote uses uppercase hex digits.
    quoted = quote(decoded, safe="-._~")
    quoted_lower = "".join(
        ch.lower() if i > 0 and quoted[i - 1] == "%" or (i > 1 and quoted[i - 2] == "%") else ch
        for i, ch in enumerate(quoted)
    )
    variants = [encoded, encoded.lower(), quoted, quoted_lower, decoded]
    # Deduplicate while keeping order
    seen = set()
    out = []
    for item in variants:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def test_listing_lookup_covers_each_encoding():
    for category, encoded, decoded, new_slug in LISTING_SLUG_CHANGES:
        for variant in _encodings(encoded, decoded):
            assert listing_redirect_target(category, variant) == new_slug, (category, variant)
        assert listing_redirect_target(category, new_slug) is None


def test_canonicalize_listing_slugs_every_locale_and_slash():
    for category, encoded, decoded, new_slug in LISTING_SLUG_CHANGES:
        for variant in _encodings(encoded, decoded):
            for prefix in LOCALES.values():
                for slash in ("", "/"):
                    path = f"{prefix}/{category}/{variant}{slash}"
                    action = canonicalize_path(path)
                    assert action is not None, path
                    assert action.status_code == 301, path
                    assert action.location == f"{prefix}/{category}/{new_slug}", path


def test_new_latin_slugs_do_not_redirect():
    for category, _encoded, _decoded, new_slug in LISTING_SLUG_CHANGES:
        for prefix in LOCALES.values():
            path = f"{prefix}/{category}/{new_slug}"
            action = canonicalize_path(path)
            assert action is None, path


def test_vlachogianneio_redirect_all_locales():
    old = "/hidden-gems/vlachogianneio-museum-folklore-museum"
    new = "/archaeological-sites/vlachogianneio-museum-of-the-macedonian-struggle-in-veria"
    for prefix in LOCALES.values():
        for slash in ("", "/"):
            action = canonicalize_path(f"{prefix}{old}{slash}")
            assert action is not None
            assert action.status_code == 301
            assert action.location == f"{prefix}{new}"


def test_http_slug_redirects_are_single_hop(client):
    for category, encoded, decoded, new_slug in LISTING_SLUG_CHANGES:
        for variant in (encoded, decoded):
            for prefix in LOCALES.values():
                response = client.get(f"{prefix}/{category}/{variant}", follow_redirects=False)
                assert response.status_code == 301, variant
                assert response.headers["location"] == f"{prefix}/{category}/{new_slug}"
                follow = client.get(response.headers["location"], follow_redirects=False)
                assert follow.status_code in (200, 404)
                assert follow.headers.get("location") is None


def test_http_new_slug_is_not_a_redirect_loop(client):
    response = client.get("/de/cafes/cafe-lakis", follow_redirects=False)
    assert response.status_code == 404
    assert response.headers.get("location") is None


def test_http_vlachogianneio(client):
    for prefix in LOCALES.values():
        response = client.get(
            f"{prefix}/hidden-gems/vlachogianneio-museum-folklore-museum/",
            follow_redirects=False,
        )
        assert response.status_code == 301
        assert (
            response.headers["location"]
            == f"{prefix}/archaeological-sites/vlachogianneio-museum-of-the-macedonian-struggle-in-veria"
        )


def test_tag_slug_typo_redirects(client):
    for prefix in LOCALES.values():
        archeo = client.get(f"{prefix}/tag/archeological-site", follow_redirects=False)
        assert archeo.status_code == 301
        assert archeo.headers["location"] == f"{prefix}/tag/archaeological-site"
        hike = client.get(f"{prefix}/tags/hicking/", follow_redirects=False)
        assert hike.status_code == 301
        assert hike.headers["location"] == f"{prefix}/tags/hiking"
