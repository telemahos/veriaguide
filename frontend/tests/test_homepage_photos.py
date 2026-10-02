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
    assert not listing_has_photo(_item("g5", gallery="None"))
    assert not listing_has_photo(_item("g6", gallery=False))


def test_listing_has_photo_ignores_placeholder_sized_featured_media():
    item = {
        "slug": "church-icon",
        "title": {"rendered": "church-icon"},
        "acf": {},
        "_embedded": {
            "wp:featuredmedia": [{
                "source_url": "/static/img/placeholder-church.svg",
                "media_details": {
                    "sizes": {
                        "medium": {"source_url": "/static/img/placeholder-church.svg", "width": 400},
                    }
                },
            }]
        },
    }
    assert not listing_has_photo(item)


def test_listing_has_photo_ignores_wp_embed_errors():
    item = {
        "slug": "err",
        "acf": {},
        "_embedded": {"wp:featuredmedia": [{"code": "rest_forbidden", "data": {"status": 401}}]},
    }
    assert not listing_has_photo(item)


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


def test_get_category_items_sorts_photos_first_before_pagination():
    """Category listings keep photo items first (stable) so page 1 is not photo-less."""
    no_photo_a = _item("no-photo-a")
    with_photo_b = _item("with-photo-b", featured_url="https://cdn.example/b.jpg")
    no_photo_c = _item("no-photo-c")
    with_photo_d = _item("with-photo-d", gallery=[{"url": "https://cdn.example/d.jpg"}])
    placeholder = _item("placeholder", featured_url="/static/img/placeholder-default.svg")

    async def _run():
        with patch(
            "app.services.content_service.get_all_posts_for_type",
            new=AsyncMock(
                return_value=[
                    no_photo_a,
                    with_photo_b,
                    no_photo_c,
                    with_photo_d,
                    placeholder,
                ]
            ),
        ):
            return await ContentService.get_category_items("religious_site", page=1)

    result = asyncio.get_event_loop().run_until_complete(_run())
    slugs = [item["slug"] for item in result["items"]]
    assert slugs[:2] == ["with-photo-b", "with-photo-d"]
    assert slugs[2:] == ["no-photo-a", "no-photo-c", "placeholder"]
    assert result["total_count"] == 5


def test_get_category_items_sorts_photos_first_after_site_type_filter():
    """Monastery (site_type) filter must not keep WP order that starts with placeholders."""
    moutsialis = _item("moutsialis")
    moutsialis["tag_names"] = ["Christianity", "Monastery"]
    photo_monastery = _item("photo-monastery", featured_url="https://cdn.example/mon.jpg")
    photo_monastery["tag_names"] = ["Christianity", "Monastery"]
    chapel_photo = _item("chapel-photo", featured_url="https://cdn.example/chapel.jpg")
    chapel_photo["tag_names"] = ["Christianity", "Chapel"]
    placeholder_mon = _item("placeholder-mon", featured_url="/static/img/placeholder-church.svg")
    placeholder_mon["tag_names"] = ["Christianity", "Monastery"]
    gallery_mon = _item("gallery-mon", gallery=[{"url": "https://cdn.example/g.jpg"}])
    gallery_mon["tag_names"] = ["Christianity", "Monastery"]

    async def _run():
        with patch(
            "app.services.content_service.get_all_posts_for_type",
            new=AsyncMock(
                return_value=[
                    moutsialis,
                    chapel_photo,
                    placeholder_mon,
                    photo_monastery,
                    gallery_mon,
                ]
            ),
        ):
            return await ContentService.get_category_items(
                "religious_site", page=1, site_type="Monastery"
            )

    result = asyncio.get_event_loop().run_until_complete(_run())
    slugs = [item["slug"] for item in result["items"]]
    assert "chapel-photo" not in slugs
    assert slugs[:2] == ["photo-monastery", "gallery-mon"]
    assert slugs[2:] == ["moutsialis", "placeholder-mon"]
    assert result["total_count"] == 4
