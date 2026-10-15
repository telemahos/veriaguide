"""Live SEO audit: theme duplicates, hyphen links, JSON-LD, localized meta, sitemap."""
import copy
import json
import re
from urllib.parse import urlparse

import pytest

from tests.conftest import SAMPLE_POST

UNDERSCORE_TYPES = (
    "religious_sites",
    "archaeological_sites",
    "hiking_trails",
    "ski_resorts",
    "hidden_gems",
)
HREF_RE = re.compile(r"""href=(["'])([^"']+)\1""")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")


def _meta(html: str, name: str) -> str:
    match = re.search(rf'<meta name="{name}" content="([^"]*)"', html)
    assert match, name
    return match.group(1)


def _canonical(html: str) -> str:
    match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert match
    return match.group(1)


def _hreflang(html: str) -> dict[str, str]:
    pairs = re.findall(
        r'<link rel="alternate" href="([^"]+)" hreflang="([^"]+)"',
        html,
    )
    return {lang: href for href, lang in pairs}


def _title(html: str) -> str:
    match = TITLE_RE.search(html)
    assert match
    return match.group(1)


def _jsonld(html: str) -> list:
    blocks = []
    for raw in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S):
        blocks.append(json.loads(raw))
    return blocks


def _nodes(html: str) -> list[dict]:
    found = []
    for block in _jsonld(html):
        if isinstance(block, dict) and isinstance(block.get("@graph"), list):
            found.extend(block["@graph"])
        elif isinstance(block, dict):
            found.append(block)
    return found


def _typed(html: str, schema_type: str) -> dict:
    for node in _nodes(html):
        if node.get("@type") == schema_type:
            return node
    raise AssertionError(schema_type)


def _href_paths(html: str) -> list[str]:
    paths = []
    for _quote, href in HREF_RE.findall(html):
        path = urlparse(href).path
        paths.append(path)
    return paths


def _assert_no_underscore_href(html: str):
    for path in _href_paths(html):
        parts = [part for part in path.split("/") if part]
        assert not any(part in UNDERSCORE_TYPES for part in parts), path


def _localized_place(fake_wp):
    post = fake_wp.posts[0]
    post["title"] = {"rendered": "Παναγία της Βέροιας"}
    post["excerpt"] = {"rendered": "<p>Περιγραφή στα ελληνικά για τον ναό.</p>"}
    post["content"] = {"rendered": "<p>Μεγάλο ελληνικό κείμενο για τη σελίδα λεπτομερειών.</p>"}
    post["acf"] = {
        **post["acf"],
        "title_en": "Church of the Virgin",
        "title_el": ["Ναός της Παναγίας"],
        "title_de": "Kirche der Jungfrau",
        "excerpt_en": "A Byzantine church in Veria (about 4.7) with frescoes.",
        "seo_description_en": "Byzantine church of the Virgin in Veria, with frescoes and a visitor map.",
        "excerpt_el": "Βυζαντινός ναός της Παναγίας στη Βέροια, με τοιχογραφίες και χάρτη.",
        "excerpt_de": "Byzantinische Kirche der Jungfrau in Veria, mit Fresken und Besucherhinweisen.",
        "phone": "+30 23310 12345",
        "opening_hours": "Monday: 9:00-17:00\nTuesday: Closed\nAsk the caretaker at the gate",
    }


def test_theme_query_is_noindex_and_absent_from_canonical(client):
    response = client.get("/restaurants", params={"theme": "new"})
    assert response.status_code == 200
    html = response.text
    assert response.headers["x-robots-tag"] == "noindex, follow"
    assert _meta(html, "robots") == "noindex, follow"
    assert _canonical(html) == "https://site.test/restaurants"
    alternates = _hreflang(html)
    assert alternates["en"] == "https://site.test/restaurants"
    assert alternates["el"] == "https://site.test/el/restaurants"
    assert alternates["de"] == "https://site.test/de/restaurants"
    assert all("theme" not in href and "theme" not in _canonical(html) for href in alternates.values())
    assert "?theme=" not in html
    assert 'data-set-theme="new"' in html
    assert 'data-set-theme="classic"' in html
    assert 'data-set-theme="zeitalter"' in html

    paged = client.get("/restaurants", params={"theme": "classic", "page": "2"}).text
    assert _canonical(paged) == "https://site.test/restaurants?page=2"
    assert "theme" not in _canonical(paged)
    assert all("theme" not in href for href in _hreflang(paged).values())


@pytest.mark.parametrize("theme", ["classic", "new"])
@pytest.mark.parametrize("prefix", ["", "/el", "/de"])
@pytest.mark.parametrize("hub", ["religious-sites", "archaeological-sites", "hiking-trails"])
def test_hub_and_detail_hrefs_use_hyphen_paths(client, fake_wp, theme, prefix, hub):
    second = copy.deepcopy(SAMPLE_POST)
    second.update(id=2, slug="other-place")
    fake_wp.posts.append(second)
    client.cookies.set("vg_theme", theme)
    hub_html = client.get(f"{prefix}/{hub}").text
    detail_html = client.get(f"{prefix}/{hub}/sample-place").text
    _assert_no_underscore_href(hub_html)
    _assert_no_underscore_href(detail_html)
    locale = prefix or ""
    assert f'href="{locale}/{hub}/sample-place"' in hub_html or f'href="{locale}/{hub}/other-place"' in hub_html
    assert f'href="{locale}/{hub}"' in detail_html
    assert f'href="{locale}/{hub}/other-place"' in detail_html


def test_detail_jsonld_has_breadcrumbs_phone_hours_and_no_placeholder(client, fake_wp):
    _localized_place(fake_wp)
    html = client.get("/religious-sites/sample-place").text
    place = _typed(html, "PlaceOfWorship")
    crumbs = _typed(html, "BreadcrumbList")
    assert place["name"] == "Church of the Virgin"
    assert place["url"] == "https://site.test/religious-sites/sample-place"
    assert place["inLanguage"] == "en"
    assert place["telephone"] == "+30 23310 12345"
    assert place["address"]["streetAddress"] == "Main Street 1, Veria"
    assert place["address"]["addressCountry"] == "GR"
    assert place["geo"]["latitude"] == 40.52
    assert place["geo"]["longitude"] == 22.2
    assert "image" not in place
    assert "placeholder" not in html.split('property="og:image"', 1)[1][:200]
    assert 'property="og:image" content="https://site.test/static/img/default-og.jpg"' in html
    hours = place["openingHoursSpecification"]
    assert len(hours) == 1
    assert hours[0]["dayOfWeek"] == "Monday"
    assert hours[0]["opens"] == "09:00"
    assert hours[0]["closes"] == "17:00"
    assert "openingHoursSpecification\": []" not in html.replace(" ", "")
    names = [item["name"] for item in crumbs["itemListElement"]]
    urls = [item["item"] for item in crumbs["itemListElement"]]
    assert names[0] == "Home"
    assert urls[0] == "https://site.test/"
    assert urls[1] == "https://site.test/religious-sites"
    assert urls[2] == "https://site.test/religious-sites/sample-place"
    assert "theme=" not in "".join(urls)


def test_localized_titles_and_descriptions(client, fake_wp):
    _localized_place(fake_wp)
    pages = {
        "/religious-sites/sample-place": ("en", "Church of the Virgin | VeriaGuide", "Byzantine church of the Virgin"),
        "/el/religious-sites/sample-place": ("el", "Ναός της Παναγίας | Οδηγός Βέροιας", "Βυζαντινός ναός"),
        "/de/religious-sites/sample-place": ("de", "Kirche der Jungfrau | Veria Reiseführer", "Byzantinische Kirche"),
    }
    titles = []
    for path, (lang, title, description_start) in pages.items():
        html = client.get(path).text
        document_title = _title(html)
        description = _meta(html, "description")
        titles.append(document_title)
        assert document_title == title
        assert description.startswith(description_start)
        assert "(about" not in description
        assert len(document_title) <= 60
        assert len(description) <= 155
        assert _typed(html, "PlaceOfWorship")["inLanguage"] == lang
        if lang == "el":
            assert GREEK_RE.search(document_title)
            assert GREEK_RE.search(description)
        else:
            assert not GREEK_RE.search(document_title)
            assert not GREEK_RE.search(description)
        if lang == "de":
            assert "Heilige" not in document_title
            assert "Heiliges" not in document_title
            assert "Heilige" not in description
    assert len(set(titles)) == 3


def test_german_fallback_does_not_reuse_english_or_heilige(client, fake_wp):
    post = fake_wp.posts[0]
    post["title"] = {"rendered": "Παναγία"}
    post["excerpt"] = {"rendered": "<p>Short English excerpt about the church.</p>"}
    post["acf"] = {**post["acf"], "title_de": "Heilige Panagia"}
    html = client.get("/de/museums/sample-place").text
    description = _meta(html, "description")
    assert "Short English excerpt" not in description
    assert "Heilige" not in description
    assert "Heiliges" not in description
    assert "Kirche" in description or "Museum" in description


def test_hubs_and_static_pages_have_jsonld(client):
    hub = client.get("/el/restaurants").text
    collection = _typed(hub, "CollectionPage")
    crumbs = _typed(hub, "BreadcrumbList")
    assert collection["inLanguage"] == "el"
    assert collection["url"] == "https://site.test/el/restaurants"
    assert crumbs["itemListElement"][0]["item"] == "https://site.test/el/"
    assert crumbs["itemListElement"][1]["item"] == "https://site.test/el/restaurants"

    about = client.get("/about").text
    assert _typed(about, "AboutPage")["url"] == "https://site.test/about"
    contact = client.get("/de/contact").text
    assert _typed(contact, "ContactPage")["inLanguage"] == "de"
    assert _typed(contact, "ContactPage")["url"] == "https://site.test/de/contact"
    themed = client.get("/map").text
    assert _typed(themed, "WebPage")["url"] == "https://site.test/map"


def test_empty_hub_is_noindex_and_absent_from_sitemap(client, monkeypatch):
    from app.services import content_service as content_mod
    from app.services import sitemap_service as sitemap_mod

    async def fake_posts(post_type, search=None, category=None):
        if post_type == "tour":
            return []
        return [copy.deepcopy(SAMPLE_POST)]

    monkeypatch.setattr(content_mod, "get_all_posts_for_type", fake_posts)
    monkeypatch.setattr(sitemap_mod, "get_all_posts_for_type", fake_posts)
    html = client.get("/tours").text
    assert _meta(html, "robots") == "noindex, follow"
    body = client.get("/sitemap.xml").text
    assert "<loc>https://site.test/tours</loc>" not in body
    assert "<loc>https://site.test/cafes</loc>" in body


def test_home_canonical_matches_sitemap_and_every_url_has_lastmod(client):
    home = client.get("/").text
    assert _canonical(home) == "https://site.test/"
    alternates = _hreflang(home)
    assert alternates["en"] == "https://site.test/"
    assert alternates["el"] == "https://site.test/el/"
    assert alternates["de"] == "https://site.test/de/"
    body = client.get("/sitemap.xml").text
    assert "<loc>https://site.test/</loc>" in body
    assert "<loc>https://site.test</loc>" not in body
    urls = re.findall(r"<url>(.*?)</url>", body, re.S)
    assert urls
    assert all("<lastmod>" in url for url in urls)
    for path in ("/", "/contact", "/about", "/map", "/el/", "/de/about"):
        loc = f"https://site.test{path}" if path != "/" else "https://site.test/"
        assert f"<loc>{loc}</loc>" in body


def test_known_image_dimensions_are_rendered(client, fake_wp):
    media = fake_wp.posts[0]["_embedded"]["wp:featuredmedia"][0]
    media["source_url"] = "https://cdn.test/church.jpg"
    media["media_details"] = {"width": 1200, "height": 800}
    html = client.get("/museums/sample-place").text
    assert 'width="1200"' in html
    assert 'height="800"' in html
    place = _typed(html, "Museum")
    assert place["image"] == "https://cdn.test/church.jpg"
    assert "placeholder" not in place["image"]

    zeitalter = client.get("/", params={"theme": "zeitalter"}).text
    assert 'width="1200" height="800"' in zeitalter
    hub = client.get("/religious-sites", params={"theme": "zeitalter"}).text
    assert 'width="1200" height="1702"' in hub


def test_opening_hours_parser_skips_ambiguous_lines():
    from app.utils.seo import opening_hours_specification

    specs = opening_hours_specification(
        "Monday-Friday: 9am-5pm\nSaturday: Closed\nSunday: open 24 hours\nCall ahead"
    )
    days = [item["dayOfWeek"] for item in specs]
    assert days[:5] == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    assert all(item["opens"] == "09:00" and item["closes"] == "17:00" for item in specs[:5])
    assert "Saturday" not in days
    sunday = next(item for item in specs if item["dayOfWeek"] == "Sunday")
    assert sunday["opens"] == "00:00"
    assert opening_hours_specification("ask at the door") == []
    assert opening_hours_specification({}) == []
