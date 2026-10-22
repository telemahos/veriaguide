"""GSC report 16.10.2026: legal pages, guide 301s, empty maps, search placeholder."""
import re

import pytest

HREF_RE = re.compile(r"""href=(["'])([^"']+)\1""")


def _canonical(html: str) -> str:
    match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert match
    return match.group(1)


@pytest.mark.parametrize("prefix", ["", "/el", "/de"])
@pytest.mark.parametrize(
    "path,marker",
    [
        ("/cookies", "cookie_consent"),
        ("/terms", "TODO (Kostas)"),
        ("/imprint", "TODO (Kostas)"),
    ],
)
def test_legal_pages_exist_in_every_locale(client, prefix, path, marker):
    response = client.get(f"{prefix}{path}")
    assert response.status_code == 200
    assert marker in response.text
    assert "info@veriaguide.gr" in response.text
    assert "Μητροπόλεως" not in response.text
    assert '"@type": "WebPage"' in response.text


def test_legal_copy_is_localized(client):
    assert "Όροι χρήσης" in client.get("/el/terms").text
    assert "Nutzungsbedingungen" in client.get("/de/terms").text
    assert "Στοιχεία εκδότη" in client.get("/el/imprint").text
    assert "Impressum" in client.get("/de/imprint").text
    cookies = client.get("/de/cookies").text
    assert "vg_theme" in cookies
    assert "Google Analytics" in cookies
    greek = client.get("/el/cookies").text
    assert "απαραίτητα cookies" in greek


def test_privacy_still_redirects_and_footer_links_legal_pages(client):
    response = client.get("/privacy", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/privacy-policy"
    html = client.get("/de/", params={"theme": "classic"}).text
    for href in ("/de/privacy-policy", "/de/cookies", "/de/terms", "/de/imprint"):
        assert f'href="{href}"' in html
    assert "/cookies</loc>" in client.get("/sitemap.xml").text
    assert "/terms</loc>" in client.get("/sitemap.xml").text
    assert "/imprint</loc>" in client.get("/sitemap.xml").text


@pytest.mark.parametrize(
    "path,target",
    [
        ("/guides/thessaloniki-airport", "/about"),
        ("/el/guides/thessaloniki-airport", "/el/about"),
        ("/de/guides/imathia-weekend", "/de/about"),
        ("/guides/events", "/about"),
        ("/de/guides/not-a-published-guide", "/de/about"),
        ("/archaeological_sites", "/archaeological-sites"),
        ("/archaeological-sites/", "/archaeological-sites"),
        ("/el/archaeological_sites/", "/el/archaeological-sites"),
    ],
)
def test_gsc_soft_404_and_guide_urls_are_single_hop(client, path, target):
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == target
    assert client.get(target).status_code == 200


def test_rendered_pages_do_not_link_to_guides_or_the_search_placeholder(client):
    homes = {"/", "/el/", "/de/"}
    pages = ["/", "/el/", "/de/", "/about", "/contact", "/religious-sites", "/hiking-trails", "/search?q=veria"]
    for path in pages:
        html = client.get(path).text
        hrefs = [href for _quote, href in HREF_RE.findall(html)]
        for href in hrefs:
            assert "{search_term_string}" not in href, (path, href)
            path_only = href.split("?", 1)[0]
            assert "/guides/" not in path_only and not path_only.rstrip("/").endswith("/guides"), (path, href)
        if path not in homes:
            assert "{search_term_string}" not in html, path


def test_search_action_url_template_is_only_on_the_home_page(client):
    home = client.get("/").text
    assert '"urlTemplate": "https://site.test/search?q={search_term_string}"' in home
    assert '"@type": "EntryPoint"' in home
    about = client.get("/about").text
    assert "urlTemplate" not in about
    assert "{search_term_string}" not in about


@pytest.mark.parametrize(
    "path,location",
    [
        ("/search?q={search_term_string}", "/search"),
        ("/map?q={search_term_string}&type=cafes", "/map?type=cafes"),
        ("/el/map?q=%7Bsearch_term_string%7D", "/el/map"),
        ("/cafes?page=1", "/cafes"),
        ("/el/restaurants?page=1&theme=new", "/el/restaurants?theme=new"),
    ],
)
def test_placeholder_and_page_one_redirect_once(client, path, location):
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == location


def test_map_and_page_canonicals(client):
    cafes = client.get("/cafes")
    assert cafes.status_code == 200
    assert _canonical(cafes.text) == "https://site.test/cafes"

    mapped = client.get("/map", params={"q": "veria", "type": "cafes"})
    assert mapped.status_code == 200
    assert _canonical(mapped.text) == "https://site.test/map?q=veria&amp;type=cafes"
    assert "Showing locations for" in mapped.text

    typed = client.get("/de/map", params={"type": "cafes"})
    assert _canonical(typed.text) == "https://site.test/de/map?type=cafes"

    search = client.get("/search", params={"q": "veria", "page": "2"})
    assert _canonical(search.text) == "https://site.test/search?q=veria&amp;page=2"
