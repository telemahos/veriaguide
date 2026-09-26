"""Pick a small, relevant set of WordPress listings for the prompt."""
import asyncio
import html
import re

from app.ai_guide.interests import EXCLUDED, categories_for
from app.ai_guide.models import WizardState
from app.api.wordpress import get_all_posts_for_type
from app.config import POST_TYPES
from app.i18n import lang_prefix
from app.utils.category_urls import get_category_url_path
from app.utils.helpers import strip_tags

HOURS_FIELDS = ("opening_hours", "operating_hours", "service_times", "estimated_time", "best_time_to_visit")
BUDGET_WORDS = {"low": ("€", "cheap", "budget", "free"), "high": ("€€€", "luxury", "fine", "premium")}
PRIORITY_CATEGORIES = {"religious_sites": 3.0, "archaeological_sites": 2.0, "museums": 1.5, "cafes": 1.5}
FAST_FOOD = ("fast food", "fast-food", "burger", "pizza", "snack", "kebab", "gyros", "street food")
LANDMARKS = (
    "vergina", "aigai", "aegae", "royal tomb", "βασιλικ",
    "apostle", "αποστόλ", "αποστολ", "βήμα", "βημα",
    "metropolis", "μητρόπολ", "μητροπολ",
    "resurrection", "ανάστασ", "αναστασ",
    "barbouta", "μπαρμπούτ", "μπαρμπουτ", "synagogue", "συναγωγ",
    "byzantine museum", "βυζαντινό μουσείο", "βυζαντινο μουσειο",
    "archaeological museum", "αρχαιολογικό μουσείο", "αρχαιολογικο μουσειο",
)
WORD_RE = re.compile(r"\w{3,}", re.UNICODE)


def _text(value) -> str:
    if isinstance(value, dict):
        value = value.get("rendered", "")
    return html.unescape(strip_tags(str(value or ""))).strip()


def _short(value, limit: int) -> str:
    text = " ".join(_text(value).split())
    return text[:limit].rstrip()


def _coords(acf: dict) -> tuple[float, float] | None:
    for field in ("location_map", "trail_map", "meeting_point_map"):
        point = acf.get(field)
        if isinstance(point, dict) and point.get("lat") and point.get("lng"):
            try:
                return float(point["lat"]), float(point["lng"])
            except (TypeError, ValueError):
                continue
    return None


def _acf_text(acf: dict) -> str:
    return " ".join(str(v) for v in acf.values() if isinstance(v, (str, int, float)))


def _image(post: dict) -> str:
    media = (post.get("_embedded") or {}).get("wp:featuredmedia") or []
    if media and isinstance(media[0], dict):
        sizes = (media[0].get("media_details") or {}).get("sizes") or {}
        for size in ("medium_large", "medium", "large"):
            if isinstance(sizes.get(size), dict) and sizes[size].get("source_url"):
                return sizes[size]["source_url"]
        return media[0].get("source_url") or ""
    return ""


def to_venue(post: dict, category: str) -> dict:
    acf = post.get("acf") if isinstance(post.get("acf"), dict) else {}
    coords = _coords(acf)
    hours = next((_short(acf[f], 160) for f in HOURS_FIELDS if acf.get(f)), "")
    return {
        "id": int(post["id"]),
        "name": _short(post.get("title"), 120),
        "category": category,
        "url": f"{lang_prefix()}/{get_category_url_path(category)}/{post.get('slug', '')}",
        "summary": _short(post.get("excerpt"), 480),
        "address": _short(acf.get("address", ""), 80),
        "hours": hours,
        "price": _short(acf.get("price_range", ""), 20),
        "city": _short(acf.get("city", ""), 60),
        "tags": [str(t) for t in (post.get("tag_names") or [])][:6],
        "lat": coords[0] if coords else None,
        "lng": coords[1] if coords else None,
        "image": _image(post),
    }


def score(post: dict, category: str, keywords: set[str], state: WizardState) -> float:
    acf = post.get("acf") if isinstance(post.get("acf"), dict) else {}
    haystack = " ".join(
        [_text(post.get("title")), _text(post.get("excerpt")), _acf_text(acf), " ".join(post.get("tag_names") or [])]
    ).lower()
    total = sum(2.0 if kw in _text(post.get("title")).lower() else 1.0 for kw in keywords if kw in haystack)
    total += PRIORITY_CATEGORIES.get(category, 0.0)
    if any(name in haystack for name in LANDMARKS):
        total += 20.0
    if state.budget != "low" and any(word in haystack for word in FAST_FOOD):
        total -= 8.0
    for word in BUDGET_WORDS.get(state.budget or "", ()):
        if word in haystack:
            total += 0.5
    if _coords(acf):
        total += 0.25
    return total


def keywords_for(state: WizardState) -> set[str]:
    words = {w.lower() for w in WORD_RE.findall(state.wishes or "")}
    words.update(state.interests)
    return words


async def retrieve(state: WizardState, limit: int) -> list[dict]:
    categories = [c for c in categories_for(state.interests) if c not in EXCLUDED]
    if "cafes" in POST_TYPES and "cafes" not in categories:
        categories.append("cafes")
    if state.days > 1 and "accommodations" in POST_TYPES and "accommodations" not in categories:
        categories.append("accommodations")
    results = await asyncio.gather(
        *(get_all_posts_for_type(POST_TYPES[c]) for c in categories), return_exceptions=True
    )
    keywords = keywords_for(state)
    buckets: dict[str, list[tuple[float, dict]]] = {}
    for category, posts in zip(categories, results, strict=True):
        if isinstance(posts, BaseException) or not posts:
            continue
        ranked = []
        for post in posts:
            if not isinstance(post, dict) or not post.get("id") or post.get("type") == "tour":
                continue
            ranked.append((score(post, category, keywords, state), to_venue(post, category)))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        buckets[category] = ranked

    # Round-robin across categories. Churches get a second pick so one chapel cannot stand for the old town.
    church_heavy = "churches" in state.interests or "heritage" in state.interests
    picked: list[dict] = []
    seen: set[int] = set()
    while len(picked) < limit and any(buckets.values()):
        for category in list(buckets):
            takes = 2 if church_heavy and category == "religious_sites" else 1
            for _pick in range(takes):
                if not buckets.get(category) or len(picked) >= limit:
                    break
                venue = buckets[category].pop(0)[1]
                if venue["id"] not in seen:
                    seen.add(venue["id"])
                    picked.append(venue)
    return picked
