"""One fixed walking day: every old-town church, from the Vema, with coffee and a meal."""
import asyncio
from datetime import datetime, timedelta

from app.ai_guide.models import Itinerary, ItineraryDay, Slot
from app.ai_guide.retrieval import FAST_FOOD, REVANI_VERIA, to_venue
from app.ai_guide.routing import _distance_km
from app.api.wordpress import get_all_posts_for_type

OLD_TOWN_KM = 4.0
START_HINTS = ("vema", "bema", "βήμα", "βημα", "βήματος", "βηματος")
STAY_MINUTES = {"church": 15, "cafe": 30, "meal": 80}
NOTES = {
    "start": "Start here, where Apostle Paul preached. Then walk from church to church.",
    "church": "A short visit, about 15 minutes.",
    "cafe": "Coffee break on the way.",
    "revani": "The original Veria revani, beside Agios Antonios.",
    "meal": "Sit down for a meal, then continue to the next church.",
}


def _is_start(venue: dict) -> bool:
    """The Vema (Step) of Apostle Paul, not a church that only mentions Paul."""
    name = (venue.get("name") or "").lower()
    if any(hint in name for hint in START_HINTS):
        return True
    return "step" in name and "apostle" in name


def _is_fast_food(venue: dict) -> bool:
    name = (venue.get("name") or "").lower()
    return any(word in name for word in FAST_FOOD)


def _venues(posts, category: str, wp_type: str) -> list[dict]:
    if isinstance(posts, BaseException) or not isinstance(posts, list):
        return []
    found = []
    for post in posts:
        if not isinstance(post, dict) or not post.get("id"):
            continue
        if post.get("type") not in (None, "", wp_type):
            continue
        venue = to_venue(post, category)
        if venue.get("lat") is None or venue.get("lng") is None:
            continue
        found.append(venue)
    return found


def order_churches(churches: list[dict]) -> list[dict]:
    """Nearest-neighbour walk from the Vema, only churches in the old town."""
    pinned = [church for church in churches if church.get("lat") is not None and _is_start(church)]
    if not pinned:
        return []
    start = pinned[0]
    pool = [
        church
        for church in churches
        if church["id"] != start["id"] and _distance_km(start, church) <= OLD_TOWN_KM
    ]
    ordered = [start]
    while pool:
        nxt = min(pool, key=lambda church: _distance_km(ordered[-1], church))
        pool.remove(nxt)
        ordered.append(nxt)
    return ordered


def _nearest(origin: dict, options: list[dict], used: set[int], limit_km: float) -> dict | None:
    choices = [
        venue
        for venue in options
        if venue["id"] not in used and not _is_fast_food(venue) and _distance_km(origin, venue) <= limit_km
    ]
    if not choices:
        return None
    return min(choices, key=lambda venue: _distance_km(origin, venue))


def _insert_after(sequence: list[tuple[str, dict]], church_id: int, kind: str, venue: dict) -> None:
    for index, (current_kind, current) in enumerate(sequence):
        if current_kind == "church" and current["id"] == church_id:
            sequence.insert(index + 1, (kind, venue))
            return


def with_breaks(churches: list[dict], cafes: list[dict], restaurants: list[dict]) -> list[tuple[str, dict]]:
    sequence = [("church", church) for church in churches]
    if not sequence:
        return []
    used = {church["id"] for church in churches}
    revani = REVANI_VERIA
    if revani["id"] not in used:
        host = min(churches, key=lambda church: _distance_km(church, revani))
        _insert_after(sequence, host["id"], "cafe", revani)
        used.add(revani["id"])

    def church_at(fraction: float) -> dict:
        church_only = [venue for kind, venue in sequence if kind == "church"]
        return church_only[min(len(church_only) - 1, int(len(church_only) * fraction))]

    meal = _nearest(church_at(0.45), restaurants, used, 4.0)
    if meal:
        _insert_after(sequence, church_at(0.45)["id"], "meal", meal)
        used.add(meal["id"])
    extra_cafe = _nearest(church_at(0.75), cafes, used, 4.0)
    if extra_cafe:
        _insert_after(sequence, church_at(0.75)["id"], "cafe", extra_cafe)
    return sequence


def build_itinerary(sequence: list[tuple[str, dict]]) -> Itinerary:
    cursor = datetime(2000, 1, 1, 9, 0)
    slots: list[Slot] = []
    previous = None
    first_church = True
    for kind, venue in sequence:
        if previous and previous.get("lat") is not None and venue.get("lat") is not None:
            walk = max(4, int(round(_distance_km(previous, venue) / 4 * 60)))
            cursor += timedelta(minutes=walk)
        if kind == "church" and first_church:
            note = NOTES["start"]
            first_church = False
        elif kind == "cafe" and venue["id"] == REVANI_VERIA["id"]:
            note = NOTES["revani"]
        else:
            note = NOTES[kind]
        slots.append(Slot(time=cursor.strftime("%H:%M"), venue_id=int(venue["id"]), note=note))
        cursor += timedelta(minutes=STAY_MINUTES[kind])
        previous = venue
    return Itinerary(
        title="All the churches of Veria",
        summary=(
            "One walking day that starts at the Vema of Apostle Paul and visits every old-town church, "
            "with coffee and a meal along the way. Each church is a short stop."
        ),
        days=[ItineraryDay(day=1, title="From church to church", slots=slots)],
    )


async def load_church_day() -> tuple[Itinerary, list[dict]] | None:
    religious, cafes, restaurants = await asyncio.gather(
        get_all_posts_for_type("religious_site"),
        get_all_posts_for_type("cafe"),
        get_all_posts_for_type("restaurant"),
        return_exceptions=True,
    )
    churches = order_churches(_venues(religious, "religious_sites", "religious_site"))
    if not churches:
        return None
    cafe_venues = _venues(cafes, "cafes", "cafe")
    meal_venues = _venues(restaurants, "restaurants", "restaurant")
    sequence = with_breaks(churches, cafe_venues, meal_venues)
    venues = [venue for _kind, venue in sequence]
    return build_itinerary(sequence), venues
