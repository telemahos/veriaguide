import json

from app.i18n import set_lang
from app.utils.helpers import generate_homepage_schema


def test_listing_detail_trailing_slash_301(client):
    response = client.get("/cafes/sample-place/")
    assert response.status_code == 301
    assert response.headers["location"] == "/cafes/sample-place"

    greek = client.get("/el/cafes/sample-place/")
    assert greek.status_code == 301
    assert greek.headers["location"] == "/el/cafes/sample-place"


def test_hub_trailing_slash_301_matches_canonical(client):
    response = client.get("/cafes/")
    assert response.status_code == 301
    assert response.headers["location"] == "/cafes"
    canonical_page = client.get("/cafes")
    assert canonical_page.status_code == 200
    assert 'rel="canonical" href="https://site.test/cafes"' in canonical_page.text


def test_locale_home_keeps_trailing_slash(client):
    assert client.get("/el/").status_code == 200
    assert client.get("/de/").status_code == 200


def test_legacy_churches_redirect_when_slug_exists(client, fake_wp):
    church = fake_wp.posts[0]
    church["wp_slug"] = "holy-church-of-saint-basil-a-byzantine-church-in-veria"
    church["slug"] = "holy-church-of-saint-basil-a-byzantine-church-in-veria"

    response = client.get("/churches/holy-church-of-saint-basil")
    assert response.status_code == 301
    assert response.headers["location"] == "/religious-sites/holy-church-of-saint-basil"

    long_slug = client.get(
        "/el/monasteries/holy-church-of-saint-basil-a-byzantine-church-in-veria"
    )
    assert long_slug.status_code == 301
    assert long_slug.headers["location"] == "/el/religious-sites/holy-church-of-saint-basil"

    hub = client.get("/churches")
    assert hub.status_code == 301
    assert hub.headers["location"] == "/religious-sites"


def test_unknown_legacy_church_is_404(client):
    assert client.get("/churches/not-a-real-place").status_code == 404
    assert client.get("/de/monasteries/missing-slug").status_code == 404


def test_homepage_jsonld_is_localized():
    from app.i18n import reset_lang

    token = set_lang("en")
    try:
        en = json.loads(generate_homepage_schema())
        website = en["@graph"][0]
        assert website["inLanguage"] == "en"
        assert website["potentialAction"]["target"].endswith("/search?q={search_term_string}")

        set_lang("el")
        el = json.loads(generate_homepage_schema())
        website = el["@graph"][0]
        assert website["inLanguage"] == "el"
        assert "/el/search?q={search_term_string}" in website["potentialAction"]["target"]
        assert website["description"] != en["@graph"][0]["description"]

        set_lang("de")
        de = json.loads(generate_homepage_schema())
        website = de["@graph"][0]
        assert website["inLanguage"] == "de"
        assert "/de/search?q={search_term_string}" in website["potentialAction"]["target"]
    finally:
        reset_lang(token)


def test_homepage_meta_matches_what_to_see_queries(client):
    """EN/EL/DE homepages serve the CTR-focused title and description once."""
    expected = {
        "/": (
            "Veria Greece: What to See – Churches, Vergina & Museums | VeriaGuide",
            "What to see in Veria (Veroia), Greece: Byzantine churches, Vergina Royal Tombs, museums, maps and a free AI day planner for Imathia.",
        ),
        "/el/": (
            "Βέροια: Τι να δεις – ναοί, Βεργίνα και μουσεία | VeriaGuide",
            "Τι να δεις στη Βέροια (Veroia): βυζαντινοί ναοί, βασιλικοί τάφοι Βεργίνας, μουσεία, χάρτης και δωρεάν AI σχεδιασμός ημέρας στην Ημαθία.",
        ),
        "/de/": (
            "Veria: Sehenswürdigkeiten – Kirchen, Vergina und Museen | VeriaGuide",
            "Was man in Veria (Veroia) sehen sollte: byzantinische Kirchen, Königsgräber von Vergina, Museen, Karte und kostenloser KI-Tagesplaner für Imathia.",
        ),
    }
    retired = (
        "Veria Greece Travel Guide – Churches, Museums & Vergina",
        "Plan your trip to Veria (Veroia), Imathia, Greece",
        "Ταξιδιωτικός οδηγός Βέροιας – ναοί, μουσεία και Βεργίνα",
        "Reiseführer Veria – Kirchen, Museen und Vergina",
    )
    for path, (title, description) in expected.items():
        html = client.get(path).text
        assert f"<title>{title}</title>" in html
        assert f'<meta name="description" content="{description}">' in html
        assert f'<meta property="og:title" content="{title}">' in html
        assert f'<meta property="og:description" content="{description}">' in html
        assert "| VeriaGuide | VeriaGuide" not in html
        for old in retired:
            assert old not in html
        schema = json.loads(html.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0])
        assert schema["@graph"][0]["description"] == description
        assert schema["@graph"][2]["description"] == description


def test_homepage_html_jsonld_uses_locale_search(client):
    html = client.get("/el/").text
    assert '"inLanguage": "el"' in html
    assert "/el/search?q={search_term_string}" in html
    assert "Plan my trip" not in html
