"""Dated events for /events. Edit this list; the pages sort by date."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from app.config import SITE_URL

KINDS = {
    "festival": "Festival",
    "religious": "Religious feast",
    "market": "Market",
    "concert": "Concert",
    "exhibition": "Exhibition",
}


@dataclass(frozen=True)
class Event:
    slug: str
    start: date
    end: date
    kind: str
    admission: str  # free | ticket
    title: dict[str, str]
    summary: dict[str, str]
    venue: dict[str, str]
    venue_path: str | None = None
    image: str | None = None
    info_url: str | None = None
    cancelled: bool = False

    def when(self) -> str:
        start = self.start.strftime("%d.%m.%Y")
        if self.end == self.start:
            return start
        return f"{start} – {self.end.strftime('%d.%m.%Y')}"

    def is_upcoming(self, today: date) -> bool:
        return self.end >= today and not self.cancelled

    def text(self, field: str, lang: str) -> str:
        bag = getattr(self, field)
        return bag.get(lang) or bag["en"]


EVENTS: tuple[Event, ...] = (
    Event(
        slug="christmas-in-the-old-town",
        start=date(2026, 12, 19),
        end=date(2027, 1, 6),
        kind="festival",
        admission="free",
        image="/static/img/v3/nacht-800.webp",
        title={
            "en": "Christmas in the old town",
            "el": "Χριστούγεννα στην παλιά πόλη",
            "de": "Weihnachten in der Altstadt",
        },
        summary={
            "en": "Lights, music and stalls in the lanes of Veria, from the week before Christmas through Epiphany.",
            "el": "Φώτα, μουσική και πάγκοι στα σοκάκια της Βέροιας, από την εβδομάδα πριν τα Χριστούγεννα μέχρι τα Φώτα.",
            "de": "Lichter, Musik und Stände in den Gassen von Veria, von der Woche vor Weihnachten bis Epiphanias.",
        },
        venue={
            "en": "Old town, Veria",
            "el": "Παλιά πόλη, Βέροια",
            "de": "Altstadt, Veria",
        },
    ),
    Event(
        slug="theophany",
        start=date(2027, 1, 6),
        end=date(2027, 1, 6),
        kind="religious",
        admission="free",
        image="/static/img/v3/fluss-800.webp",
        title={
            "en": "Theophany",
            "el": "Θεοφάνεια",
            "de": "Theophanie",
        },
        summary={
            "en": "The blessing of the waters on 6 January, the close of the Christmas season in Veria.",
            "el": "Ο αγιασμός των υδάτων στις 6 Ιανουαρίου, το κλείσιμο της χριστουγεννιάτικης περιόδου στη Βέροια.",
            "de": "Die Wasserweihe am 6. Januar, der Abschluss der Weihnachtszeit in Veria.",
        },
        venue={
            "en": "Veria",
            "el": "Βέροια",
            "de": "Veria",
        },
    ),
    Event(
        slug="saints-peter-and-paul",
        start=date(2027, 6, 29),
        end=date(2027, 6, 29),
        kind="religious",
        admission="free",
        image="/static/img/v3/bema-800.webp",
        venue_path="/religious-sites/step-of-the-apostle-paul",
        title={
            "en": "Feast of Saints Peter and Paul",
            "el": "Εορτή των Αγίων Πέτρου και Παύλου",
            "de": "Fest der Heiligen Petrus und Paulus",
        },
        summary={
            "en": "The feast of the apostles on 29 June. The Bema in the centre of Veria marks where Paul spoke.",
            "el": "Η εορτή των αποστόλων στις 29 Ιουνίου. Το Βήμα στο κέντρο της Βέροιας σημαδεύει το σημείο όπου μίλησε ο Παύλος.",
            "de": "Das Apostelfest am 29. Juni. Das Bema im Zentrum von Veria markiert die Stelle, an der Paulus sprach.",
        },
        venue={
            "en": "Bema of Apostle Paul, Veria",
            "el": "Βήμα του Αποστόλου Παύλου, Βέροια",
            "de": "Bema des Apostels Paulus, Veria",
        },
    ),
    Event(
        slug="dormition",
        start=date(2026, 8, 15),
        end=date(2026, 8, 15),
        kind="religious",
        admission="free",
        image="/static/img/v3/innen-800.webp",
        title={
            "en": "Dormition of the Virgin",
            "el": "Κοίμηση της Θεοτόκου",
            "de": "Entschlafung der Gottesmutter",
        },
        summary={
            "en": "The great August feast in the churches of Veria, on 15 August.",
            "el": "Η μεγάλη γιορτή του Αυγούστου στους ναούς της Βέροιας, στις 15 Αυγούστου.",
            "de": "Das große Augustfest in den Kirchen von Veria, am 15. August.",
        },
        venue={
            "en": "Churches of Veria",
            "el": "Ναοί της Βέροιας",
            "de": "Kirchen von Veria",
        },
    ),
)


def _by_start(event: Event) -> date:
    return event.start


def split_events(today: date | None = None) -> tuple[list[Event], list[Event]]:
    today = today or date.today()
    upcoming = sorted((event for event in EVENTS if event.is_upcoming(today)), key=_by_start)
    past = sorted((event for event in EVENTS if event.end < today), key=_by_start, reverse=True)
    return upcoming, past


def get_event(slug: str) -> Event | None:
    return next((event for event in EVENTS if event.slug == slug), None)


def present(event: Event, lang: str, today: date | None = None) -> dict:
    today = today or date.today()
    return {
        "slug": event.slug,
        "title": event.text("title", lang),
        "summary": event.text("summary", lang),
        "venue": event.text("venue", lang),
        "venue_path": event.venue_path,
        "when": event.when(),
        "kind": event.kind,
        "kind_label": KINDS.get(event.kind, event.kind),
        "admission": event.admission,
        "image": event.image,
        "info_url": event.info_url,
        "cancelled": event.cancelled,
        "upcoming": event.is_upcoming(today),
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
    }


def event_graph(lang: str, events: list[Event]) -> str:
    items = []
    for event in events:
        if event.cancelled:
            status = "https://schema.org/EventCancelled"
        elif event.end < date.today():
            status = "https://schema.org/EventScheduled"
        else:
            status = "https://schema.org/EventScheduled"
        place = {
            "@type": "Place",
            "name": event.text("venue", lang),
            "address": "Veria, Greece",
        }
        if event.venue_path:
            place["url"] = f"{SITE_URL}{event.venue_path}"
        items.append({
            "@type": "Event",
            "name": event.text("title", lang),
            "startDate": event.start.isoformat(),
            "endDate": event.end.isoformat(),
            "eventStatus": status,
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": place,
            "isAccessibleForFree": event.admission == "free",
            "description": event.text("summary", lang),
            "url": f"{SITE_URL}/events/{event.slug}",
        })
    return json.dumps({"@context": "https://schema.org", "@graph": items}, ensure_ascii=False)
