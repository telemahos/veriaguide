"""Homepage featured cards must only include listings with photos."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.services.content_service import ContentService
from app.utils.helpers import listing_has_photo


def _item(slug: str, *, featured_url=None, gallery=None, is_featured=False):
    item = {
        "slug": slug,
        "title": {"rendered": slug},
        "acf": {},
    }
    if featured_url:
        item["_embedded"] = {
            "wp:featuredmedia": [{"source_url": featured_url}]
        }
    if gallery is not None:
        item["acf"]["photo_gallery"] = gallery
    if is_featured:
        item["acf"]["is_featured"] = ["Is Featured"]
    return item


def test_listing_has_photo_featured_image():
    assert listing_has_photo(_item("a", featured_url="https://cdn.example/a.jpg"))
    assert not listing_has_photo(_item("b", featured_url="/static/img/placeholder-default.svg"))
    assert not listing_has_photo(_item("c"))


def test_listing_has_photo_gallery():
    assert listing_has_photo(
        _item("g", gallery=[{"url": "https://cdn.example/g1.jpg"}])
    )
    assert listing_has_photo(_item("g2", gallery=["https://cdn.example/g2.jpg"]))
    assert not listing_has_photo(_item("g3", gallery=[]))
    assert not listing_has_photo(
        _item("g4", gallery=[{"url": "/static/img/placeholder-museum.svg"}])
    )


def test_get_featured_items_excludes_no_photo():
    with_photo = _item("with", featured_url="https://cdn.example/ok.jpg", is_featured=True)
    no_photo = _item("without", is_featured=True)
    gallery_only = _item(
        "gallery",
        gallery=[{"source_url": "https://cdn.example/gal.jpg"}],
    )
    sections = [
        {
            "category": "religious_sites",
            "post_type": "religious_site",
            "items_count": 4,
        }
    ]

    async def _run():
        with patch(
            "app.services.content_service.get_all_posts_for_type",
            new=AsyncMock(return_value=[no_photo, with_photo, gallery_only]),
        ):
            return await ContentService.get_featured_items(sections)

    result = asyncio.get_event_loop().run_until_complete(_run())
    slugs = [item["slug"] for item in result["religious_sites"]]
    assert "without" not in slugs
    assert "with" in slugs
    assert "gallery" in slugs
    # Featured+photo comes first
    assert slugs[0] == "with"
