def test_greek_home_hero_js_is_localized(client):
    html = client.get("/el/").text
    assert "Royal Tombs of Vergina" not in html
    assert "τους βασιλικούς τάφους της Βεργίνας" in html
    assert html.count("var defaultSubtitle") == 1


def test_german_home_hero_js_is_localized(client):
    html = client.get("/de/").text
    assert "Royal Tombs of Vergina" not in html
    assert "Königsgräber von Vergina" in html


def test_greek_hub_intros_are_expanded(client):
    cafes = client.get("/el/cafes").text
    assert "Τα καλύτερα καφέ στη Βέροια" in cafes
    assert "specialty καφέ" in cafes
    assert "πρωινός καφές" in cafes
    assert "Discover cozy cafes" not in cafes

    ski = client.get("/el/ski-resorts").text
    assert "στο Βέρμιο" in ski
    assert "3-5 Πηγάδια" in ski
    assert "Discover ski resorts and winter sports destinations near Veria" not in ski

    sites = client.get("/el/archaeological-sites").text
    assert "βασιλικοί τάφοι UNESCO" in sites
    assert "Μπαρμπούτα" in sites
    assert "Discover ancient ruins, temples and historical sites in Veria" not in sites


def test_german_hub_intros_are_expanded(client):
    html = client.get("/de/restaurants").text
    assert "Revani-Bäckereien" in html
    assert "Discover authentic Greek cuisine and dining experiences in Veria" not in html



def test_english_home_stays_english(client):
    response = client.get("/")
    assert 'lang="en"' in response.text
    assert "Favorites" in response.text
    assert "Αγαπημένα" not in response.text
    assert "Favoriten" not in response.text
    assert 'href="/religious-sites"' in response.text
    assert 'aria-label="Language"' in response.text
    assert ">DE</a>" in response.text
    assert 'hreflang="de"' in response.text


def test_german_home_uses_german_ui_and_links(client):
    response = client.get("/de/")
    assert response.status_code == 200
    assert 'lang="de"' in response.text
    assert "Favoriten" in response.text
    assert 'hreflang="de"' in response.text
    assert 'hreflang="x-default"' in response.text
    assert 'og:locale" content="de_DE"' in response.text
    assert 'href="/de/religious-sites"' in response.text
    assert 'href="/de/contact"' in response.text
    assert ">DE</a>" in response.text
    assert 'aria-label="Sprache"' in response.text


def test_german_legacy_url_keeps_language(client):
    response = client.get("/de/religious_sites")
    assert response.status_code == 301
    assert response.headers["location"] == "/de/religious-sites"


def test_german_detail_uses_stored_translation(client, fake_wp):
    fake_wp.posts[0]["meta"] = {
        "title_de": "Deutscher Titel",
        "excerpt_de": "<p>Kurzer Auszug.</p>",
        "content_de": "<p>Deutscher Text.</p>",
    }
    german = client.get("/de/tours/sample-place")
    assert german.status_code == 200
    assert "Deutscher Titel" in german.text
    english = client.get("/tours/sample-place")
    assert "Sample Place" in english.text
    assert "Deutscher Titel" not in english.text


def test_greek_legacy_url_keeps_language(client):
    response = client.get("/el/religious_sites")
    assert response.status_code == 301
    assert response.headers["location"] == "/el/religious-sites"


def test_greek_detail_uses_stored_translation(client, fake_wp):
    fake_wp.posts[0]["meta"] = {
        "title_el": "Ελληνικός τίτλος",
        "excerpt_el": "<p>Σύντομο απόσπασμα για τον χώρο.</p>",
        "content_el": "<p>Ελληνικό κείμενο.</p>",
    }
    greek = client.get("/el/tours/sample-place")
    assert greek.status_code == 200
    assert "Ελληνικός τίτλος" in greek.text
    english = client.get("/tours/sample-place")
    assert "Sample Place" in english.text
    assert "Ελληνικός τίτλος" not in english.text


def test_category_map_listing_pages(client):
    for path in ("/el/restaurants/map", "/cafes/map", "/accommodations/map", "/religious-sites/map"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "map-listings-container" in response.text
        assert "Sample Place" in response.text
    assert 'href="/el/restaurants/sample-place"' in client.get("/el/restaurants/map").text


def test_about_intro_uses_homepage_translation(client):
    """Homepage about_text is translated on /de/about and /el/about."""
    from pathlib import Path

    from app.i18n import UI_EL, tr
    from app.i18n_de import UI_DE
    from app.theme import reset_theme, set_theme
    from app.utils.helpers import HOME_ABOUT_TEXT
    from main import templates

    assert "t" in templates.env.filters

    for theme, template_name in (("classic", "about/page.html"), ("new", "v2/about/page.html")):
        token = set_theme(theme)
        try:
            loaded = templates.env.get_template("about/page.html")
        finally:
            reset_theme(token)
        assert loaded.name == template_name
        assert "t" in loaded.environment.filters
        assert "{{ about_text|t|safe }}" in Path(loaded.filename).read_text()

    key = " ".join(HOME_ABOUT_TEXT.split())
    assert key in UI_DE
    assert key in UI_EL
    assert tr(HOME_ABOUT_TEXT, "de") == UI_DE[key]
    assert tr(HOME_ABOUT_TEXT, "el") == UI_EL[key]
    assert tr(HOME_ABOUT_TEXT, "en") == HOME_ABOUT_TEXT

    german = "Entdecken Sie Veria, eine historische Stadt in Imathia"
    greek = "Ανακαλύψτε τη Βέροια, μια ιστορική πόλη στην Ημαθία"
    english = "Discover Veria (Veroia), a historic city in Imathia, northern Greece"

    en = client.get("/about").text
    assert english in en
    assert german not in en

    de = client.get("/de/about").text
    assert german in de
    assert english not in de

    el = client.get("/el/about").text
    assert greek in el
    assert english not in el

    client.cookies.set("vg_theme", "new")
    assert german in client.get("/de/about").text
    assert greek in client.get("/el/about").text
    assert english in client.get("/about").text


def test_sitemap_lists_greek_and_german_urls(client):
    body = client.get("/sitemap.xml").text
    assert "<loc>https://site.test/el/</loc>" in body
    assert "<loc>https://site.test/de/</loc>" in body
    assert "<loc>https://site.test/el/tours/sample-place</loc>" in body
    assert "<loc>https://site.test/de/tours/sample-place</loc>" in body
    assert 'hreflang="el"' in body
    assert 'hreflang="de"' in body
