import json
import re
from datetime import date
from xml.etree import ElementTree

import pytest

from app.events.catalogue import Event, event_node

SLUG = "eleni-dimou-enas-dromos-tragoudia"
SITEMAP_NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "xhtml": "http://www.w3.org/1999/xhtml",
}


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


def _canonical(html: str) -> str:
    match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert match
    return match.group(1)


def _hreflang(html: str) -> dict[str, str]:
    pairs = re.findall(r'<link rel="alternate" href="([^"]+)" hreflang="([^"]+)"', html)
    return {lang: href for href, lang in pairs}


def _events(html: str) -> list[dict]:
    found = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(raw)
        if data.get("@type") == "Event":
            found.append(data)
        for node in data.get("@graph") or []:
            if isinstance(node, dict) and node.get("@type") == "Event":
                found.append(node)
    return found


@pytest.mark.parametrize("theme", ["classic", "new", "zeitalter"])
@pytest.mark.parametrize(
    "prefix,lang,name,venue,performer",
    [
        ("", "en", "Eleni Dimou: A Road of Songs", "Thanos Mikroutsikos Arts Venue, Veria", "Isidoros Pateros"),
        ("/el", "el", "Ελένη Δήμου: Ένας Δρόμος Τραγούδια", "Χώρος Τεχνών «Θάνος Μικρούτσικος», Βέροια", "Ισίδωρος Πάτερος"),
        ("/de", "de", "Eleni Dimou: Ein Weg voller Lieder", "Kunsthaus Thanos Mikroutsikos, Veria", "Isidoros Pateros"),
    ],
)
def test_event_detail_jsonld_canonical_and_hreflang(client, theme, prefix, lang, name, venue, performer):
    path = f"{prefix}/events/{SLUG}" if prefix else f"/events/{SLUG}"
    page = client.get(path, params={"theme": theme})
    assert page.status_code == 200
    html = page.text
    assert f'<html lang="{lang}"' in html
    assert f'data-lang="{lang}"' in html
    canonical = f"https://site.test{path}"
    assert _canonical(html) == canonical
    alternates = _hreflang(html)
    assert alternates["en"] == f"https://site.test/events/{SLUG}"
    assert alternates["el"] == f"https://site.test/el/events/{SLUG}"
    assert alternates["de"] == f"https://site.test/de/events/{SLUG}"
    assert alternates["x-default"] == alternates["en"]
    assert "theme" not in _canonical(html)
    assert all("theme" not in href for href in alternates.values())

    events = _events(html)
    assert len(events) == 1
    event = events[0]
    assert event["@context"] == "https://schema.org"
    assert event["name"] == name
    assert event["startDate"] == "2026-11-07T20:00:00+02:00"
    assert "endDate" not in event
    assert event["eventStatus"] == "https://schema.org/EventScheduled"
    assert event["eventAttendanceMode"] == "https://schema.org/OfflineEventAttendanceMode"
    assert event["location"]["@type"] == "Place"
    assert event["location"]["name"] == venue
    assert event["location"]["address"] == {
        "@type": "PostalAddress",
        "addressLocality": "Veria",
        "addressCountry": "GR",
    }
    assert "url" not in event["location"]
    assert event["image"] == "https://site.test/static/img/events/eleni-dimou.jpg"
    assert event["description"]
    assert event["url"] == canonical
    offer = event["offers"]
    assert offer["@type"] == "Offer"
    assert offer["price"] == 15
    assert offer["priceCurrency"] == "EUR"
    assert offer["url"] == "https://www.ticketservices.gr/event/periodeia-eleni-dimou/"
    assert "availability" not in offer
    assert "validFrom" not in offer
    names = [person["name"] for person in event["performer"]]
    assert names[0] == "Eleni Dimou"
    assert performer in names
    assert event["organizer"] == {
        "@type": "Organization",
        "name": "ARTHEMA",
        "url": "https://www.arthema.gr",
    }
    assert event["isAccessibleForFree"] is False


def test_event_jsonld_uses_athens_offset_and_omits_unknown_fields():
    summer = Event(
        slug="summer-concert",
        start=date(2026, 6, 15),
        end=date(2026, 6, 15),
        time="21:00",
        kind="concert",
        admission="ticket",
        title={"en": "Summer concert", "el": "Καλοκαιρινή", "de": "Sommerkonzert"},
        summary={"en": "An evening outdoors.", "el": "Ένα βράδυ.", "de": "Ein Abend."},
        venue={"en": "Veria", "el": "Βέροια", "de": "Veria"},
        price_from=10,
    )
    node = event_node(summer, "en")
    assert node["startDate"] == "2026-06-15T21:00:00+03:00"
    assert "endDate" not in node
    assert "image" not in node
    assert "performer" not in node
    assert "organizer" not in node
    assert node["offers"] == {"@type": "Offer", "price": 10, "priceCurrency": "EUR"}
    assert "url" not in node["offers"]
    assert "availability" not in node["offers"]
    assert "validFrom" not in node["offers"]

    feast = Event(
        slug="plain-feast",
        start=date(2026, 8, 15),
        end=date(2026, 8, 16),
        kind="religious",
        admission="free",
        cancelled=True,
        title={"en": "Feast", "el": "Γιορτή", "de": "Fest"},
        summary={"en": "A feast.", "el": "Μια γιορτή.", "de": "Ein Fest."},
        venue={"en": "Churches of Veria", "el": "Ναοί", "de": "Kirchen"},
        producer="Parish",
    )
    node = event_node(feast, "el")
    assert node["startDate"] == "2026-08-15"
    assert node["endDate"] == "2026-08-16"
    assert node["name"] == "Γιορτή"
    assert node["eventStatus"] == "https://schema.org/EventCancelled"
    assert node["isAccessibleForFree"] is True
    assert "offers" not in node
    assert "image" not in node
    assert "performer" not in node
    assert node["organizer"] == {"@type": "Organization", "name": "Parish"}
    assert "url" not in node["organizer"]


def test_sitemap_lists_event_detail_urls_in_every_language(client):
    xml = client.get("/sitemap.xml").text
    root = ElementTree.fromstring(xml)
    wanted = {
        f"https://site.test/events/{SLUG}",
        f"https://site.test/el/events/{SLUG}",
        f"https://site.test/de/events/{SLUG}",
    }
    found = {}
    for url in root.findall("sm:url", SITEMAP_NS):
        loc = url.find("sm:loc", SITEMAP_NS)
        if loc is None or loc.text not in wanted:
            continue
        lastmod = url.find("sm:lastmod", SITEMAP_NS)
        assert lastmod is not None and lastmod.text
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod.text)
        alternates = {
            link.get("hreflang"): link.get("href")
            for link in url.findall("xhtml:link", SITEMAP_NS)
        }
        assert alternates["en"] == f"https://site.test/events/{SLUG}"
        assert alternates["el"] == f"https://site.test/el/events/{SLUG}"
        assert alternates["de"] == f"https://site.test/de/events/{SLUG}"
        assert alternates["x-default"] == alternates["en"]
        found[loc.text] = lastmod.text
    assert found.keys() == wanted
    for hidden in ("theophany", "christmas-in-the-old-town", "dormition", "saints-peter-and-paul"):
        assert hidden not in xml
