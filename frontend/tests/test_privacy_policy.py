import pytest


@pytest.mark.parametrize(
    "path,marker",
    [
        ("/privacy-policy", "Privacy Policy"),
        ("/el/privacy-policy", "Πολιτική απορρήτου"),
        ("/de/privacy-policy", "Datenschutzerklärung"),
    ],
)
def test_privacy_policy_pages(client, path, marker):
    r = client.get(path)
    assert r.status_code == 200
    assert marker in r.text
    assert "https://www.googleapis.com/auth/adwords" in r.text
    assert "Limited Use" in r.text
    assert "info@veriaguide.gr" in r.text
    assert "api-services-user-data-policy" in r.text


@pytest.mark.parametrize("theme", ["classic", "new", "zeitalter"])
def test_privacy_policy_renders_in_all_themes(client, theme):
    r = client.get(f"/el/privacy-policy?theme={theme}")
    assert r.status_code == 200
    assert "Μητροπόλεως 54" in r.text
    assert 'href="/el/privacy-policy"' in r.text


@pytest.mark.parametrize(
    "path,target", [("/privacy", "/privacy-policy"), ("/el/privacy", "/el/privacy-policy"), ("/de/privacy", "/de/privacy-policy")]
)
def test_privacy_redirect(client, path, target):
    r = client.get(path, follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"].endswith(target)


def test_cookie_notice_links_to_privacy_policy(client):
    html = client.get("/?theme=classic").text
    assert 'class="cookie-consent__link" href="/cookies"' in html


def test_sitemap_lists_privacy_policy(client):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "/privacy-policy</loc>" in r.text
