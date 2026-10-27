"""GA4 click events fire only with analytics consent and carry listing params."""
import json
import re
import subprocess
from pathlib import Path

import pytest

JS = Path(__file__).resolve().parents[1] / "static" / "js" / "ga-events.js"


def _classify(cases: list[dict]) -> list[str]:
    script = JS.read_text()
    program = script + """
const cases = JSON.parse(process.argv[1]);
const out = cases.map((item) => {
  const link = {
    href: item.href,
    textContent: item.text || "",
    className: item.className || "",
    getAttribute(name) {
      if (name === "href") return item.href;
      if (name === "data-ga") return item.dataGa || "";
      return "";
    }
  };
  return globalThis.vgClassifyGaClick(link, item.host || "veriaguide.gr");
});
process.stdout.write(JSON.stringify(out));
"""
    result = subprocess.run(
        ["node", "-e", program, json.dumps(cases)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_detail_page_exposes_listing_params_and_website_marker(client, fake_wp):
    post = fake_wp.posts[0]
    post["title"] = {"rendered": "Church of the Virgin"}
    post["acf"] = {
        **post["acf"],
        "phone": "+30 23310 12345",
        "email": "church@example.gr",
        "website": "https://church.example.gr",
    }
    html = client.get("/el/religious-sites/sample-place").text
    assert 'data-lang="el"' in html
    assert 'data-listing-type="religious_site"' in html
    assert 'data-listing-slug="sample-place"' in html
    assert 'data-listing-title="Church of the Virgin"' in html
    assert 'href="tel:+30 23310 12345"' in html
    assert 'href="mailto:church@example.gr"' in html
    assert 'data-ga="website"' in html
    assert "https://www.google.com/maps/dir/" in html
    assert 'src="/static/js/ga-events.js?v=20261027a"' in html
    assert "G-KHZEWGNX7J" in html
    assert "if (readConsent() === '1')" in html

    home = client.get("/").text
    assert 'data-lang="en"' in home
    assert "data-listing-type" not in home
    assert 'src="/static/js/ga-events.js?v=20261027a"' in home


def test_click_classifier_and_consent_gate():
    names = _classify([
        {"href": "tel:+302331012345", "text": "Call"},
        {"href": "mailto:church@example.gr", "text": "Email"},
        {"href": "https://www.google.com/maps/dir/?api=1&destination=40,22", "text": "Get Directions"},
        {"href": "https://www.openstreetmap.org/directions?from=&to=40,22", "text": "Route"},
        {"href": "#", "text": "Οδηγίες"},
        {"href": "/map", "text": "Map"},
        {"href": "/el/hiking-trails/map", "text": "Show on map"},
        {"href": "#map", "text": "Show on map"},
        {"href": "https://church.example.gr", "text": "https://church.example.gr", "dataGa": "website"},
        {"href": "https://commons.wikimedia.org/wiki/File:Veria.jpg", "text": "Photo"},
        {"href": "/religious-sites", "text": "Churches"},
        {"href": "https://veriaguide.gr/about", "text": "About"},
        {"href": "https://www.ticketservices.gr/event/periodeia-eleni-dimou/", "text": "Tickets · from 15 €", "dataGa": "tickets"},
        {"href": "/events/eleni-dimou-enas-dromos-tragoudia", "text": "About the evening", "dataGa": "event_details"},
        {"href": "/el/events/eleni-dimou-enas-dromos-tragoudia", "text": "Για τη βραδιά", "dataGa": "event_details"},
        {"href": "/de/events/eleni-dimou-enas-dromos-tragoudia", "text": "Zum Abend", "dataGa": "event_details"},
        {"href": "https://www.ticketservices.gr/event/periodeia-eleni-dimou/", "text": "Αγορά εισιτηρίων"},
    ])
    assert names == [
        "click_phone",
        "click_email",
        "click_directions",
        "click_directions",
        "click_directions",
        "click_map",
        "click_map",
        "click_map",
        "click_website",
        "click_outbound",
        "",
        "",
        "click_tickets",
        "click_event_details",
        "click_event_details",
        "click_event_details",
        "click_outbound",
    ]

    gate = subprocess.run(
        [
            "node", "-e",
            JS.read_text() + """
const checks = [
  globalThis.vgShouldSendGa("veriaguide.gr", "1", true),
  globalThis.vgShouldSendGa("veriaguide.gr", "essential", true),
  globalThis.vgShouldSendGa("veriaguide.gr", "", true),
  globalThis.vgShouldSendGa("veriaguide.gr", "1", false),
  globalThis.vgShouldSendGa("localhost", "1", true),
  globalThis.vgShouldSendGa("127.0.0.1", "1", true)
];
process.stdout.write(JSON.stringify(checks));
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(gate.stdout) == [True, False, False, False, False, False]


def test_event_clicks_send_event_params_once():
    """A ticket link is click_tickets only — not also click_outbound — and only with consent."""
    script = JS.read_text() + r"""
const calls = [];
globalThis.gtag = function () { calls.push(Array.prototype.slice.call(arguments)); };
globalThis.location = { hostname: "veriaguide.gr" };
globalThis.document = {
  cookie: "cookie_consent=1",
  body: { getAttribute(name) { return name === "data-lang" ? "el" : ""; } }
};
function link(attrs, href) {
  return {
    href: href,
    textContent: attrs["data-event-title"] || "",
    className: "",
    getAttribute(name) { return attrs[name] || (name === "href" ? href : ""); }
  };
}
const tickets = link({
  "data-ga": "tickets",
  "data-event-title": "Ελένη Δήμου: Ένας Δρόμος Τραγούδια",
  "data-event-slug": "eleni-dimou-enas-dromos-tragoudia",
  "data-event-date": "2026-11-07",
  "data-ga-placement": "event_detail"
}, "https://www.ticketservices.gr/event/periodeia-eleni-dimou/");
const details = link({
  "data-ga": "event_details",
  "data-event-title": "Eleni Dimou: A Road of Songs",
  "data-event-slug": "eleni-dimou-enas-dromos-tragoudia",
  "data-event-date": "2026-11-07",
  "data-ga-placement": "events_hero"
}, "https://veriaguide.gr/events/eleni-dimou-enas-dromos-tragoudia");
function fire(node) {
  globalThis.vgOnGaClick({ target: { closest: () => node } });
}
fire(tickets);
globalThis.location = { hostname: "localhost" };
fire(tickets);
globalThis.location = { hostname: "127.0.0.1" };
fire(tickets);
globalThis.location = { hostname: "veriaguide.gr" };
globalThis.document.cookie = "cookie_consent=essential";
fire(tickets);
globalThis.document.cookie = "cookie_consent=1";
fire(details);
process.stdout.write(JSON.stringify(calls));
"""
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    calls = json.loads(result.stdout)
    assert len(calls) == 2
    assert calls[0][0] == "event"
    assert calls[0][1] == "click_tickets"
    assert calls[0][2] == {
        "event_title": "Ελένη Δήμου: Ένας Δρόμος Τραγούδια",
        "event_slug": "eleni-dimou-enas-dromos-tragoudia",
        "event_date": "2026-11-07",
        "lang": "el",
        "link_url": "https://www.ticketservices.gr/event/periodeia-eleni-dimou/",
        "placement": "event_detail",
    }
    assert calls[1][1] == "click_event_details"
    assert calls[1][2]["placement"] == "events_hero"
    assert calls[1][2]["lang"] == "el"
    assert "listing_slug" not in calls[0][2]
    assert all(call[1] != "click_outbound" for call in calls)


SLUG = "eleni-dimou-enas-dromos-tragoudia"
TICKET_URL = "https://www.ticketservices.gr/event/periodeia-eleni-dimou/"
TITLES = {
    "": "Eleni Dimou: A Road of Songs",
    "/el": "Ελένη Δήμου: Ένας Δρόμος Τραγούδια",
    "/de": "Eleni Dimou: Ein Weg voller Lieder",
}


def _anchors(html: str, href: str) -> list[str]:
    return re.findall(r"<a\b[^>]*href=\"" + re.escape(href) + r"\"[^>]*>", html)


def _assert_event_attrs(tag: str, kind: str, placement: str, title: str) -> None:
    assert f'data-ga="{kind}"' in tag
    assert f'data-ga-placement="{placement}"' in tag
    assert f'data-event-slug="{SLUG}"' in tag
    assert 'data-event-date="2026-11-07"' in tag
    assert f'data-event-title="{title}"' in tag


@pytest.mark.parametrize("theme", ["classic", "new", "zeitalter"])
@pytest.mark.parametrize("prefix", ["", "/el", "/de"])
def test_event_detail_tickets_are_marked(client, theme, prefix):
    html = client.get(f"{prefix}/events/{SLUG}", params={"theme": theme}).text
    tags = _anchors(html, TICKET_URL)
    assert len(tags) == 1
    _assert_event_attrs(tags[0], "tickets", "event_detail", TITLES[prefix])
    assert 'data-lang="' + {"/el": "el", "/de": "de"}.get(prefix, "en") + '"' in html


@pytest.mark.parametrize("prefix,label", [("", "About the evening"), ("/el", "Για τη βραδιά"), ("/de", "Zum Abend")])
def test_featured_event_details_link_is_marked(client, prefix, label):
    events = client.get(f"{prefix}/events" if prefix else "/events", params={"theme": "zeitalter"}).text
    home = client.get(f"{prefix}/" if prefix else "/", params={"theme": "zeitalter"}).text
    for html, placement in ((events, "events_hero"), (home, "home")):
        match = re.search(rf'<a class="zt-link" href="[^"]+"[^>]*>{re.escape(label)}</a>', html)
        assert match, (prefix, placement)
        _assert_event_attrs(match.group(0), "event_details", placement, TITLES[prefix])
        tickets = _anchors(html, TICKET_URL)
        assert tickets
        _assert_event_attrs(tickets[0], "tickets", placement, TITLES[prefix])


def test_event_cards_and_lists_mark_detail_clicks(client):
    classic_home = client.get("/", params={"theme": "classic"}).text
    home_title = _anchors(classic_home, f"/events/{SLUG}")
    assert home_title
    _assert_event_attrs(home_title[0], "event_details", "home", TITLES[""])

    classic_list = client.get("/de/events", params={"theme": "new"}).text
    listed = _anchors(classic_list, f"/de/events/{SLUG}")
    assert listed
    _assert_event_attrs(listed[0], "event_details", "event_list", TITLES["/de"])
