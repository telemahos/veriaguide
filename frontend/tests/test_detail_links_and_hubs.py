"""Breadcrumbs, nearby listings, hub SEO and English title overrides."""
import copy
import json
import re

from tests.conftest import SAMPLE_POST

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
HUBS = {
    "accommodations": "Διαμονή στη Βέροια: ξενοδοχεία και ξενώνες | VeriaGuide",
    "hiking-trails": "Μονοπάτια στο Βέρμιο, κοντά στη Βέροια | VeriaGuide",
    "religious-sites": "Βυζαντινοί ναοί και μοναστήρια στη Βέροια | VeriaGuide",
    "archaeological-sites": "Αρχαιολογικοί χώροι σε Βέροια και Βεργίνα | VeriaGuide",
    "hidden-gems": "Κρυφές γωνιές της Βέροιας, πέρα από τα μουσεία | VeriaGuide",
    "tours": "Περιηγήσεις στη Βέροια: ναοί και Βεργίνα | VeriaGuide",
}
HUB_DESCRIPTIONS = {
    "accommodations": "Ξενοδοχεία, ξενώνες και δωμάτια στη Βέροια",
    "hiking-trails": "Μονοπάτια κοντά στη Βέροια, στο Βέρμιο",
    "religious-sites": "Βυζαντινοί ναοί και μοναστήρια στη Βέροια, κοντά στη Μπαρμπούτα",
    "archaeological-sites": "Αρχαιολογικοί χώροι σε Βέροια και Βεργίνα",
    "hidden-gems": "Πιο ήσυχες γωνιές της Βέροιας",
    "tours": "Περιηγήσεις στη Βέροια: βυζαντινοί ναοί",
}


def _title(html: str) -> str:
    match = TITLE_RE.search(html)
    assert match
    return match.group(1).replace("&amp;", "&")


def _meta(html: str, name: str) -> str:
    match = re.search(rf'<meta name="{name}" content="([^"]*)"', html)
    assert match, name
    return match.group(1)


def _graph(html: str) -> list:
    nodes = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(block)
        nodes.extend(data.get("@graph", [data]))
    return nodes


def _post(slug, title, post_type, lat, lng, photo=False, item_id=1):
    post = copy.deepcopy(SAMPLE_POST)
    post.update(id=item_id, slug=slug, type=post_type)
    post["title"] = {"rendered": title}
    post["acf"] = {
        "location_map": {"lat": lat, "lng": lng, "address": "Veria"},
        "trail_map": {"lat": lat, "lng": lng},
        "meeting_point_map": {"lat": lat, "lng": lng},
    }
    image = "https://cdn.example/photo.jpg" if photo else "/static/img/placeholder.jpg"
    post["_embedded"] = {"wp:featuredmedia": [{"source_url": image}]}
    return post


def test_detail_breadcrumb_is_visible_and_localized(client, fake_wp):
    html = client.get("/museums/sample-place").text
    assert 'class="detail-breadcrumb' in html or 'class="vg-breadcrumbs"' in html
    assert 'href="/"' in html
    assert 'href="/museums"' in html
    assert "Home" in html
    crumbs = next(node for node in _graph(html) if node.get("@type") == "BreadcrumbList")
    names = [item["name"] for item in crumbs["itemListElement"]]
    urls = [item["item"] for item in crumbs["itemListElement"]]
    assert names[0] == "Home"
    assert urls == [
        "https://site.test/",
        "https://site.test/museums",
        "https://site.test/museums/sample-place",
    ]

    greek = client.get("/el/cafes/sample-place").text
    assert 'href="/el/"' in greek
    assert 'href="/el/cafes"' in greek
    assert "Αρχική" in greek
    el_crumbs = next(node for node in _graph(greek) if node.get("@type") == "BreadcrumbList")
    assert el_crumbs["itemListElement"][0]["name"] == "Αρχική"
    assert el_crumbs["itemListElement"][1]["item"] == "https://site.test/el/cafes"

    german = client.get("/de/accommodations/sample-place").text
    assert 'href="/de/"' in german
    assert 'href="/de/accommodations"' in german
    assert "Start" in german
    assert 'href="/accommodations"' not in german.split("detail-breadcrumb", 1)[-1][:500]


def test_nearby_prefers_photos_then_orders_by_distance(client, fake_wp):
    origin = _post("sample-place", "Origin Museum", "museum", 40.52, 22.20, item_id=1)
    # Six photographed places, farther than one photoless café.
    far = []
    for index in range(6):
        far.append(_post(
            f"photo-{index}",
            f"Photo {index}",
            "cafe",
            40.52 + 0.05 + index * 0.01,
            22.20,
            photo=True,
            item_id=10 + index,
        ))
    close_plain = _post("close-plain", "Close Plain", "restaurant", 40.521, 22.20, photo=False, item_id=2)
    same_type = _post("other-museum", "Other Museum", "museum", 40.5201, 22.20, photo=True, item_id=3)
    fake_wp.posts = [origin, close_plain, same_type, *far]

    html = client.get("/museums/sample-place").text
    block = html.split('class="detail-sidebar-card mb-4 detail-nearby"', 1)[1].split("</div>", 1)[0]
    assert "Nearby" in block
    assert "Close Plain" not in block
    assert "Other Museum" not in block
    order = [slug for slug in re.findall(r'href="/cafes/([^"]+)"', block)]
    assert order == [f"photo-{index}" for index in range(6)]
    assert "More Museums" in block
    assert 'href="/museums"' in block
    distances = [float(value) for value in re.findall(r"([0-9]+\.[0-9]) km", block)]
    assert distances == sorted(distances)


def test_nearby_falls_back_to_same_category_without_coordinates(client, fake_wp):
    origin = _post("sample-place", "Origin", "hiking_trail", 40.5, 22.1, item_id=1)
    origin["acf"] = {}
    sibling_photo = _post("with-photo", "With Photo", "hiking_trail", 40.8, 22.4, photo=True, item_id=2)
    sibling_plain = _post("no-photo", "No Photo", "hiking_trail", 40.51, 22.11, photo=False, item_id=3)
    other = _post("a-cafe", "A Cafe", "cafe", 40.52, 22.2, photo=True, item_id=4)
    fake_wp.posts = [origin, sibling_plain, sibling_photo, other]

    html = client.get("/hiking-trails/sample-place").text
    block = html.split("detail-nearby", 1)[1].split("detail-nearby-more", 1)[0]
    assert "With Photo" in block
    assert "No Photo" in block
    assert "A Cafe" not in block
    assert "km" not in block
    assert block.index("With Photo") < block.index("No Photo")
    assert 'href="/hiking-trails/with-photo"' in html
    assert 'href="/hiking-trails"' in html


def test_new_hubs_have_greek_titles_guides_and_faq(client):
    for path, title in HUBS.items():
        html = client.get(f"/el/{path}").text.replace("&amp;", "&")
        assert _title(html) == title, path
        assert _title(html).count("| VeriaGuide") == 1
        assert _meta(html, "description").startswith(HUB_DESCRIPTIONS[path])
        assert "Η καταχώριση" not in html
        assert "vg-hub-guide" in html or "hub-guide" in html or "<h2>Συχνές ερωτήσεις</h2>" in html
        assert html.count("<p>") >= 2
        assert "FAQPage" in html

    german = client.get("/de/religious-sites").text
    assert "Kirche" in german or "Kloster" in german
    assert "Heilige" not in german
    assert "Heiliges" not in german
    assert _title(german).endswith("| VeriaGuide")
    assert _title(german).count("| VeriaGuide") == 1


def test_english_seo_title_and_description_override(client, fake_wp):
    post = fake_wp.posts[0]
    post["title"] = {"rendered": "Sample Place"}
    post["excerpt"] = {"rendered": "<p>Fallback excerpt about the museum.</p>"}
    post["acf"] = {
        **post["acf"],
        "seo_title": "ACF Place Name",
        "seo_description": "ACF English description of the museum in Veria.",
    }
    post["meta"] = {
        "seo_title_en": "Editor English title for the museum",
        "seo_description_en": "Editor English description that wins over the ACF text.",
    }
    html = client.get("/museums/sample-place").text
    assert _title(html) == "Editor English title for the museum | VeriaGuide"
    assert _title(html).count("| VeriaGuide") == 1
    assert _meta(html, "description").startswith("Editor English description")
    assert "ACF English description" not in _meta(html, "description")
    assert "Fallback excerpt" not in _meta(html, "description")

    post["meta"] = {}
    fallback = client.get("/restaurants/sample-place").text
    assert _title(fallback) == "ACF Place Name | VeriaGuide"
    assert _meta(fallback, "description").startswith("ACF English description")
