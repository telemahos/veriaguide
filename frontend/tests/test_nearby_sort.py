"""Equal distances must not make sorted() compare listing dicts."""
import asyncio

from app.services.content_service import ContentService


def test_nearby_items_with_the_same_distance_sort_by_slug(monkeypatch):
    async def fake_locations():
        return [
            {"id": 2, "slug": "beta-place", "title": "Beta", "type": "museum", "lat": 40.52, "lng": 22.20},
            {"id": 3, "slug": "alpha-place", "title": "Alpha", "type": "museum", "lat": 40.52, "lng": 22.20},
        ]

    monkeypatch.setattr("app.services.content_service.get_all_locations", fake_locations)
    items = asyncio.get_event_loop().run_until_complete(
        ContentService.get_nearby_items({"lat": 40.52, "lng": 22.20}, "origin-place", current_id=1)
    )
    assert [item["slug"] for item in items] == ["alpha-place", "beta-place"]
    assert items[0]["distance_km"] == items[1]["distance_km"]
