"""Document titles use | VeriaGuide in every locale, and never twice."""
from app.utils.seo import compose_document_title


def test_compose_uses_veriaguide_for_every_locale():
    assert compose_document_title("Ναός της Παναγίας", "el") == "Ναός της Παναγίας | VeriaGuide"
    assert compose_document_title("Kirche der Jungfrau", "de") == "Kirche der Jungfrau | VeriaGuide"
    assert compose_document_title("Church of the Virgin", "en") == "Church of the Virgin | VeriaGuide"
    assert "Οδηγός Βέροιας" not in compose_document_title("Ναός", "el")
    assert "Reiseführer" not in compose_document_title("Kirche", "de")


def test_compose_does_not_suffix_a_branded_title_twice():
    branded = "Αρχαιολογικό Μουσείο Βέροιας | VeriaGuide"
    assert compose_document_title(branded, "el") == branded
    assert compose_document_title("Barbouta: Jüdisches Viertel von Veria | VeriaGuide", "de") == (
        "Barbouta: Jüdisches Viertel von Veria | VeriaGuide"
    )


def test_listing_override_ending_in_veriaguide_is_not_doubled(client, fake_wp):
    post = fake_wp.posts[0]
    post["meta"] = {"seo_title_el": "Μπαρμπούτα: η εβραϊκή συνοικία | VeriaGuide"}
    html = client.get("/el/religious-sites/sample-place").text
    assert "<title>Μπαρμπούτα: η εβραϊκή συνοικία | VeriaGuide</title>" in html
    assert "VeriaGuide | VeriaGuide" not in html
