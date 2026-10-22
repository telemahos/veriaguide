import pytest

from app.utils.canonical import canonicalize_path
from app.utils.church_slugs import public_church_slug


@pytest.mark.parametrize("path,target", [
    # WordPress attachment pages fold into the parent listing (single hop, short church slug)
    ("/religious_sites/holy-church-of-saint-stephen-a-16th-century-sanctuary-in-veria-greece/img_6222/",
     "/religious-sites/holy-church-of-saint-stephen"),
    ("/religious_site/holy-church-of-saint-barbara-a-serene-sanctuary-in-veria-greece/img_6328/",
     "/religious-sites/holy-church-of-saint-barbara"),
    ("/el/religious_sites/holy-church-of-hosios-patapios-15th-c/img_6329",
     "/el/religious-sites/holy-church-of-hosios-patapios-15th-c"),
    # Old long church slugs go straight to the short public slug
    ("/religious_sites/the-holy-church-of-the-virgin-mary-peribleptos-a-byzantine-masterpiece-in-veria-greece",
     "/religious-sites/holy-church-of-the-virgin-mary-peribleptos"),
    ("/de/religious-sites/holy-church-of-saint-basil-verias-18th-century-spiritual-haven",
     "/de/religious-sites/holy-church-of-saint-basil"),
    ("/religious_site/metochion-of-the-holy-monastery-of-the-virgin-mary-kallipetra-a-spiritual-retreat-in-veria-greece/",
     "/religious-sites/metochion-of-the-holy-monastery-of-the-virgin-mary-kallipetra"),
    # Singular WordPress post-type prefixes
    ("/restaurant/giannis", "/restaurants/giannis"),
    ("/cafe/mr-coffee/", "/cafes/mr-coffee"),
    # Tags -> closest hub
    ("/tag/christianity/", "/religious-sites"),
    ("/tag/historical/", "/archaeological-sites"),
    ("/tag/vergina/", "/archaeological-sites"),
    ("/tag/veria/", "/hidden-gems"),
    ("/el/tag/christianity", "/el/religious-sites"),
])
def test_gsc_404_redirects_single_hop(path, target):
    action = canonicalize_path(path)
    assert action is not None and action.status_code == 301, path
    assert action.location == target
    assert canonicalize_path(target) is None, "target must not redirect again"


@pytest.mark.parametrize("path", [
    "/religious-sites/${site.slug}",
    "/cafes/${cafe.slug}",
    "/archaeological-sites/%24%7Bsite.slug%7D",
    "/el/museums/${site.slug}",
])
def test_unrendered_js_template_paths_are_gone(path):
    action = canonicalize_path(path)
    assert action is not None and action.status_code == 410


@pytest.mark.parametrize("slug", [
    "holy-church-of-saint-stephen",
    "holy-church-of-hosios-patapios-15th-c",
    "holy-church-of-the-virgin-mary-evangelistria",
    "step-of-the-apostle-paul",
])
def test_current_church_slugs_are_stable(slug):
    assert public_church_slug(slug) == slug
    assert canonicalize_path(f"/religious-sites/{slug}") is None
    assert canonicalize_path(f"/el/religious-sites/{slug}") is None


def test_listing_attachment_rule_does_not_touch_other_paths():
    assert canonicalize_path("/restaurants/map") is None
    assert canonicalize_path("/api/religious-sites/autocomplete") is None


def test_http_attachment_redirect(client):
    response = client.get("/religious_sites/sample-place-in-veria-greece/img_6268/", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/religious-sites/sample-place"


def test_http_template_literal_is_410(client):
    response = client.get("/cafes/${cafe.slug}", follow_redirects=False)
    assert response.status_code == 410


def test_api_and_map_search_are_noindex(client):
    api = client.get("/api/museums/autocomplete")
    assert api.status_code == 200
    assert api.headers["x-robots-tag"] == "noindex"
    el_api = client.get("/el/api/religious-sites/autocomplete")
    assert el_api.headers.get("x-robots-tag") == "noindex"
    placeholder = client.get("/el/map", params={"q": "{search_term_string}"})
    assert placeholder.status_code == 301
    assert placeholder.headers["location"] == "/el/map"
    search_map = client.get("/el/map", params={"q": "veria"})
    assert search_map.status_code == 200
    assert search_map.headers["x-robots-tag"] == "noindex, follow"
    plain_map = client.get("/map")
    assert "noindex" not in plain_map.headers.get("x-robots-tag", "")


def test_robots_disallows_json_endpoints(client):
    body = client.get("/robots.txt").text
    for rule in ("Disallow: /api/", "Disallow: /el/api/", "Disallow: /de/api/", "Disallow: /wp-json/"):
        assert rule in body


@pytest.mark.parametrize("path", ["/religious-sites", "/el/restaurants", "/religious-sites/map", "/"])
def test_no_crawlable_js_template_links(client, path):
    html = client.get(path, params={"theme": "classic"}).text
    for junk in ("/${site.slug}", "/${location.slug}", "/${cafe.slug}", "/${item.category}"):
        assert junk not in html, (path, junk)
