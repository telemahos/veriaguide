from app.utils.wp_text import (
    canonical_tag_name,
    display_wp_text,
    localize_acf_value,
    tag_label,
    translate_hours_text,
)


def test_tag_typos_canonicalize():
    assert canonical_tag_name("Archeological Site") == "Archaeological Site"
    assert canonical_tag_name("Hicking") == "Hiking"
    assert canonical_tag_name("Hiking") == "Hiking"
    assert canonical_tag_name("Archaeological Site") == "Archaeological Site"


def test_tag_labels_de_el():
    assert tag_label("Religious Site", "de") == "Kirche / Kloster"
    assert "Heilige" not in tag_label("Church", "de")
    assert "Heiliges" not in tag_label("Monastery", "de")
    assert tag_label("Church", "de") == "Kirche"
    assert tag_label("Monastery", "de") == "Kloster"
    assert tag_label("Archeological Site", "de") == "Archäologische Stätte"
    assert tag_label("Hicking", "de") == "Wandern"
    assert tag_label("Hiking", "el") == "Πεζοπορία"
    assert tag_label("Christianity", "el") == "Χριστιανισμός"
    assert tag_label("Greek Orthodox church", "de") == "Griechisch-orthodoxe Kirche"
    assert tag_label("Free", "de") == "Kostenlos"


def test_hours_translation_and_fallback():
    source = "Monday: 8:30 am–3:30 pm"
    german = translate_hours_text(source, "de")
    assert "Montag" in german
    assert "08:30" in german
    assert "15:30" in german
    assert "am" not in german.lower()
    greek = translate_hours_text("Tuesday: Closed", "el")
    assert "Τρίτη" in greek
    assert "Κλειστά" in greek
    assert translate_hours_text("Open 24 hours", "de") == "Rund um die Uhr"
    leftover = "Doors open after vespers — ask the caretaker"
    assert translate_hours_text(leftover, "de") == leftover
    assert translate_hours_text(source, "en") == source
    assert "Δευτέρα" in translate_hours_text(source, "el")


def test_localized_acf_variant_wins():
    acf = {
        "opening_hours": "Monday: 8:30 am–3:30 pm",
        "opening_hours_de": "Nur nach Vereinbarung",
    }
    assert localize_acf_value(acf, "opening_hours", "de") == "Nur nach Vereinbarung"
    assert "Δευτέρα" in localize_acf_value(acf, "opening_hours", "el")


def test_visitor_guidelines_phrases_de_el():
    phrase = "Free access without ticket"
    assert display_wp_text(phrase, "de") == "Kostenloser Eintritt ohne Ticket"
    assert display_wp_text(phrase, "el") == "Ελεύθερη είσοδος χωρίς εισιτήριο"
    assert display_wp_text(phrase, "en") == phrase
    longer = "Ask the caretaker about vespers seating"
    assert display_wp_text(longer, "de") == longer
    acf = {"visitor_guidelines": phrase}
    assert localize_acf_value(acf, "visitor_guidelines", "de") == "Kostenloser Eintritt ohne Ticket"
    assert localize_acf_value(
        {"visitor_guidelines": phrase, "visitor_guidelines_de": "Nur mit Reservierung"},
        "visitor_guidelines",
        "de",
    ) == "Nur mit Reservierung"


def test_visitor_guidelines_render_on_map_and_detail(client, fake_wp):
    fake_wp.posts[0]["acf"]["visitor_guidelines"] = "Free access without ticket"
    fake_wp.posts[0]["acf"]["location_map"] = {
        "lat": 40.52,
        "lng": 22.2,
        "address": "Main Street 1, Veria",
    }
    de_map = client.get("/de/religious-sites/map").text
    assert "Free access without ticket" not in de_map
    assert "Kostenloser Eintritt ohne Ticket" in de_map
    el_map = client.get("/el/religious-sites/map").text
    assert "Free access without ticket" not in el_map
    assert "Ελεύθερη είσοδος χωρίς εισιτήριο" in el_map
    de_detail = client.get("/de/religious-sites/sample-place").text
    assert "Kostenloser Eintritt ohne Ticket" in de_detail
    assert "Free access without ticket" not in de_detail


def test_price_and_free_display():
    assert display_wp_text("Free", "de") == "Kostenlos"
    assert display_wp_text("€€", "de") == "€€"


def test_directory_and_search_strings_de_el(client, fake_wp):
    fake_wp.posts[0]["tag_names"] = [
        "Religious Site",
        "Christianity",
        "Greek Orthodox church",
        "Archeological Site",
        "Hicking",
    ]
    fake_wp.posts[0]["_embedded"]["wp:term"] = [[
        {"taxonomy": "post_tag", "name": "Religious Site", "slug": "religious-site"},
        {"taxonomy": "post_tag", "name": "Christianity", "slug": "christianity"},
        {"taxonomy": "post_tag", "name": "Greek Orthodox church", "slug": "greek-orthodox-church"},
        {"taxonomy": "post_tag", "name": "Archeological Site", "slug": "archeological-site"},
        {"taxonomy": "post_tag", "name": "Hicking", "slug": "hicking"},
    ]]
    fake_wp.posts[0]["acf"]["opening_hours"] = "Monday: 8:30 am–3:30 pm"
    fake_wp.posts[0]["acf"]["price_range"] = "Free"
    fake_wp.posts[0]["acf"]["religious_affiliation"] = "Christianity"

    de_list = client.get("/de/religious-sites").text
    assert "directory-listing-card__tag\">Kirche / Kloster" in de_list
    assert "directory-listing-card__tag\">Religious Site" not in de_list
    assert "Kirche / Kloster" in de_list
    assert "Griechisch-orthodoxe Kirche" in de_list
    assert "Archäologische Stätte" in de_list
    assert ">Wandern<" in de_list

    el_list = client.get("/el/religious-sites").text
    assert "directory-listing-card__tag\">Θρησκευτικός χώρος" in el_list
    assert "Χριστιανισμός" in el_list or "Ελληνορθόδοξη" in el_list

    de_map = client.get("/de/religious-sites/map").text
    assert "badge bg-info" in de_map
    assert "Kirche / Kloster" in de_map
    assert "Montag" in de_map
    assert "08:30" in de_map

    de_detail = client.get("/de/religious-sites/sample-place").text
    assert "Christentum" in de_detail
    assert "Montag" in de_detail
    assert "08:30" in de_detail

    de_rest = client.get("/de/restaurants/sample-place").text
    assert "Montag" in de_rest
    assert "08:30" in de_rest
    assert "Kostenlos" in de_rest

    search = client.get("/de/search", params={"q": "Sample"}).text
    assert "Results Found" not in search
    assert "Ergebnisse gefunden" in search


def test_en_keeps_english_tags(client, fake_wp):
    fake_wp.posts[0]["_embedded"]["wp:term"] = [[
        {"taxonomy": "post_tag", "name": "Religious Site", "slug": "religious-site"},
        {"taxonomy": "post_tag", "name": "Archeological Site", "slug": "archeological-site"},
        {"taxonomy": "post_tag", "name": "Hicking", "slug": "hicking"},
    ]]
    html = client.get("/religious-sites").text
    assert ">Archaeological Site<" in html
    assert ">Hiking<" in html
    assert ">Archeological Site<" not in html
    assert ">Hicking<" not in html
