import json

import pytest

from app.services.submission_service import SubmissionService

# 1×1 PNG, well under the 5 MB limit.
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

DUMMY = {
    "business_name": "Dummy Taverna",
    "category": "restaurant",
    "description": "Dies ist ein Testeintrag und kein echter Betrieb. " * 2,
    "email": "dummy-test@example.com",
    "phone": "+30 23310 00000",
    "address": "Teststrasse 1",
    "city": "Veria",
    "opening_hours": "Montag bis Freitag, 9 bis 17 Uhr",
    "website": "https://example.com",
    "privacy": "on",
    "terms": "on",
}


@pytest.fixture
def submission_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(SubmissionService, "SUBMISSIONS_DIR", tmp_path)
    return tmp_path


def _post(client, data, image=TINY_PNG):
    files = {"images": ("dummy.png", image, "image/png")} if image is not None else None
    return client.post("/de/submit", data=data, files=files or {})


def test_greek_submit_page_renders(client):
    response = client.get("/el/submit")
    assert response.status_code == 200
    assert 'lang="el"' in response.text
    assert 'action="/el/submit"' in response.text
    assert "Καταχωρίστε την επιχείρησή σας στο VeriaGuide" in response.text
    assert "Στοιχεία επιχείρησης" in response.text


def test_german_submit_page_renders(client):
    response = client.get("/de/submit")
    assert response.status_code == 200
    assert 'lang="de"' in response.text
    assert 'action="/de/submit"' in response.text
    assert 'name="business_name"' in response.text
    assert "Betrieb bei VeriaGuide eintragen" in response.text
    assert "Angaben zum Betrieb" in response.text


def test_german_submit_accepts_dummy_business(client, submission_dir):
    response = _post(client, DUMMY)
    assert response.status_code == 200, response.text[:500]
    assert 'lang="de"' in response.text
    assert "Erfolgreich gesendet!" in response.text
    assert "Ihre Einreichung wurde gespeichert und wird geprüft." in response.text

    saved = list(submission_dir.glob("*.json"))
    assert len(saved) == 1
    payload = json.loads(saved[0].read_text())
    assert payload["status"] == "pending"
    assert payload["business_info"]["name"] == "Dummy Taverna"
    assert payload["business_info"]["category"] == "restaurant"
    assert payload["business_info"]["email"] == DUMMY["email"]
    assert payload["images"][0]["filename"] == "dummy.png"
    assert saved[0].stem in response.text


def test_submit_rejects_short_description(client, submission_dir):
    data = {**DUMMY, "description": "zu kurz"}
    response = _post(client, data)
    assert response.status_code == 200
    assert "Erfolgreich gesendet!" not in response.text
    assert "Die Beschreibung muss mindestens 50 Zeichen lang sein" in response.text
    assert list(submission_dir.glob("*.json")) == []
