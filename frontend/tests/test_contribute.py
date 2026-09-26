import json

import pytest

from app.services.contribution_service import ContributionService

DUMMY = {
    "listing_id": "1",
    "listing_category": "religious_site",
    "email": "dummy-test@example.com",
    "name": "Dummy Tester",
    "description": "Dies ist ein Testbeitrag und keine echte Bewertung.",
    "privacy": "on",
}


@pytest.fixture
def contribution_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ContributionService, "CONTRIBUTIONS_DIR", tmp_path)
    return tmp_path


def test_greek_contribute_page_renders(client):
    response = client.get("/el/contribute")
    assert response.status_code == 200
    assert 'lang="el"' in response.text
    assert 'action="/el/contribute"' in response.text
    assert "Μοιραστείτε περιεχόμενο" in response.text
    assert "Φόρμα συνεισφοράς" in response.text


def test_german_contribute_page_renders(client):
    response = client.get("/de/contribute")
    assert response.status_code == 200
    assert 'lang="de"' in response.text
    assert 'action="/de/contribute"' in response.text
    assert 'name="listing_id"' in response.text
    assert "Inhalte teilen" in response.text
    assert "Beitragsformular" in response.text


def test_german_contribute_accepts_dummy_description(client, contribution_dir):
    response = client.post(
        "/de/contribute",
        data={
            **DUMMY,
            "contribution_types": "description",
        },
    )
    assert response.status_code == 200
    assert 'lang="de"' in response.text
    assert "Erfolgreich gesendet!" in response.text
    assert "Ihr Beitrag wurde gesendet und wird geprüft." in response.text

    saved = list(contribution_dir.glob("*.json"))
    assert len(saved) == 1
    payload = json.loads(saved[0].read_text())
    assert payload["status"] == "pending"
    assert payload["listing_info"] == {"listing_id": "1", "category": "religious_site"}
    assert payload["contributor"]["email"] == DUMMY["email"]
    assert payload["contributor"]["name"] == DUMMY["name"]
    assert payload["content"]["description"] == DUMMY["description"]
    assert payload["contribution_types"] == ["description"]
    assert saved[0].stem in response.text


def test_contribute_rejects_missing_consent(client, contribution_dir):
    data = {**DUMMY, "contribution_types": "description"}
    del data["privacy"]
    response = client.post("/de/contribute", data=data)
    assert response.status_code == 200
    assert "Erfolgreich gesendet!" not in response.text
    assert "Sie müssen den Bedingungen zustimmen" in response.text
    assert list(contribution_dir.glob("*.json")) == []
