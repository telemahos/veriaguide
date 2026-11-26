"""?lang=el|de|en is a 301 to the clean locale path, not a self-canonical page."""
import pytest

from app.middleware.canonical_urls import lang_query_redirect


@pytest.mark.parametrize(
    "path,query,location",
    [
        ("/restaurants", "lang=el", "/el/restaurants"),
        ("/", "lang=de", "/de/"),
        ("/cafes", "lang=en", "/cafes"),
        ("/el/cafes", "lang=en", "/cafes"),
        ("/el/ski-resorts", "lang=de", "/de/ski-resorts"),
        ("/de/", "lang=el", "/el/"),
        ("/restaurants", "lang=el&page=2", "/el/restaurants?page=2"),
        ("/map", "type=cafe&lang=de", "/de/map?type=cafe"),
        ("/restaurants/", "lang=el", "/el/restaurants"),
    ],
)
def test_lang_query_redirect_targets(path, query, location):
    assert lang_query_redirect(path, query) == location


def test_lang_query_redirect_ignores_api_and_other_values():
    assert lang_query_redirect("/api/search/autocomplete", "q=bema&lang=el") is None
    assert lang_query_redirect("/restaurants", "lang=fr") is None
    assert lang_query_redirect("/restaurants", "page=2") is None
    assert lang_query_redirect("/el/restaurants", "") is None


def test_lang_query_is_a_single_301(client):
    response = client.get("/restaurants", params={"lang": "el", "page": "2"}, follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/el/restaurants?page=2"

    home = client.get("/", params={"lang": "de"}, follow_redirects=False)
    assert home.status_code == 301
    assert home.headers["location"] == "/de/"

    english = client.get("/el/cafes", params={"lang": "en"}, follow_redirects=False)
    assert english.status_code == 301
    assert english.headers["location"] == "/cafes"

    clean = client.get("/el/restaurants", follow_redirects=False)
    assert clean.status_code == 200
    assert 'rel="canonical" href="https://site.test/el/restaurants"' in clean.text
    assert "lang=el" not in clean.text.split("</head>", 1)[0]


def test_api_lang_param_is_not_redirected(client, fake_wp):
    response = client.get("/api/search/autocomplete", params={"q": "Church", "lang": "en"}, follow_redirects=False)
    assert response.status_code == 200
