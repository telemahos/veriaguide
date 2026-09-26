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
    party_hint = {
        "solo": "Solo: a dense walking day is fine, one seated meal is enough.",
        "couple": "Couple: keep one unhurried meal and do not pack the evening.",
        "family": "Family: shorter museum stops, no late dinner, avoid long drives after 16:00.",
        "group": "Group: choose places that can seat several people and keep one shared meal.",
    }.get(state.party or "", "")
    system = (
        "You write practical day plans for Veria (Veroia) and the Imathia region for VeriaGuide. "
        "Stay inside Veria and Imathia. Use only the given venue_id values. "
        "Never invent a place, address, price, dish or opening hour. "
        f"Write every text field in {language}. Leave venue names exactly as given; do not translate them. "
        "Group stops geographically. Keep Vergina and Aigai in one morning block. "
        "Keep the old town of Veria as a walking cluster. Put a meal next to where the person already is. "
        "Use 3 to 5 stops a day. Do not put every stop on the hour. "
        "Leave a real gap: museum 60 to 90 minutes, church 20 to 40 minutes, meal 75 to 90 minutes. "
        "Vergina needs about 20 minutes of driving each way from Veria, plus time on site. "
        "Each note is exactly two short sentences and must include all three of these: "
        "one concrete thing to look at, copied from that venue's summary, tags or hours; "
        "how long to stay; "
        "how to arrive from the previous stop, on foot in the old town or by car, with a rough number of minutes. "
        "If the source text has no concrete fact, say what to do on arrival instead of describing a mood. "
        "Do not write filler such as: enjoy the atmosphere, take a stroll, immerse yourself, magical, "
        "unique experience, rich history, morning exploration, απολαύστε, βόλτα, χαλαρός ρυθμός, "
        "μοναδική εμπειρία, πρωινή περιήγηση. "
        "The day title names the places or the move, for example Vergina in the morning and the old town after lunch. "
        "The summary is two sentences: where the days go, and one practical warning about hours or driving. "
        "Do not schedule a stop outside its stated hours. "
        + (
            "The traveller opted out of churches and heritage, so leave those categories out. "
            if churches_opted_out
            else "Keep at least one church or heritage stop on each day when the list contains one. "
        )
        + (party_hint + " " if party_hint else "")
        + "Reply with one JSON object only, no markdown, in this shape: "
        + json.dumps(SCHEMA)
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
