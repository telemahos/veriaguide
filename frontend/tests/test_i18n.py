def test_greek_home_uses_greek_ui_and_links(client):
    response = client.get("/el/")
    assert response.status_code == 200
    assert 'lang="el"' in response.text
    assert "Αγαπημένα" in response.text
    assert 'hreflang="el"' in response.text
    assert 'href="/el/religious-sites"' in response.text
    assert 'href="/el/contact"' in response.text


def test_english_home_stays_english(client):
    response = client.get("/")
    assert 'lang="en"' in response.text
    assert "Favorites" in response.text
    assert "Αγαπημένα" not in response.text
    assert 'href="/religious-sites"' in response.text
    assert 'aria-label="Language"' in response.text


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


def test_category_map_links_redirect_to_filtered_map(client):
    response = client.get("/el/restaurants/map")
    assert response.status_code == 301
    assert response.headers["location"] == "/el/map?type=restaurant"
    assert client.get("/map?type=restaurant").status_code == 200


def test_sitemap_lists_greek_urls(client):
    body = client.get("/sitemap.xml").text
    assert "<loc>https://site.test/el/</loc>" in body
    assert "<loc>https://site.test/el/tours/sample-place</loc>" in body
    assert 'hreflang="el"' in body
