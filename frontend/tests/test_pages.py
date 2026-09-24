import pytest

LIST_PAGES = [
    "/",
    "/about",
    "/contact",
    "/religious-sites",
    "/museums",
    "/archaeological-sites",
    "/restaurants",
    "/cafes",
    "/accommodations",
    "/ski-resorts",
    "/tours",
    "/hiking-trails",
    "/hidden-gems",
    "/map",
    "/favorites",
]

DETAIL_PAGES = [
    "/religious-sites/sample-place",
    "/museums/sample-place",
    "/tours/sample-place",
    "/hiking-trails/sample-place",
    "/hidden-gems/sample-place",
]


@pytest.mark.parametrize("path", LIST_PAGES)
def test_page_renders(client, path):
    response = client.get(path)
    assert response.status_code == 200, response.text[:500]
    assert "text/html" in response.headers["content-type"]


@pytest.mark.parametrize("path", DETAIL_PAGES)
def test_detail_page_renders(client, path):
    response = client.get(path)
    assert response.status_code == 200, response.text[:500]
    assert "Sample Place" in response.text


def test_category_list_shows_item(client):
    response = client.get("/tours")
    assert "Sample Place" in response.text
    assert 'href="/tours/sample-place"' in response.text


@pytest.mark.parametrize(
    "old, new",
    [("/religious_sites", "/religious-sites"), ("/hidden_gems/sample-place", "/hidden-gems/sample-place")],
)
def test_legacy_urls_redirect(client, old, new):
    response = client.get(old)
    assert response.status_code == 301
    assert response.headers["location"] == new


def test_category_name_is_not_a_query_parameter(client):
    response = client.get("/tours?category_name=../admin/submissions")
    assert response.status_code == 200
    assert "Sample Place" in response.text


def test_health_reports_status(client):
    response = client.get("/health")
    assert response.status_code in (200, 503)
    assert "status" in response.json()


def test_robots_txt(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "Sitemap:" in response.text


def test_sitemap_contains_activated_categories(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    body = response.text
    for path in ("/tours", "/hiking-trails", "/hidden-gems", "/tours/sample-place"):
        assert f"<loc>https://site.test{path}</loc>" in body
    assert "/religious_sites" not in body


def test_admin_requires_key(client):
    assert client.get("/admin/config").status_code in (401, 403)
