def test_events_hub_lists_upcoming_and_hides_past_from_the_top(client):
    html = client.get("/events").text
    assert "Christmas in the old town" in html
    assert "Theophany" in html
    upcoming = html.split("Past events")[0]
    assert "Dormition of the Virgin" not in upcoming
    assert "Dormition of the Virgin" in html
    assert '"@type": "Event"' in html


def test_events_are_translated(client):
    greek = client.get("/el/events").text
    assert "Χριστούγεννα στην παλιά πόλη" in greek
    assert 'href="/el/events/christmas-in-the-old-town"' in greek
    german = client.get("/de/events").text
    assert "Weihnachten in der Altstadt" in german


def test_event_detail_and_missing_slug(client):
    page = client.get("/events/theophany")
    assert page.status_code == 200
    assert "The blessing of the waters" in page.text
    missing = client.get("/events/not-a-real-date")
    assert missing.status_code == 404


def test_home_and_nav_link_to_events(client):
    html = client.get("/").text
    assert 'href="/events"' in html
    assert "Eleni Dimou" in html
    assert "Christmas in the old town" in html


def test_old_guides_events_points_at_the_hub(client):
    response = client.get("/guides/events", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/events"


def test_sitemap_lists_the_hub(client):
    xml = client.get("/sitemap.xml").text
    assert "/events</loc>" in xml
    assert "/events/theophany</loc>" in xml
