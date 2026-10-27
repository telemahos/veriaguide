"""GSC report 16.10.2026: legal pages, guide 301s, empty maps, search placeholder."""
import re

import pytest

HREF_RE = re.compile(r"""href=(["'])([^"']+)\1""")


def _canonical(html: str) -> str:
    match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert match
    return match.group(1)


def test_cookies_page_stays_live(client):
    for prefix in ("", "/el", "/de"):
        response = client.get(f"{prefix}/cookies")
        assert response.status_code == 200
        assert "cookie_consent" in response.text
        assert "info@veriaguide.gr" in response.text
        assert "Μητροπόλεως" not in response.text
        assert '"@type": "WebPage"' in response.text
    assert "vg_theme" in client.get("/de/cookies").text
    assert "Google Analytics" in client.get("/de/cookies").text
    assert "απαραίτητα cookies" in client.get("/el/cookies").text


@pytest.mark.parametrize("prefix,target", [("", "/about"), ("/el", "/el/about"), ("/de", "/de/about")])
@pytest.mark.parametrize("path", ["/terms", "/imprint"])
def test_imprint_and_terms_redirect_until_the_flag_is_on(client, prefix, target, path):
    response = client.get(f"{prefix}{path}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == target


def test_hidden_legal_pages_are_absent_from_footer_and_sitemap(client):
    sitemap = client.get("/sitemap.xml").text
    assert "/cookies</loc>" in sitemap
    assert "/terms</loc>" not in sitemap
    assert "/imprint</loc>" not in sitemap
    for theme in ("classic", "new", "zeitalter"):
        html = client.get("/de/", params={"theme": theme}).text
        assert 'href="/de/cookies"' in html
        assert 'href="/de/privacy-policy"' in html
        assert 'href="/de/terms"' not in html
        assert 'href="/de/imprint"' not in html


def test_imprint_and_terms_render_when_the_flag_is_on(client, monkeypatch):
    monkeypatch.setenv("SHOW_IMPRINT_AND_TERMS", "true")
    for path, marker in (("/terms", "TODO (Kostas)"), ("/el/imprint", "Στοιχεία εκδότη"), ("/de/terms", "Nutzungsbedingungen")):
        response = client.get(path)
        assert response.status_code == 200
        assert marker in response.text
        assert "info@veriaguide.gr" in response.text
    html = client.get("/", params={"theme": "new"}).text
    assert 'href="/terms"' in html
    assert 'href="/imprint"' in html
    sitemap = client.get("/sitemap.xml").text
    assert "/terms</loc>" in sitemap
    assert "/imprint</loc>" in sitemap


def test_privacy_still_redirects_and_footer_links_cookies(client):
    response = client.get("/privacy", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/privacy-policy"
    html = client.get("/de/", params={"theme": "classic"}).text
    for href in ("/de/privacy-policy", "/de/cookies"):
        assert f'href="{href}"' in html


@pytest.mark.parametrize(
    "path,target",
    [
        ("/guides/thessaloniki-airport", "/about"),
        ("/el/guides/thessaloniki-airport", "/el/about"),
        ("/de/guides/imathia-weekend", "/de/about"),
        ("/guides/events", "/events"),
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
