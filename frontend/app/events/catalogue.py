"""Dated events for /events. Edit this list; the pages sort by date."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import SITE_URL
from app.i18n import absolute_url

_ATHENS = ZoneInfo("Europe/Athens")

KINDS = {
    "festival": "Festival",
    "religious": "Religious feast",
    "market": "Market",
    "concert": "Concert",
    "exhibition": "Exhibition",
}

MONTHS = {
    "en": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
    "el": ("Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου", "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου"),
    "de": ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"),
}
WEEKDAYS = {
    "en": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    "el": ("Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"),
    "de": ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"),
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
    time: str | None = None
    end_time: str | None = None  # local clock time; never inferred
    tickets_on_sale: date | None = None  # offers.validFrom; only a known on-sale date
    cancelled: bool = False
    hidden: bool = False  # kept in the file but off every page and the sitemap
    price_from: int | None = None  # euros
    body: dict[str, tuple[str, ...]] | None = None  # paragraphs for the detail page
    lineup: tuple[tuple[dict[str, str], dict[str, str]], ...] = ()  # (name, role), each per language
    headliner: str | None = None  # schema.org performer, ahead of the lineup
    producer: str | None = None
    producer_url: str | None = None
    image_srcset: str | None = None

    def when(self) -> str:
        start = self.start.strftime("%d.%m.%Y")
        if self.end != self.start:
            start = f"{start} – {self.end.strftime('%d.%m.%Y')}"
        if self.time:
            return f"{start}, {self.time}"
        return start

    def is_upcoming(self, today: date) -> bool:
        return self.end >= today and not self.cancelled

    def text(self, field: str, lang: str) -> str:
        bag = getattr(self, field)
        return bag.get(lang) or bag["en"]

    def paragraphs(self, lang: str) -> tuple[str, ...]:
        if not self.body:
            return ()
        return self.body.get(lang) or self.body["en"]


EVENTS: tuple[Event, ...] = (
    Event(
        slug="eleni-dimou-enas-dromos-tragoudia",
        start=date(2026, 11, 7),
        end=date(2026, 11, 7),
        time="20:00",
        kind="concert",
        admission="ticket",
        price_from=15,
        image="/static/img/events/eleni-dimou.jpg",
        image_srcset="/static/img/events/eleni-dimou-600.webp 600w, /static/img/events/eleni-dimou-905.webp 905w",
        info_url="https://www.ticketservices.gr/event/periodeia-eleni-dimou/",
        headliner="Eleni Dimou",
        producer="ARTHEMA",
        producer_url="https://www.arthema.gr",
        title={
            "en": "Eleni Dimou: A Road of Songs",
            "el": "Ελένη Δήμου: Ένας Δρόμος Τραγούδια",
            "de": "Eleni Dimou: Ein Weg voller Lieder",
        },
        summary={
            "en": "One of the most distinctive voices of Greek song brings her new show to the Thanos Mikroutsikos Arts Venue, with Isidoros Pateros and conductor Giorgos Pagiatis.",
            "el": "Μία από τις πιο ξεχωριστές φωνές του ελληνικού τραγουδιού έρχεται στον Χώρο Τεχνών «Θάνος Μικρούτσικος» με τη νέα της παράσταση, μαζί με τον Ισίδωρο Πάτερο και τον μαέστρο Γιώργο Παγιάτη.",
            "de": "Eine der unverwechselbaren Stimmen des griechischen Liedes bringt ihr neues Programm in das Kunsthaus Thanos Mikroutsikos, mit Isidoros Pateros und Dirigent Giorgos Pagiatis.",
        },
        body={
            "el": (
                "Ένας δρόμος γεμάτος τραγούδια, μνήμες, συναντήσεις και στιγμές που μας ακολουθούν στον χρόνο.",
                "Η Ελένη Δήμου, μία από τις πιο ξεχωριστές και αναγνωρίσιμες φωνές του ελληνικού τραγουδιού, έρχεται στη Βέροια το Σάββατο 7 Νοεμβρίου, στον Χώρο Τεχνών – Θάνος Μικρούτσικος, με τη νέα της μουσική παράσταση «Ένας Δρόμος Τραγούδια».",
                "Μια βραδιά που διατρέχει μια μεγάλη πορεία στο ελληνικό τραγούδι, μέσα από τις προσωπικές της επιτυχίες αλλά και μέσα από τραγούδια σπουδαίων δημιουργών που σημάδεψαν διαφορετικές εποχές και έγιναν κομμάτι της κοινής μας μνήμης.",
                "Με τη χαρακτηριστική ευαισθησία και την ερμηνευτική δύναμη που τη συνοδεύουν σε όλη την καλλιτεχνική της διαδρομή, η Ελένη Δήμου επιστρέφει σε τραγούδια που αγαπήσαμε, τα συναντά ξανά από τη σημερινή της ματιά και μας καλεί σε μια παράσταση όπου το χθες συνομιλεί με το σήμερα.",
                "Η συνάντηση αυτή αποκτά ιδιαίτερη σημασία και από τον ίδιο τον χώρο που τη φιλοξενεί.",
                "Ο Χώρος Τεχνών της Βέροιας, που εγκαινιάστηκε το 1999 και αποτελεί εδώ και περισσότερα από 25 χρόνια ένα από τα σημαντικότερα πολιτιστικά σημεία αναφοράς της πόλης, φέρει πλέον το όνομα του Θάνου Μικρούτσικου. Η συμβολή του μεγάλου συνθέτη, ως Υπουργού Πολιτισμού, υπήρξε καθοριστική για τη δημιουργία του, στο πλαίσιο της βαθιάς του πίστης ότι ο πολιτισμός δεν πρέπει να περιορίζεται στην Αθήνα αλλά να φτάνει σε κάθε γωνιά της Ελλάδας.",
                "Μια σύγχρονη αίθουσα, με πλατεία και εξώστη, εξαιρετική ακουστική και ολοκληρωμένες σκηνικές υποδομές, που έχει φιλοξενήσει σημαντικές μουσικές και θεατρικές παραγωγές. Και ίσως δεν υπάρχει πιο όμορφος τρόπος να συνεχίζεται η ζωή ενός τέτοιου χώρου από αυτόν για τον οποίο δημιουργήθηκε: με ανθρώπους, μουσική και τραγούδια.",
            ),
            "en": (
                "A road full of songs, memories, encounters and moments that stay with us over time.",
                "Eleni Dimou, one of the most distinctive and recognisable voices of Greek song, comes to Veria on Saturday 7 November, to the Thanos Mikroutsikos Arts Venue, with her new show “A Road of Songs”.",
                "An evening that travels a long road through Greek song, through her own hits and through songs by great composers that marked different eras and became part of our shared memory.",
                "With the sensitivity and interpretive power that have run through her whole career, Eleni Dimou returns to songs we have loved, meets them again with today’s eyes, and invites us to a show where yesterday talks with today.",
                "The venue itself gives the evening a particular meaning.",
                "The Veria Arts Venue opened in 1999 and for more than 25 years has been one of the town’s main cultural landmarks. It now bears the name of Thanos Mikroutsikos, whose support as Minister of Culture was decisive in building it, out of his conviction that culture should not stop at Athens but reach every corner of Greece.",
                "A modern hall with stalls and a balcony, excellent acoustics and a full stage, it has hosted major music and theatre productions. And there may be no better way for such a place to live on than the one it was built for: with people, music and songs.",
            ),
            "de": (
                "Ein Weg voller Lieder, Erinnerungen, Begegnungen und Momente, die uns durch die Zeit begleiten.",
                "Eleni Dimou, eine der unverwechselbarsten Stimmen des griechischen Liedes, kommt am Samstag, 7. November, mit ihrem neuen Programm „Ein Weg voller Lieder“ in das Kunsthaus Thanos Mikroutsikos in Veria.",
                "Ein Abend, der einen langen Weg durch das griechische Lied geht: mit ihren eigenen Erfolgen und mit Liedern großer Komponisten, die verschiedene Epochen geprägt haben und Teil unserer gemeinsamen Erinnerung geworden sind.",
                "Mit der Feinfühligkeit und Ausdruckskraft, die ihren ganzen künstlerischen Weg begleiten, kehrt Eleni Dimou zu Liedern zurück, die wir lieben, begegnet ihnen mit dem Blick von heute und lädt zu einem Abend ein, an dem das Gestern mit dem Heute spricht.",
                "Der Ort selbst gibt dieser Begegnung eine besondere Bedeutung.",
                "Das Kunsthaus von Veria wurde 1999 eröffnet und ist seit mehr als 25 Jahren einer der wichtigsten kulturellen Orte der Stadt. Heute trägt es den Namen von Thanos Mikroutsikos, der als Kulturminister entscheidend zu seinem Bau beitrug, aus der Überzeugung, dass Kultur nicht in Athen enden, sondern jeden Winkel Griechenlands erreichen soll.",
                "Ein moderner Saal mit Parkett und Rang, hervorragender Akustik und voll ausgestatteter Bühne, der bedeutende Musik- und Theaterproduktionen erlebt hat. Und vielleicht gibt es keinen schöneren Weg, einen solchen Ort lebendig zu halten, als den, für den er gebaut wurde: mit Menschen, Musik und Liedern.",
            ),
        },
        lineup=(
            ({"en": "Isidoros Pateros", "el": "Ισίδωρος Πάτερος"}, {"en": "vocals, guitar & bouzouki", "el": "τραγούδι, κιθάρα & μπουζούκι", "de": "Gesang, Gitarre & Bouzouki"}),
            ({"en": "Giorgos Pagiatis", "el": "Γιώργος Παγιάτης"}, {"en": "musical director", "el": "μαέστρος", "de": "musikalische Leitung"}),
            ({"en": "Christos Kechris", "el": "Χρήστος Κεχρής"}, {"en": "bass", "el": "μπάσο", "de": "Bass"}),
            ({"en": "Dimitris Alexiou", "el": "Δημήτρης Αλεξίου"}, {"en": "drums", "el": "ντραμς", "de": "Schlagzeug"}),
        ),
        venue={
            "en": "Thanos Mikroutsikos Arts Venue, Veria",
            "el": "Χώρος Τεχνών «Θάνος Μικρούτσικος», Βέροια",
            "de": "Kunsthaus Thanos Mikroutsikos, Veria",
        },
    ),
    Event(
        slug="christmas-in-the-old-town",
        hidden=True,
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
        hidden=True,
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
        hidden=True,
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
        hidden=True,
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


def visible_events() -> list[Event]:
    return [event for event in EVENTS if not event.hidden]


def split_events(today: date | None = None) -> tuple[list[Event], list[Event]]:
    today = today or date.today()
    shown = visible_events()
    upcoming = sorted((event for event in shown if event.is_upcoming(today)), key=_by_start)
    past = sorted((event for event in shown if event.end < today), key=_by_start, reverse=True)
    return upcoming, past


def get_event(slug: str) -> Event | None:
    return next((event for event in visible_events() if event.slug == slug), None)


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
        "image_srcset": event.image_srcset,
        "info_url": event.info_url,
        "day": event.start.day,
        "month": MONTHS.get(lang, MONTHS["en"])[event.start.month - 1],
        "weekday": WEEKDAYS.get(lang, WEEKDAYS["en"])[event.start.weekday()],
        "year": event.start.year,
        "time": event.time,
        "price_from": event.price_from,
        "paragraphs": event.paragraphs(lang),
        "lineup": [{"name": name.get(lang) or name["en"], "role": role.get(lang) or role["en"]} for name, role in event.lineup],
        "producer": event.producer,
        "producer_url": event.producer_url,
        "cancelled": event.cancelled,
        "upcoming": event.is_upcoming(today),
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
    }


def _asset_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return f"{SITE_URL.rstrip('/')}{path}"


def _local_datetime(day: date, clock: str | None) -> str | None:
    """ISO datetime with the Europe/Athens offset, or None when the clock time is missing or invalid."""
    if not clock or ":" not in clock:
        return None
    hour, minute, *_rest = clock.split(":")
    try:
        local = datetime(day.year, day.month, day.day, int(hour), int(minute), tzinfo=_ATHENS)
    except ValueError:
        return None
    return local.isoformat()


def _start_date(event: Event) -> str:
    """Date, or a local datetime with the Europe/Athens offset when a start time is known."""
    return _local_datetime(event.start, event.time) or event.start.isoformat()


def _end_date(event: Event) -> str | None:
    """A known end, or the date-only end already used for multi-day and untimed events."""
    if event.end_time:
        timed = _local_datetime(event.end, event.end_time)
        if timed:
            return timed
    if not event.time or event.end > event.start:
        return event.end.isoformat()
    return None


def _performers(event: Event, lang: str) -> list[dict]:
    names: list[str] = []
    if event.headliner:
        names.append(event.headliner)
    for name, _role in event.lineup:
        localized = name.get(lang) or name.get("en")
        if localized and localized not in names:
            names.append(localized)
    return [{"@type": "Person", "name": name} for name in names]


def event_node(event: Event, lang: str) -> dict:
    """schema.org Event built only from fields this event already has."""
    place: dict = {
        "@type": "Place",
        "name": event.text("venue", lang),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Veria",
            "addressCountry": "GR",
        },
    }
    if event.venue_path:
        place["url"] = absolute_url(event.venue_path, lang)
    node: dict = {
        "@type": "Event",
        "name": event.text("title", lang),
        "startDate": _start_date(event),
        "eventStatus": (
            "https://schema.org/EventCancelled"
            if event.cancelled
            else "https://schema.org/EventScheduled"
        ),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": place,
        "url": absolute_url(f"/events/{event.slug}", lang),
    }
    description = event.text("summary", lang)
    if description:
        node["description"] = description
    image = _asset_url(event.image)
    if image:
        node["image"] = image
    end_date = _end_date(event)
    if end_date:
        node["endDate"] = end_date
    if event.admission == "free":
        node["isAccessibleForFree"] = True
    elif event.admission == "ticket":
        node["isAccessibleForFree"] = False
    performers = _performers(event, lang)
    if performers:
        node["performer"] = performers
    if event.producer:
        organizer: dict = {"@type": "Organization", "name": event.producer}
        if event.producer_url:
            organizer["url"] = event.producer_url
        node["organizer"] = organizer
    if event.price_from is not None or (event.admission == "ticket" and event.info_url):
        offer: dict = {"@type": "Offer"}
        if event.price_from is not None:
            offer["price"] = event.price_from
            offer["priceCurrency"] = "EUR"
        if event.info_url:
            offer["url"] = event.info_url
            if event.is_upcoming(date.today()):
                offer["availability"] = "https://schema.org/InStock"
        if event.tickets_on_sale is not None:
            offer["validFrom"] = event.tickets_on_sale.isoformat()
        node["offers"] = offer
    return node


def event_graph(lang: str, events: list[Event]) -> str:
    return json.dumps(
        {"@context": "https://schema.org", "@graph": [event_node(event, lang) for event in events]},
        ensure_ascii=False,
    )


def event_detail_jsonld(event: Event, lang: str) -> str:
    return json.dumps({"@context": "https://schema.org", **event_node(event, lang)}, ensure_ascii=False)
