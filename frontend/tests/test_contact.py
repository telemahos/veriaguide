import asyncio

import pytest

from app.api import wordpress


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setattr(wordpress, "WP_API_USERNAME", "api-user")
    monkeypatch.setattr(wordpress, "WP_API_PASSWORD", "app-password")


def test_contact_sends_to_wordpress(fake_wp, credentials):
    result = asyncio.run(wordpress.submit_contact_form("Maria", "maria@example.com", "Hello", "Message body"))

    assert result["success"] is True
    method, url, payload, auth = fake_wp.requests[-1]
    assert url == "https://wp.test/wp-json/veriaguide/v1/contact"
    assert payload == {"name": "Maria", "email": "maria@example.com", "subject": "Hello", "message": "Message body"}
    assert auth == ("api-user", "app-password")


def test_contact_reports_wordpress_failure(fake_wp, credentials):
    fake_wp.contact_status = 502
    result = asyncio.run(wordpress.submit_contact_form("Maria", "maria@example.com", "Hello", "Message body"))
    assert result["success"] is False


def test_contact_without_credentials_does_not_call_wordpress(fake_wp, monkeypatch):
    monkeypatch.setattr(wordpress, "WP_API_USERNAME", "")
    result = asyncio.run(wordpress.submit_contact_form("Maria", "maria@example.com", "Hello", "Message body"))
    assert result["success"] is False
    assert not fake_wp.requests


def test_contact_requires_all_fields(fake_wp, credentials):
    result = asyncio.run(wordpress.submit_contact_form("Maria", "maria@example.com", " ", "Message body"))
    assert result["success"] is False
    assert not fake_wp.requests
