"""GA4 click events fire only with analytics consent and carry listing params."""
import json
import subprocess
from pathlib import Path

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
    assert 'src="/static/js/ga-events.js?v=20261026a"' in html
    assert "G-KHZEWGNX7J" in html
    assert "if (readConsent() === '1')" in html

    home = client.get("/").text
    assert 'data-lang="en"' in home
    assert "data-listing-type" not in home
    assert 'src="/static/js/ga-events.js?v=20261026a"' in home


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
