COOKIE_KEYS = (
    "Cookie notice",
    "We use essential cookies so this site works. With your consent we also use Google Analytics to understand traffic.",
    "Accept all",
    "Essential only",
    "Learn more",
)


def test_cookie_consent_i18n_keys_exist_for_el_and_de():
    from app.i18n import UI_EL
    from app.i18n_de import UI_DE

    for key in COOKIE_KEYS:
        assert key in UI_EL, key
        assert key in UI_DE, key
        assert UI_EL[key] != key
        assert UI_DE[key] != key


def test_cookie_banner_on_en_el_de_home_without_consent(client):
    en = client.get("/").text
    assert 'id="cookie-consent"' in en
    assert "Cookie notice" in en
    assert "Accept all" in en
    assert "Essential only" in en
    assert "Learn more" in en
    assert 'href="/about"' in en
    assert "Ειδοποίηση για cookies" not in en
    assert "Cookie-Hinweis" not in en
    assert "googletagmanager.com/gtag/js" in en
    assert "if (readConsent() === '1')" in en

    el = client.get("/el/").text
    assert 'id="cookie-consent"' in el
    assert "Ειδοποίηση για cookies" in el
    assert "Αποδοχή όλων" in el
    assert "Μόνο απαραίτητα" in el
    assert "Μάθετε περισσότερα" in el
    assert 'href="/el/about"' in el
    assert "Cookie notice" not in el

    de = client.get("/de/").text
    assert 'id="cookie-consent"' in de
    assert "Cookie-Hinweis" in de
    assert "Alle akzeptieren" in de
    assert "Nur notwendige" in de
    assert "Mehr erfahren" in de
    assert 'href="/de/about"' in de
    assert "Cookie notice" not in de


def test_cookie_banner_absent_when_consent_cookie_set(client):
    client.cookies.set("cookie_consent", "1")
    for path in ("/", "/el/", "/de/"):
        html = client.get(path).text
        assert 'id="cookie-consent"' not in html
        assert "Cookie notice" not in html
        assert "Ειδοποίηση για cookies" not in html
        assert "Cookie-Hinweis" not in html


def test_cookie_banner_absent_for_essential_only_choice(client):
    client.cookies.set("cookie_consent", "essential")
    html = client.get("/").text
    assert 'id="cookie-consent"' not in html


def test_cookie_banner_on_search_contact_and_about(client):
    search = client.get("/search?q=veria")
    assert search.status_code == 200
    assert 'id="cookie-consent"' in search.text

    contact = client.get("/el/contact")
    assert contact.status_code == 200
    assert 'id="cookie-consent"' in contact.text
    assert "Ειδοποίηση για cookies" in contact.text

    about = client.get("/de/about")
    assert about.status_code == 200
    assert 'id="cookie-consent"' in about.text
    assert "Cookie-Hinweis" in about.text


def test_consent_helpers():
    from app.utils.cookie_consent import analytics_allowed, consent_choice, has_consent

    class Req:
        def __init__(self, cookies):
            self.cookies = cookies

    none = Req({})
    assert consent_choice(none) == ""
    assert has_consent(none) is False
    assert analytics_allowed(none) is False

    accepted = Req({"cookie_consent": "1"})
    assert has_consent(accepted) is True
    assert analytics_allowed(accepted) is True

    essential = Req({"cookie_consent": "essential"})
    assert has_consent(essential) is True
    assert analytics_allowed(essential) is False
