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
        "Greece: include one cafe stop on each day when a cafe is in the list. People drink coffee, often to take away. "
        + (
            "Budget is low, so a fast food stop is allowed for the meal. "
            if state.budget == "low"
            else "Budget is not low, so do not choose fast food, burgers, pizza or snacks. The meal must be a taverna or a sit-down restaurant. "
        )
        + (
            "The trip covers more than one day. Include one accommodation in Veria or Imathia from the list and name the night it covers. "
            if state.days > 1
            else ""
        )
        + "Use 5 to 7 stops on a day spent in Veria. A church visit is short, so one church is not a day. "
        "When churches or heritage are requested and several churches are in the list, visit at least three different churches across the trip, and two or three on an old-town day. "
        + (
            "One day cannot hold every landmark. It must still include the Royal Tombs at Aigai when that venue is listed, plus either the Vema of Apostle Paul, the Old Metropolis, or the Church of the Resurrection, and an evening meal. "
            if state.days <= 1
            else "Two days must include, when each venue is in the list: the Royal Tombs and the theatre at Aigai on one morning; on the Veria day the Vema of Apostle Paul, the Old Metropolis, the Church of the Resurrection, and Barbouta; plus the Byzantine Museum or the Archaeological Museum. "
            if state.days == 2
            else "With three or more days, include every one of these that appears in the list, each on its own slot: the Royal Tombs at Aigai, the theatre at Aigai, the Vema of Apostle Paul, the Old Metropolis, the Church of the Resurrection, Barbouta, the Byzantine Museum, and the Archaeological Museum. Use leftover time for more old-town churches. "
        )
        + "Never drop one of these landmarks to make room for a lesser stop. "
        "Do not finish a day at 17:00 or 18:00. Veria eats and drinks late. End the day with a taverna or a drink around 20:30 to 22:00 when such a place is in the list. "
        "Do not put every stop on the hour. "
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
