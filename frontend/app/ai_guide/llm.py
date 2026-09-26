"""Single OpenRouter call returning a validated itinerary."""
import json
import re
from collections.abc import Awaitable, Callable

import httpx

from app.ai_guide import config
from app.ai_guide.models import Itinerary
from app.utils.logging_config import get_logger

logger = get_logger("ai_guide")

Completer = Callable[[list[dict]], Awaitable[str]]


class ItineraryError(Exception):
    pass


async def openrouter_complete(messages: list[dict]) -> str:
    key = config.api_key()
    if not key:
        raise ItineraryError("OPENROUTER_API_KEY is not set")
    payload = {
        "model": config.model(),
        "messages": messages,
        "max_tokens": config.max_tokens(),
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://veriaguide.gr",
        "X-Title": "VeriaGuide AI Guide",
    }
    try:
        async with httpx.AsyncClient(timeout=config.timeout()) as client:
            response = await client.post(config.OPENROUTER_URL, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"] or ""
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise ItineraryError(f"OpenRouter request failed: {exc}") from exc


_completer: Completer = openrouter_complete


def set_completer(completer: Completer | None) -> None:
    global _completer
    _completer = completer or openrouter_complete


def parse_itinerary(raw: str, allowed_ids: set[int], max_days: int) -> Itinerary:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip())
    try:
        itinerary = Itinerary.model_validate(json.loads(text))
    except ValueError as exc:
        raise ItineraryError(f"Invalid itinerary JSON: {exc}") from exc
    days = []
    for day in itinerary.days[:max_days]:
        day.slots = [slot for slot in day.slots if slot.venue_id in allowed_ids]
        if day.slots:
            days.append(day)
    if not days:
        raise ItineraryError("Itinerary contained no known venues")
    for index, day in enumerate(days, start=1):
        day.day = index
    itinerary.days = days
    return itinerary


async def generate(messages: list[dict], allowed_ids: set[int], max_days: int) -> Itinerary:
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            return parse_itinerary(await _completer(messages), allowed_ids, max_days)
        except ItineraryError as exc:
            last_error = exc
            logger.warning(f"AI guide generation failed: {exc}")
    raise ItineraryError(str(last_error))
