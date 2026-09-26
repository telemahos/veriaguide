"""Road line for a day's stops, and nearby replacement options."""
import math

import httpx

from app.utils.logging_config import get_logger

logger = get_logger("ai_guide")

OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{coords}"
DAY_COLORS = ("#c8863a", "#1a4182", "#2d5a4a", "#8b1e1e", "#5b3b6b", "#3b4f6b", "#a66d2e")


def _distance_km(a: dict, b: dict) -> float:
    if not (a.get("lat") and a.get("lng") and b.get("lat") and b.get("lng")):
        return 999.0
    radius = 6371.0
    lat1, lat2 = math.radians(float(a["lat"])), math.radians(float(b["lat"]))
    dlat = lat2 - lat1
    dlng = math.radians(float(b["lng"]) - float(a["lng"]))
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def alternatives(current: dict, pool: dict, used_ids: set[int], limit: int = 5) -> list[dict]:
    """Three to five replacements: same category first, then the nearest other places."""
    options = []
    for venue in pool.values():
        if not isinstance(venue, dict) or venue.get("id") == current.get("id"):
            continue
        if venue.get("id") in used_ids and venue.get("category") != current.get("category"):
            continue
        distance = _distance_km(current, venue)
        same = venue.get("category") == current.get("category")
        options.append((0 if same else 1, distance, venue))
    options.sort(key=lambda item: (item[0], item[1]))
    picked = []
    for _rank, distance, venue in options:
        if len(picked) >= limit:
            break
        item = dict(venue)
        item["distance_km"] = round(distance, 1)
        item["same_kind"] = venue.get("category") == current.get("category")
        picked.append(item)
    if len(picked) < 3:
        for _rank, distance, venue in options:
            if any(existing["id"] == venue["id"] for existing in picked):
                continue
            item = dict(venue)
            item["distance_km"] = round(distance, 1)
            item["same_kind"] = venue.get("category") == current.get("category")
            picked.append(item)
            if len(picked) >= limit:
                break
    return picked[:limit]


async def road_line(points: list[list[float]]) -> list[list[float]]:
    """Driving line through [lat, lng] points. Falls back to straight segments."""
    if len(points) < 2:
        return points
    coords = ";".join(f"{point[1]},{point[0]}" for point in points)
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.get(
                OSRM_URL.format(coords=coords),
                params={"overview": "full", "geometries": "geojson"},
            )
            response.raise_for_status()
            geometry = response.json()["routes"][0]["geometry"]["coordinates"]
            return [[pair[1], pair[0]] for pair in geometry]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning(f"Route line fallback: {exc}")
        return points


def ordered_stops(itinerary: dict, venues: dict) -> list[dict]:
    stops = []
    number = 1
    for day in itinerary.get("days") or []:
        for slot in day.get("slots") or []:
            venue = venues.get(str(slot.get("venue_id")))
            if not venue or venue.get("lat") is None or venue.get("lng") is None:
                continue
            stops.append(
                {
                    "n": number,
                    "day": day.get("day"),
                    "time": slot.get("time") or "",
                    "name": venue.get("name") or "",
                    "url": venue.get("url") or "",
                    "lat": float(venue["lat"]),
                    "lng": float(venue["lng"]),
                }
            )
            number += 1
    return stops


async def route_for_itinerary(itinerary: dict, venues: dict) -> dict:
    stops = ordered_stops(itinerary, venues)
    days = []
    by_day: dict[int, list[dict]] = {}
    for stop in stops:
        by_day.setdefault(int(stop["day"] or 1), []).append(stop)
    for index, (day, day_stops) in enumerate(by_day.items()):
        points = [[stop["lat"], stop["lng"]] for stop in day_stops]
        days.append(
            {
                "day": day,
                "color": DAY_COLORS[index % len(DAY_COLORS)],
                "stops": day_stops,
                "line": await road_line(points),
            }
        )
    return {"days": days}
