"""Anonymous usage counts for finished AI plans. Raw IP addresses are never stored."""
import hashlib
import hmac
import os
from collections import Counter
from datetime import UTC, datetime

from fastapi import Request

from app.ai_guide.models import WizardState
from app.ai_guide.store import get_store

STATS_KEY = "stats:events"
STATS_TTL = 400 * 86400
MAX_EVENTS = 2000

_BOTS = ("bot", "spider", "crawl", "slurp", "wget", "curl", "python", "httpclient", "headless", "scrap")


def is_bot(request: Request) -> bool:
    ua = (request.headers.get("user-agent") or "").strip().lower()
    if not ua:
        return True
    return any(token in ua for token in _BOTS)


def visitor_code(ip: str) -> str:
    secret = os.getenv("SECRET_KEY") or os.getenv("ADMIN_API_KEY") or "veriaguide"
    digest = hmac.new(secret.encode(), ip.encode(), hashlib.sha256).hexdigest()
    return digest[:8].upper()


def country_code(request: Request) -> str:
    for header in ("CF-IPCountry", "CloudFront-Viewer-Country", "X-Country-Code"):
        value = (request.headers.get(header) or "").strip().upper()
        if len(value) == 2 and value.isalpha() and value != "XX":
            return value
    return ""


async def record_plan(request: Request, ip: str, state: WizardState, lang: str) -> None:
    event = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "visitor": visitor_code(ip),
        "country": country_code(request),
        "lang": lang if lang in ("en", "el", "de") else "en",
        "days": max(1, state.days),
        "party": state.party or "",
        "interests": list(state.interests),
        "budget": state.budget or "",
        "has_wishes": bool((state.wishes or "").strip()),
    }
    store = get_store()
    events = await store.get(STATS_KEY) or []
    if not isinstance(events, list):
        events = []
    events.append(event)
    await store.set(STATS_KEY, events[-MAX_EVENTS:], STATS_TTL)


def summarize(events: list[dict]) -> dict:
    visitors = Counter(event.get("visitor") or "?" for event in events)
    countries = Counter(event.get("country") or "—" for event in events)
    parties = Counter(event.get("party") or "—" for event in events)
    budgets = Counter(event.get("budget") or "—" for event in events)
    langs = Counter(event.get("lang") or "—" for event in events)
    day_lengths = Counter(str(event.get("days") or "—") for event in events)
    interests = Counter()
    for event in events:
        for interest in event.get("interests") or []:
            interests[interest] += 1
        if not event.get("interests"):
            interests["—"] += 1
    repeats = [
        {"visitor": code, "count": count, "country": _country_for(events, code), "last": _last_for(events, code)}
        for code, count in visitors.most_common()
    ]
    return {
        "plans": len(events),
        "people": len(visitors),
        "with_wishes": sum(1 for event in events if event.get("has_wishes")),
        "countries": countries.most_common(),
        "parties": parties.most_common(),
        "budgets": budgets.most_common(),
        "langs": langs.most_common(),
        "days": sorted(day_lengths.items(), key=lambda item: item[0]),
        "interests": interests.most_common(),
        "repeats": repeats,
        "latest": list(reversed(events[-30:])),
    }


def _country_for(events: list[dict], code: str) -> str:
    for event in reversed(events):
        if event.get("visitor") == code and event.get("country"):
            return event["country"]
    return "—"


def _last_for(events: list[dict], code: str) -> str:
    for event in reversed(events):
        if event.get("visitor") == code:
            return (event.get("ts") or "")[:16].replace("T", " ")
    return ""
