import json

from app.ai_guide.models import WizardState

LANGUAGE_NAMES = {"en": "English", "el": "Greek", "de": "German"}

SCHEMA = {
    "title": "string",
    "summary": "string",
    "days": [{"day": 1, "title": "string", "slots": [{"time": "09:30", "venue_id": 123, "note": "string"}]}],
}


def build_messages(state: WizardState, venues: list[dict], lang: str) -> list[dict]:
    language = LANGUAGE_NAMES.get(lang, "English")
    churches_opted_out = "churches" not in state.interests and "heritage" not in state.interests and bool(
        state.interests
    )
    system = (
        "You are VeriaGuide, a local travel planner for Veria (Veroia) and the Imathia region of Greece. "
        "Plan only within Veria and Imathia. Use only venues from the provided list and refer to them by "
        "their numeric venue_id; never invent venues, addresses or prices. "
        "Respect opening hours and tags when given; do not schedule a venue outside its stated hours. "
        + (
            ""
            if churches_opted_out
            else "Include at least one church or heritage venue per day when available. "
        )
        + "Keep 3 to 5 slots per day with realistic walking/driving order. "
        f"Write all text fields in {language}. "
        "Reply with a single JSON object only, no markdown, matching this shape: " + json.dumps(SCHEMA)
    )
    trip = {
        "start_date": state.start_date.isoformat() if state.start_date else None,
        "days": state.days,
        "party": state.party,
        "interests": state.interests,
        "budget": state.budget,
        "wishes": state.wishes,
    }
    user = "Trip:\n" + json.dumps(trip, ensure_ascii=False) + "\n\nVenues:\n" + json.dumps(
        [{k: v for k, v in venue.items() if k not in ("url", "image")} for venue in venues], ensure_ascii=False
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
