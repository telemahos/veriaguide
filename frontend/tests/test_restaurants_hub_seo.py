import json
import re

import pytest

EXPECTED = {
    "": ("en", "Restaurants & Tavernas in Veria, Greece | VeriaGuide", "The best restaurants, tavernas and meze places"),
    "/el": ("el", "Εστιατόρια και ταβέρνες στη Βέροια | VeriaGuide", "Τα καλύτερα εστιατόρια, ταβέρνες και μεζεδοπωλεία της Βέροιας"),
    "/de": ("de", "Restaurants und Tavernen in Veria | VeriaGuide", "Die besten Restaurants, Tavernen und Meze-Lokale in Veria"),
}
OG = "https://site.test/static/img/og/restaurants-veria-1200x630.jpg"


def _meta(html, attr, key):
    m = re.search(rf'<meta {attr}="{re.escape(key)}" content="([^"]*)"', html)
    return m.group(1) if m else None


def _graph(html):
    nodes = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(block)
        nodes.extend(data.get("@graph", [data]))
    return nodes


@pytest.mark.parametrize("prefix", ["", "/el", "/de"])
def test_restaurants_hub_head_per_language(client, prefix):
    lang, title, desc_start = EXPECTED[prefix]
    html = client.get(f"{prefix}/restaurants").text
    assert f'<html lang="{lang}"' in html
    assert f"<title>{title}</title>" in html.replace("&amp;", "&")
    description = _meta(html, "name", "description")
    assert description.startswith(desc_start)
    assert 120 <= len(description) <= 155
    assert _meta(html, "property", "og:image") == OG
    assert _meta(html, "name", "twitter:image") == OG
    assert _meta(html, "property", "og:image:width") == "1200"
    assert _meta(html, "property", "og:image:height") == "630"
    assert _meta(html, "property", "og:image:alt")
    assert f'<link rel="canonical" href="https://site.test{prefix}/restaurants">' in html
    for code, path in (("en", ""), ("el", "/el"), ("de", "/de"), ("x-default", "")):
        assert f'<link rel="alternate" href="https://site.test{path}/restaurants" hreflang="{code}">' in html


def test_restaurants_hub_has_item_list_and_hero_alt(client):
    html = client.get("/el/restaurants").text
    page = next(n for n in _graph(html) if n.get("@type") == "CollectionPage")
    assert page["inLanguage"] == "el"
    assert page["primaryImageOfPage"]["url"] == OG
    item_list = page["mainEntity"]
    assert item_list["@type"] == "ItemList"
    assert item_list["itemListElement"], "expected listings in ItemList"
    first = item_list["itemListElement"][0]
    assert first["position"] == 1
    assert first["url"].startswith("https://site.test/el/restaurants/")
    hero = client.get("/el/restaurants", params={"theme": "zeitalter"}).text
    assert re.search(r'class="zt-pagehead-img"[^>]*alt="[^"]+"', hero)


def test_og_image_is_served(client):
    response = client.get("/static/img/og/restaurants-veria-1200x630.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
