"""Single Gemini call returning a validated itinerary."""
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


ITINERARY_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer"},
                    "title": {"type": "string"},
                    "slots": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "time": {"type": "string"},
                                "venue_id": {"type": "integer"},
                                "note": {"type": "string"},
                            },
                            "required": ["time", "venue_id"],
                        },
                    },
                },
                "required": ["day", "slots"],
            },
        },
    },
    "required": ["title", "summary", "days"],
}


def _gemini_payload(messages: list[dict], model: str) -> dict:
    system = "\n\n".join(message["content"] for message in messages if message.get("role") == "system")
    user = "\n\n".join(message["content"] for message in messages if message.get("role") != "system")
    payload = {
        "model": model,
        "input": user or "Plan the trip.",
        "store": False,
        "generation_config": {"temperature": 0.4, "max_output_tokens": config.max_tokens()},
        "response_format": {"type": "text", "mime_type": "application/json", "schema": ITINERARY_SCHEMA},
    }
    if system:
        payload["system_instruction"] = system
    return payload


def _gemini_text(body: dict) -> str:
    if isinstance(body.get("output_text"), str) and body["output_text"].strip():
        return body["output_text"]
    chunks = []
    for step in body.get("outputs") or body.get("steps") or []:
        if not isinstance(step, dict):
            continue
        if step.get("text"):
            chunks.append(step["text"])
        for part in step.get("content") or []:
            if isinstance(part, dict) and part.get("text"):
                chunks.append(part["text"])
    if not chunks:
        raise KeyError("Gemini response had no text")
    return "".join(chunks)


def _models_to_try() -> list[str]:
    chosen = config.model()
    fallbacks = ("gemini-3.5-flash", "gemini-2.5-flash-lite", "gemini-flash-lite-latest")
    models = [chosen]
    for name in fallbacks:
        if name not in models:
            models.append(name)
    return models


def _try_next_model(error: Exception) -> bool:
    text = str(error)
    return "404" in text or "503" in text or "UNAVAILABLE" in text


async def _post_gemini(client: httpx.AsyncClient, model: str, messages: list[dict], key: str) -> str:
    response = await client.post(
        config.GEMINI_URL,
        json=_gemini_payload(messages, model),
        headers={"x-goog-api-key": key},
    )
    if response.status_code >= 400:
        detail = " ".join(response.text.split())[:240]
        raise ItineraryError(f"Gemini request failed: {response.status_code} {detail}")
    return _gemini_text(response.json())


async def gemini_complete(messages: list[dict]) -> str:
    key = config.api_key()
    if not key:
        raise ItineraryError("GOOGLE_API_KEY is not set")
    last_error: Exception | None = None
    try:
        async with httpx.AsyncClient(timeout=config.timeout()) as client:
            for model in _models_to_try():
                try:
                    return await _post_gemini(client, model, messages, key)
                except ItineraryError as exc:
                    last_error = exc
                    if not _try_next_model(exc):
                        raise
                    logger.warning(f"Gemini model {model} unavailable, trying the next one")
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise ItineraryError(f"Gemini request failed: {exc}") from exc
    raise ItineraryError(str(last_error))


_completer: Completer = gemini_complete


def set_completer(completer: Completer | None) -> None:
    global _completer
    _completer = completer or gemini_complete


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
