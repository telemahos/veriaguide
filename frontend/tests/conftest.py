import asyncio
import copy
import os
import sys
from pathlib import Path

import httpx
import pytest

FRONTEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FRONTEND_DIR))
os.chdir(FRONTEND_DIR)

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("WP_API_URL", "https://wp.test/wp-json/wp/v2")
os.environ.setdefault("SITE_URL", "https://site.test")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:1/0")


@pytest.fixture(autouse=True)
def _ensure_asyncio_event_loop():
    """Starlette TestClient / asyncio.run can leave the thread without a loop (3.12)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield

SAMPLE_POST = {
    "id": 1,
    "slug": "sample-place",
    "link": "https://wp.test/sample-place",
    "modified": "2026-09-01T10:00:00",
    "title": {"rendered": "Sample Place"},
    "excerpt": {"rendered": "<p>Short excerpt.</p>"},
    "content": {"rendered": "<p>Long content.</p>"},
    "acf": {
        "address": "Main Street 1, Veria",
        "location_map": {"lat": 40.52, "lng": 22.2, "address": "Main Street 1, Veria"},
        "trail_map": {"lat": 40.5, "lng": 22.1},
        "meeting_point_map": {"lat": 40.53, "lng": 22.21},
    },
    "_embedded": {"wp:featuredmedia": [{"source_url": "/static/img/placeholder.jpg"}]},
}


class FakeWordPress:
    def __init__(self):
        self.posts = [copy.deepcopy(SAMPLE_POST)]
        self.contact_status = 200
        self.requests = []

    def get(self, url, params=None, **kwargs):
        self.requests.append(("GET", url, params))
        request = httpx.Request("GET", url)
        if url.endswith("/veriaguide/v1/menus"):
            return httpx.Response(200, json=[], request=request)
        if url.endswith("/veriaguide/v1/homepage-settings"):
            return httpx.Response(200, json={}, request=request)
        if "/wp/v2/" in url:
            slug = (params or {}).get("slug")
            posts = [p for p in self.posts if p["slug"] == slug] if slug else self.posts
            headers = {"X-WP-Total": str(len(posts)), "X-WP-TotalPages": "1"}
            return httpx.Response(200, json=posts, headers=headers, request=request)
        return httpx.Response(404, json={}, request=request)

    def post(self, url, json=None, data=None, **kwargs):
        self.requests.append(("POST", url, json or data, kwargs.get("auth")))
        request = httpx.Request("POST", url)
        if url.endswith("/veriaguide/v1/contact"):
            return httpx.Response(self.contact_status, json={"success": True}, request=request)
        return httpx.Response(404, json={}, request=request)


@pytest.fixture
def fake_wp(monkeypatch):
    from app.services.cache_service import CacheService
    from app.services.http_service import HTTPService

    wp = FakeWordPress()

    async def fake_get(url, params=None, headers=None, use_wp_client=False, **kwargs):
        return wp.get(url, params=params, **kwargs)

    async def fake_post(url, data=None, json=None, headers=None, use_wp_client=False, **kwargs):
        return wp.post(url, json=json, data=data, **kwargs)

    async def cache_miss(*args, **kwargs):
        return None

    monkeypatch.setattr(HTTPService, "get", staticmethod(fake_get))
    monkeypatch.setattr(HTTPService, "post", staticmethod(fake_post))
    monkeypatch.setattr(CacheService, "get", staticmethod(cache_miss))
    monkeypatch.setattr(CacheService, "set", staticmethod(cache_miss))
    return wp


@pytest.fixture
def client(fake_wp):
    from fastapi.testclient import TestClient

    from main import app

    return TestClient(app, follow_redirects=False)
