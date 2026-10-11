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
    body = response.json()
    assert set(body) == {"status"}
    assert body["status"] in {"healthy", "unhealthy"}
    leaked = response.text.lower()
    assert "redis" not in leaked
    assert "wordpress" not in leaked
    assert "connected_clients" not in leaked
    assert "wp-json" not in leaked


def test_detailed_health_is_admin_only(client, monkeypatch):
    assert client.get("/health/detailed").status_code == 401
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")
    denied = client.get("/health/detailed", headers={"X-API-Key": "nope"})
    assert denied.status_code == 401
    allowed = client.get("/health/detailed", headers={"X-API-Key": "test-key"})
    assert allowed.status_code in (200, 503)
    assert "dependencies" in allowed.json()


def test_public_cache_health_is_minimal(client):
    response = client.get("/admin/cache-health")
    assert response.status_code in (200, 503)
    body = response.json()
    assert set(body) == {"status"}
    assert body["status"] in {"healthy", "unhealthy"}
    assert "redis" not in response.text.lower()


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


def _jpeg_size(data: bytes) -> tuple[int, int]:
    import struct

    index = 2
    while index < len(data) - 8:
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[index + 5 : index + 9])
            return width, height
        if marker in (0xD8, 0xD9):
            index += 2
            continue
        segment = struct.unpack(">H", data[index + 2 : index + 4])[0]
        index += 2 + segment
    raise AssertionError("JPEG size marker missing")


def test_default_og_image_is_jpeg(client):
    response = client.get("/static/img/default-og.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.content[:3] == b"\xff\xd8\xff"
    assert _jpeg_size(response.content) == (1200, 630)


def _webp_size(data: bytes) -> tuple[int, int]:
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    chunk = data[12:16]
    if chunk == b"VP8X":
        return (
            1 + int.from_bytes(data[24:27], "little"),
            1 + int.from_bytes(data[27:30], "little"),
        )
    if chunk == b"VP8 ":
        assert data[23:26] == b"\x9d\x01\x2a"
        return (
            int.from_bytes(data[26:28], "little") & 0x3FFF,
            int.from_bytes(data[28:30], "little") & 0x3FFF,
        )
    raise AssertionError(f"unexpected webp chunk {chunk!r}")


def test_default_og_webp_matches_share_crop(client):
    response = client.get("/static/img/default-og.webp")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert _webp_size(response.content) == (1200, 630)


def test_hero_webp_content_type(client):
    response = client.get("/static/img/veria-hero2.webp")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"


def test_homepage_and_fallback_use_fresco_og_image(client):
    expected = {
        "/": "Byzantine fresco of two riders in the Old Metropolis of Veria",
        "/de/": "Byzantinisches Fresko mit zwei Reitern in der Alten Metropolis von Veria",
        "/el/": "Βυζαντινή τοιχογραφία με δύο έφιππους στην Παλαιά Μητρόπολη της Βέροιας",
    }
    image = 'content="https://site.test/static/img/default-og.jpg"'
    for path, alt in expected.items():
        html = client.get(path).text
        assert f'property="og:image" {image}' in html
        assert f'name="twitter:image" {image}' in html
        assert 'property="og:image:width" content="1200"' in html
        assert 'property="og:image:height" content="630"' in html
        assert 'property="og:image:type" content="image/jpeg"' in html
        assert f'property="og:image:alt" content="{alt}"' in html
        assert 'property="og:image" content="https://site.test/static/img/veria-hero2.webp"' not in html

    about = client.get("/about").text
    assert f'property="og:image" {image}' in about


def test_sanitize_meta_text_decodes_wordpress_entities():
    from app.utils.helpers import sanitize_meta_text

    raw = "the&amp;nbsp;Holy Church of Kosmas &amp;#038; Damian &#8220;Axion&#8221; [&amp;hellip;]"
    assert sanitize_meta_text(raw) == "the Holy Church of Kosmas & Damian \u201cAxion\u201d"
    assert sanitize_meta_text("the&nbsp;Holy [&hellip;]") == "the Holy"
    assert sanitize_meta_text("<p>Visit&nbsp;Veria</p>") == "Visit Veria"


def test_church_meta_does_not_leak_html_entities(client, fake_wp):
    fake_wp.posts[0]["title"] = {
        "rendered": "Holy Church of Kosmas &#038; Damian &#8220;Axion Estin&#8221;"
    }
    fake_wp.posts[0]["excerpt"] = {
        "rendered": "<p>Visit the&amp;nbsp;Holy Church of Saint Blaise&amp;nbsp;today [&amp;hellip;]</p>"
    }
    html = client.get("/religious-sites/sample-place").text
    description = html.split('name="description" content="', 1)[1].split('"', 1)[0]
    title = html.split("<title>", 1)[1].split("</title>", 1)[0]
    assert description.startswith("Visit the Holy Church of Saint Blaise today")
    assert "nbsp" not in description
    assert "hellip" not in description
    assert "[" not in description
    assert "Kosmas &amp; Damian" in title
    assert "Axion Estin" in title
    assert "&#038;" not in title
    assert "&#8220;" not in title
    assert "&amp;nbsp;" not in html
    assert "hellip" not in html
