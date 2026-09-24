import pytest
from fastapi import HTTPException

from app.utils.validation import InputValidator


def test_email_validation():
    assert InputValidator.validate_email("guest@example.com")
    assert not InputValidator.validate_email("not-an-email")


def test_slug_validation():
    assert InputValidator.validate_slug("agios-nikolaos")
    assert not InputValidator.validate_slug("../etc/passwd")


def test_search_query_rejects_empty():
    with pytest.raises(HTTPException) as exc:
        InputValidator.validate_search_query("   ")
    assert exc.value.status_code == 400


def test_search_query_rejects_too_long():
    with pytest.raises(HTTPException):
        InputValidator.validate_search_query("a" * 5000)


def test_contact_form_valid():
    data = InputValidator.validate_contact_form("Maria", "maria@example.com", "Hello", "A proper message text.")
    assert data["email"] == "maria@example.com"


def test_contact_form_invalid_email():
    with pytest.raises(HTTPException) as exc:
        InputValidator.validate_contact_form("Maria", "broken", "Hello", "A proper message text.")
    assert exc.value.status_code == 400


def test_sanitize_html_strips_script():
    assert "<script" not in InputValidator.sanitize_html("<script>alert(1)</script>hi")
