def test_events_hub_lists_only_the_concert(client):
    html = client.get("/events").text
    assert "Eleni Dimou" in html
    assert "Christmas in the old town" not in html
    assert "Dormition of the Virgin" not in html
    assert '"@type": "Event"' in html
    assert '"priceCurrency": "EUR"' in html


def test_events_are_translated(client):
    greek = client.get("/el/events").text
    assert "Ελένη Δήμου" in greek
    assert 'href="/el/events/eleni-dimou-enas-dromos-tragoudia"' in greek
    german = client.get("/de/events").text
    assert "Ein Weg voller Lieder" in german


def test_event_detail_has_the_full_text(client):
    page = client.get("/el/events/eleni-dimou-enas-dromos-tragoudia")
    assert page.status_code == 200
    assert "Ο Χώρος Τεχνών της Βέροιας" in page.text
    assert "Ισίδωρος Πάτερος" in page.text
    assert "/static/img/events/eleni-dimou.jpg" in page.text


def test_hidden_events_are_gone(client):
    assert client.get("/events/theophany").status_code == 404
    assert client.get("/events/not-a-real-date").status_code == 404


def test_zeitalter_pages_show_the_poster(client):
    for path in ("/?theme=zeitalter", "/events?theme=zeitalter", "/events/eleni-dimou-enas-dromos-tragoudia?theme=zeitalter"):
        html = client.get(path).text
        assert "eleni-dimou-905.webp" in html, path
    detail = client.get("/el/events/eleni-dimou-enas-dromos-tragoudia?theme=zeitalter").text
    assert "Σάββατο 7 Νοεμβρίου 2026" in detail
    assert "από 15 €" in detail


def test_home_and_nav_link_to_events(client):
    html = client.get("/").text
    assert 'href="/events"' in html
    assert "Eleni Dimou" in html
    assert "Christmas in the old town" not in html


def test_old_guides_events_points_at_the_hub(client):
    response = client.get("/guides/events", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/events"


def test_sitemap_lists_the_hub(client):
    xml = client.get("/sitemap.xml").text
    assert "/events</loc>" in xml
    assert "/events/eleni-dimou-enas-dromos-tragoudia</loc>" in xml
    assert "/events/theophany</loc>" not in xml
