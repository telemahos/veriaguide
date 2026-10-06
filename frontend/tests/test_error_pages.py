import os
import subprocess
import sys
from pathlib import Path

import pytest

FRONTEND_DIR = Path(__file__).resolve().parent.parent

FALLBACK_404 = "<h1>Error 404</h1>"


@pytest.mark.parametrize(
    "path,lang,heading",
    [
        ("/wp-cron.php", "en", "Page Not Found"),
        ("/does-not-exist", "en", "Page Not Found"),
        ("/el/wp-cron.php", "el", "Η σελίδα δεν βρέθηκε"),
        ("/el/unknown-page", "el", "Η σελίδα δεν βρέθηκε"),
        ("/de/wp-cron.php", "de", "Seite nicht gefunden"),
        ("/de/unknown-page", "de", "Seite nicht gefunden"),
    ],
)
def test_styled_404_uses_locale_and_keeps_status(client, path, lang, heading):
    response = client.get(path)
    assert response.status_code == 404
    assert "text/html" in response.headers.get("content-type", "")
    assert FALLBACK_404 not in response.text
    assert "error-container" in response.text
    assert heading in response.text
    assert f'lang="{lang}"' in response.text
    if lang == "el":
        assert 'href="/el/"' in response.text
        assert 'href="/el/restaurants"' in response.text
    elif lang == "de":
        assert 'href="/de/"' in response.text
        assert 'href="/de/restaurants"' in response.text
    else:
        assert 'href="/"' in response.text
        assert 'href="/restaurants"' in response.text


def test_api_docs_enabled_defaults(monkeypatch):
    from app.config.environments import api_docs_enabled

    monkeypatch.delenv("ENABLE_API_DOCS", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert api_docs_enabled() is False
    monkeypatch.setenv("ENVIRONMENT", "staging")
    assert api_docs_enabled() is False
    monkeypatch.setenv("ENVIRONMENT", "development")
    assert api_docs_enabled() is True
    monkeypatch.setenv("ENVIRONMENT", "testing")
    assert api_docs_enabled() is True


def test_api_docs_enabled_respects_explicit_flag(monkeypatch):
    from app.config.environments import api_docs_enabled

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ENABLE_API_DOCS", "true")
    assert api_docs_enabled() is True
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("ENABLE_API_DOCS", "false")
    assert api_docs_enabled() is False
    monkeypatch.setenv("ENABLE_API_DOCS", "0")
    assert api_docs_enabled() is False


def test_docs_routes_return_styled_404_when_flag_off():
    script = r"""
import os
import sys
from pathlib import Path

os.environ["ENVIRONMENT"] = "development"
os.environ["ENABLE_API_DOCS"] = "false"
os.environ.setdefault("WP_API_URL", "https://wp.test/wp-json/wp/v2")
os.environ.setdefault("SITE_URL", "https://site.test")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:1/0")

frontend = Path(os.environ["FRONTEND_DIR"])
sys.path.insert(0, str(frontend))
os.chdir(frontend)

from fastapi.testclient import TestClient
from main import app

assert app.docs_url is None
assert app.redoc_url is None
assert app.openapi_url is None

client = TestClient(app, follow_redirects=False)
for path in ("/docs", "/redoc", "/openapi.json"):
    response = client.get(path)
    assert response.status_code == 404, (path, response.status_code, response.text[:200])
    assert "<h1>Error 404</h1>" not in response.text
    assert "error-container" in response.text
    assert "Page Not Found" in response.text
print("ok")
"""
    env = os.environ.copy()
    env["FRONTEND_DIR"] = str(FRONTEND_DIR)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(FRONTEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout
