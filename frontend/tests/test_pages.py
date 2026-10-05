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
    for path in (
        "/tours",
        "/restaurants",
        "/cafes",
        "/accommodations",
        "/ski-resorts",
        "/hiking-trails",
        "/hidden-gems",
        "/tours/sample-place",
    ):
        assert f"<loc>https://site.test{path}</loc>" in body
    assert "/religious_sites" not in body


def test_admin_requires_key(client):
    assert client.get("/admin/config").status_code in (401, 403)


ALL_LIST_PATHS = [
    "religious-sites", "museums", "archaeological-sites", "hidden-gems", "tours",
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


def test_legacy_cuisine_and_cafe_filters_still_apply(client, fake_wp, monkeypatch):
    from app.services import content_service as content_module

    async def posts_with_tags(post_type, search=None, category=None):
        return fake_wp.posts

    monkeypatch.setattr(content_module, "get_all_posts_for_type", posts_with_tags)

    import copy

    restaurant = copy.deepcopy(fake_wp.posts[0])
    restaurant.update(id=2, slug="taverna")
    restaurant["title"] = {"rendered": "Taverna"}
    restaurant["acf"] = {"cuisine_type": "Greek", "price_range": "€€"}
    restaurant["tag_names"] = ["Greek"]
    fake_wp.posts.append(restaurant)

    cafe = copy.deepcopy(fake_wp.posts[0])
    cafe.update(id=3, slug="kafenio")
    cafe["title"] = {"rendered": "Kafenio"}
    cafe["tag_names"] = ["Traditional"]
    fake_wp.posts.append(cafe)

    page = client.get("/restaurants?cuisine_type=Greek")
    assert page.status_code == 200
    assert "Taverna" in page.text
    assert "Sample Place" not in page.text
    assert "€€" in page.text and ">Greek<" in page.text

    cafes = client.get("/cafes?cafe_type=Traditional")
    assert "Kafenio" in cafes.text
    assert "Sample Place" not in cafes.text


def test_accommodation_filters_for_price_and_amenities(client, fake_wp, monkeypatch):
    from app.services import content_service as content_module

    async def posts_with_tags(post_type, search=None, category=None):
        return fake_wp.posts

    monkeypatch.setattr(content_module, "get_all_posts_for_type", posts_with_tags)
    import copy

    hotel = copy.deepcopy(fake_wp.posts[0])
    hotel.update(id=4, slug="hotel-veria")
    hotel["title"] = {"rendered": "Hotel Veria"}
    hotel["acf"] = {"price_range": "€€€", "amenities": ["Pool", "WiFi"]}
    fake_wp.posts.append(hotel)

    page = client.get("/accommodations")
    assert 'name="price_range"' in page.text
    assert 'name="amenities"' in page.text

    filtered = client.get("/accommodations?price_range=€€€&amenities=Pool")
    assert "Hotel Veria" in filtered.text
    assert "Sample Place" not in filtered.text


def test_default_og_image_is_jpeg(client):
    response = client.get("/static/img/default-og.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.content[:3] == b"\xff\xd8\xff"


def test_hero_webp_content_type(client):
    response = client.get("/static/img/veria-hero2.webp")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
