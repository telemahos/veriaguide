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
    "/hiking-trails",
    "/hidden-gems",
    "/map",
    "/favorites",
]

DETAIL_PAGES = [
    "/religious-sites/sample-place",
    "/museums/sample-place",
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
    response = client.get("/hiking-trails")
    assert "Sample Place" in response.text
    assert 'href="/hiking-trails/sample-place"' in response.text


def test_tours_are_not_public(client):
    assert client.get("/tours").status_code == 404
    assert client.get("/tours/sample-place").status_code == 404
    assert client.get("/tours/map").status_code == 404
    home = client.get("/")
    assert 'href="/tours"' not in home.text
    assert ">Tours<" not in home.text


@pytest.mark.parametrize(
    "old, new",
    [("/religious_sites", "/religious-sites"), ("/hidden_gems/sample-place", "/hidden-gems/sample-place")],
)
def test_legacy_urls_redirect(client, old, new):
    response = client.get(old)
    assert response.status_code == 301
    assert response.headers["location"] == new


def test_category_name_is_not_a_query_parameter(client):
    response = client.get("/hiking-trails?category_name=../admin/submissions")
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
    for path in ("/hiking-trails", "/hidden-gems", "/hiking-trails/sample-place"):
        assert f"<loc>https://site.test{path}</loc>" in body
    assert "/tours" not in body
    assert "/religious_sites" not in body


def test_admin_requires_key(client):
    assert client.get("/admin/config").status_code in (401, 403)


ALL_LIST_PATHS = [
    "religious-sites", "museums", "archaeological-sites", "hidden-gems",
    "hiking-trails", "ski-resorts", "restaurants", "cafes", "accommodations",
]


@pytest.mark.parametrize("path", ALL_LIST_PATHS)
def test_every_listing_uses_shared_layout(client, path):
    html = client.get(f"/{path}").text
    assert 'id="sidebar-map"' in html
    assert f'action="/{path}"' in html
    assert f'href="/{path}/map"' in html
    assert f'href="/{path}/sample-place"' in html
    suggestions = client.get(f"/api/{path}/autocomplete").json()
    assert suggestions[0]["slug"] == "sample-place"
    assert client.get(f"/{path}/map").status_code == 200
