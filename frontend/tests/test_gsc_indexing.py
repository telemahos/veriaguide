import copy

import httpx
import pytest

from app.utils.canonical import GUIDE_GONE, GUIDE_REDIRECTS, canonicalize_path
from app.utils.helpers import listing_detail_href, listing_map_point, usable_listing_slug

ALL_MAP_PATHS = [
    "religious-sites",
    "museums",
    "archaeological-sites",
    "hidden-gems",
    "tours",
    "hiking-trails",
    "ski-resorts",
    "restaurants",
    "cafes",
    "accommodations",
]


def test_usable_listing_slug_rejects_placeholders():
    assert usable_listing_slug(None) is None
    assert usable_listing_slug("") is None
    assert usable_listing_slug("null") is None
    assert usable_listing_slug("sample-place") == "sample-place"
    assert listing_detail_href({"slug": None}, "cafes") == ""
    assert listing_detail_href({"slug": "cafe-one"}, "cafes") == "/cafes/cafe-one"


def test_listing_map_point_uses_trail_map():
    item = {"acf": {"trail_map": {"lat": 40.1, "lng": 22.2, "address": "Trailhead"}}}
    point = listing_map_point(item)
    assert point["lat"] == 40.1
    assert listing_map_point({"acf": {}}) is None


@pytest.mark.parametrize("path", ALL_MAP_PATHS)
@pytest.mark.parametrize("prefix", ["", "/el", "/de"])
def test_every_category_map_page_renders(client, fake_wp, path, prefix):
    trail = copy.deepcopy(fake_wp.posts[0])
    trail["acf"].pop("location_map", None)
    fake_wp.posts[0] = trail
    response = client.get(f"{prefix}/{path}/map")
    assert response.status_code == 200, response.text[:400]
    assert "/null" not in response.text


def test_map_skips_items_without_coordinates(client, fake_wp):
    fake_wp.posts[0]["acf"] = {}
    response = client.get("/hiking-trails/map")
    assert response.status_code == 200
    assert 'class="card mb-4 shadow-sm map-listing-card"' not in response.text
    assert "No Results Found" in response.text


def test_wordpress_outage_is_503_not_404(client, fake_wp):
    original_get = fake_wp.get

    def failing_get(url, params=None, **kwargs):
        if "/wp/v2/" in url:
            request = httpx.Request("GET", url)
            return httpx.Response(500, text="wp down", request=request)
        return original_get(url, params=params, **kwargs)

    fake_wp.get = failing_get
    response = client.get("/cafes/sample-place")
    assert response.status_code == 503
    assert response.headers.get("retry-after") == "120"
    listing = client.get("/cafes")
    assert listing.status_code == 503
    assert client.get("/cafes/definitely-missing-when-wp-works").status_code == 503


def test_wordpress_retries_then_raises(client, fake_wp):
    calls = {"n": 0}

    def failing_get(url, params=None, **kwargs):
        request = httpx.Request("GET", url)
        if "/wp/v2/" in url:
            calls["n"] += 1
            return httpx.Response(502, text="bad gateway", request=request)
        return httpx.Response(200, json=[], request=request)

    fake_wp.get = failing_get
    assert client.get("/museums/sample-place").status_code == 503
    assert calls["n"] >= 3


def test_missing_slug_is_still_404(client):
    assert client.get("/cafes/no-such-place").status_code == 404


def test_empty_wp_payload_is_not_cached(monkeypatch, fake_wp):
    from app.api import wordpress as wp
    from app.services.cache_service import CacheService

    stored = []

    async def capture_set(key, value, ttl=None, params=None):
        stored.append((key, value))
        return True

    async def cache_miss(*args, **kwargs):
        return None

    monkeypatch.setattr(CacheService, "set", staticmethod(capture_set))
    monkeypatch.setattr(CacheService, "get", staticmethod(cache_miss))

    original_get = fake_wp.get

    def empty_get(url, params=None, **kwargs):
        if "/wp/v2/" in url:
            request = httpx.Request("GET", url)
            return httpx.Response(200, json=[], request=request)
        return original_get(url, params=params, **kwargs)

    fake_wp.get = empty_get

    import asyncio

    asyncio.get_event_loop().run_until_complete(wp.api_request("cafes", {"slug": "x"}))
    assert stored == []


def test_robots_txt_single_group_disallows_all_crawlers(client):
    text = client.get("/robots.txt").text
    assert "User-agent: Googlebot" not in text
    assert "User-agent: Bingbot" not in text
    assert "User-agent: *" in text
    for rule in ("Disallow: /admin/", "Disallow: /api/", "Disallow: /favorites", "Disallow: /search"):
        assert rule in text


def test_favorites_header_link_is_nofollow(client):
    html = client.get("/").text
    assert 'href="/favorites"' in html
    assert 'rel="nofollow"' in html


@pytest.mark.parametrize("old, new", list(GUIDE_REDIRECTS.items()))
def test_legacy_guides_redirect(client, old, new):
    response = client.get(old)
    assert response.status_code == 301
    assert response.headers["location"] == new
    el = client.get(f"/el{old}")
    assert el.status_code == 301
    assert el.headers["location"] == f"/el{new}" if new != "/" else "/el/"


@pytest.mark.parametrize("path", sorted(GUIDE_GONE))
def test_legacy_guides_gone(client, path):
    assert client.get(path).status_code == 410
    assert client.get(f"/de{path}").status_code == 410


def test_root_favicon_redirects_once_static_is_not_redirected(client):
    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 301
    assert favicon.headers["location"] == "/static/img/favicon.ico"

    for prefixed in ("/el/favicon.ico", "/de/favicon.ico", "/en/favicon.ico"):
        response = client.get(prefixed)
        assert response.status_code == 301, prefixed
        assert response.headers["location"] == "/static/img/favicon.ico"

    static = client.get("/static/img/favicon.ico")
    assert static.status_code == 200
    assert static.headers.get("location") is None
    assert len(static.content) > 0


def test_en_prefix_redirect(client):
    assert client.get("/en").status_code == 301
    assert client.get("/en").headers["location"] == "/"
    en_detail = client.get("/en/cafes/sample-place")
    assert en_detail.status_code == 301
    assert en_detail.headers["location"] == "/cafes/sample-place"


def test_canonicalize_does_not_touch_static_favicon():
    assert canonicalize_path("/static/img/favicon.ico") is None
    assert canonicalize_path("/static/img/favicon.ico/") is None
    action = canonicalize_path("/favicon.ico")
    assert action is not None
    assert action.status_code == 301
    assert action.location == "/static/img/favicon.ico"


def test_legacy_category_chain_is_single_hop(client):
    response = client.get("/el/religious_sites/sample-place/")
    assert response.status_code == 301
    assert response.headers["location"] == "/el/religious-sites/sample-place"
    follow = client.get(response.headers["location"])
    assert follow.status_code == 200


def test_sitemap_uses_post_lastmod_and_escapes(client, fake_wp):
    fake_wp.posts[0]["slug"] = "cafe-&-bar"
    fake_wp.posts[0]["modified"] = "2026-03-15T12:00:00"
    body = client.get("/sitemap.xml").text
    assert "<lastmod>2026-03-15</lastmod>" in body
    assert "cafe-&amp;-bar" in body
    assert "<lastmod>" in body


def test_sitemap_omits_empty_hubs(client, monkeypatch):
    from app.services import sitemap_service as sitemap_mod

    async def fake_posts(post_type, search=None, category=None):
        if post_type == "tour":
            return []
        return [copy.deepcopy(__import__("tests.conftest", fromlist=["SAMPLE_POST"]).SAMPLE_POST)]

    monkeypatch.setattr(sitemap_mod, "get_all_posts_for_type", fake_posts)
    body = client.get("/sitemap.xml").text
    assert body.count("<loc>https://site.test/tours</loc>") == 0
    assert "<loc>https://site.test/cafes</loc>" in body


def test_sitemap_503_when_wordpress_fails(client, fake_wp):
    def failing_get(url, params=None, **kwargs):
        request = httpx.Request("GET", url)
        if "/wp/v2/" in url:
            return httpx.Response(503, text="down", request=request)
        return httpx.Response(200, json=[], request=request)

    fake_wp.get = failing_get
    response = client.get("/sitemap.xml")
    assert response.status_code == 503
    assert response.headers.get("retry-after") == "120"


def test_canonicalize_unknown_guide_is_410():
    action = canonicalize_path("/guides/not-a-real-guide")
    assert action is not None
    assert action.status_code == 410
