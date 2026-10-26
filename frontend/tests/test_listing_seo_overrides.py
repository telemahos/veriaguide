"""Per-listing EL/DE SEO title and description overrides."""
import re
from pathlib import Path

from app.utils.seo import listing_description, listing_meta, place_name

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
PLUGIN = Path(__file__).resolve().parents[2] / "wordpress" / "veriaguide-cpt.php"
LONG_EL_TITLE = "Ναός της Παναγίας στη Βέροια: πλήρης τίτλος από τον συντάκτη χωρίς κατάληξη"


def _meta(html: str, name: str) -> str:
    match = re.search(rf'<meta name="{name}" content="([^"]*)"', html)
    assert match, name
    return match.group(1)


def _property(html: str, name: str) -> str:
    match = re.search(rf'<meta property="{name}" content="([^"]*)"', html)
    assert match, name
    return match.group(1)


def _title(html: str) -> str:
    match = TITLE_RE.search(html)
    assert match
    return match.group(1)


def _place(fake_wp):
    post = fake_wp.posts[0]
    post["title"] = {"rendered": "Παναγία της Βέροιας"}
    post["excerpt"] = {"rendered": "<p>English excerpt that EL and DE must not reuse.</p>"}
    post["acf"] = {
        **post["acf"],
        "title_el": "Ναός της Παναγίας",
        "title_de": "Kirche der Jungfrau",
        "excerpt_el": "Απόσπασμα που δεν χρησιμοποιείται.",
        "excerpt_de": "Auszug, der nicht verwendet wird.",
        "seo_title": "Virgin Church",
        "seo_description": "Editor English description of the Virgin Church in Veria.",
    }
    post["meta"] = {
        "seo_title_el": LONG_EL_TITLE,
        "seo_description_el": ["Ειδική περιγραφή του ναού από τον συντάκτη, όχι το απόσπασμα."],
        "seo_title_de": "Kirche der Jungfrau | eigener Titel",
        "seo_description_de": "Eigene Beschreibung der Kirche, nicht der Auszug.",
    }
    return post


def test_locale_overrides_are_full_titles_and_beat_excerpts(client, fake_wp):
    assert len(LONG_EL_TITLE) > 60
    _place(fake_wp)

    greek = client.get("/el/religious-sites/sample-place").text
    assert _title(greek) == LONG_EL_TITLE
    assert _property(greek, "og:title") == LONG_EL_TITLE
    assert "Οδηγός Βέροιας" not in _title(greek)
    assert _meta(greek, "description").startswith("Ειδική περιγραφή του ναού")
    assert _property(greek, "og:description") == _meta(greek, "description")
    assert "Απόσπασμα που δεν χρησιμοποιείται" not in greek.split("<h1", 1)[0]
    assert '"name": "Ναός της Παναγίας"' in greek

    german = client.get("/de/religious-sites/sample-place").text
    assert _title(german) == "Kirche der Jungfrau | eigener Titel"
    assert _property(german, "og:title") == "Kirche der Jungfrau | eigener Titel"
    assert "Veria Reiseführer" not in _title(german)
    assert _meta(german, "description").startswith("Eigene Beschreibung der Kirche")
    assert "Auszug, der nicht verwendet wird" not in _meta(german, "description")

    english = client.get("/religious-sites/sample-place").text
    assert _title(english) == "Virgin Church | VeriaGuide"
    assert _property(english, "og:title") == "Virgin Church | VeriaGuide"
    assert _meta(english, "description").startswith("Editor English description")
    assert "English excerpt" not in _meta(english, "description")
    assert LONG_EL_TITLE not in _title(english)


def test_blank_locale_title_keeps_the_composed_title(client, fake_wp):
    post = _place(fake_wp)
    post["meta"]["seo_title_el"] = "   "
    post["meta"]["seo_description_el"] = ""
    html = client.get("/el/religious-sites/sample-place").text
    assert _title(html) == "Ναός της Παναγίας | Οδηγός Βέροιας"
    assert _meta(html, "description").startswith("Απόσπασμα που δεν χρησιμοποιείται")


def test_listing_meta_does_not_treat_locale_titles_as_place_names():
    item = {
        "title": {"rendered": "Παναγία"},
        "acf": {"title_el": "Ναός", "excerpt_el": "Απόσπασμα ναού στη Βέροια."},
        "meta": {"seo_title_el": "Πλήρης τίτλος | Οδηγός"},
    }
    title, description, name, verbatim = listing_meta(item, "el", "religious_site")
    assert verbatim is True
    assert title == "Πλήρης τίτλος | Οδηγός"
    assert name == "Ναός"
    assert description.startswith("Απόσπασμα")
    assert place_name(item, "en") != "Πλήρης τίτλος | Οδηγός"

    item["meta"]["seo_description_de"] = "Eigene Beschreibung ohne Auszug."
    item["acf"]["excerpt_de"] = "Auszug der Kirche."
    text = listing_description(item, "de", "Kirche", "museum")
    assert text == "Eigene Beschreibung ohne Auszug."


def test_plugin_registers_locale_seo_meta_for_editors():
    source = PLUGIN.read_text()
    block = source.split("function register_translation_meta", 1)[1].split("function register_custom_routes", 1)[0]
    for key in ("seo_title_el", "seo_title_de", "seo_description_el", "seo_description_de"):
        assert f"'{key}'" in block
    for post_type in (
        "religious_site", "museum", "archaeological_site", "hiking_trail",
        "restaurant", "cafe", "accommodation", "ski_resort", "tour", "hidden_gem",
    ):
        assert f"'{post_type}'" in block
    assert "'type' => 'string'" in block
    assert "'single' => true" in block
    assert "'show_in_rest' => true" in block
    assert "current_user_can('edit_posts')" in block
