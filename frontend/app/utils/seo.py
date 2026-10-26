"""Localized document titles, opening hours and JSON-LD for public pages."""
from __future__ import annotations

import json
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode

from app.config import SITE_NAME, SITE_URL

TITLE_LIMIT = 60
DESCRIPTION_LIMIT = 155
NON_CONTENT_QUERY_PARAMS = frozenset({"theme"})

_GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")
# Parenthetical ratings such as "(about 4.7)", "(περίπου 4.7)", "(etwa 4,7)".
_RATING_INNER_RE = re.compile(
    r"(?:about|approx(?:imately)?|circa|zirka|ca|etwa|ungefahr|rund|περιπου)\.?"
    r"\s+\d+(?:[.,]\d+)?",
    re.IGNORECASE,
)
_HUB_DESCRIPTION_RE = re.compile(
    r"(?:"
    r"discover the best [a-z0-9 &/-]+ in veria \(veroia\), imathia, greece\.?"
    r"|[a-z0-9 &/-]{3,48} in veria greece"
    r")",
    re.IGNORECASE,
)
_DANGLING_WORDS = frozenset({
    "a", "an", "am", "and", "at", "auf", "bei", "das", "de", "dem", "den", "der",
    "des", "die", "du", "ein", "eine", "for", "fur", "im", "in", "la", "le",
    "mit", "of", "the", "to", "und", "von", "vom", "zu", "zum", "zur",
    "και", "ο", "η", "το", "τον", "την", "του", "της", "των", "στο", "στην", "στον",
})
_CLOCK_RE = re.compile(
    r"(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?)\s*(?:-|–|—|\bto\b|\bbis\b)\s*"
    r"(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?)",
    re.IGNORECASE,
)
_CLOSED_RE = re.compile(
    r"\b(closed|geschlossen|κλειστ[αά])\b",
    re.IGNORECASE,
)
_ALL_DAY_RE = re.compile(
    r"(open\s*24|24\s*hours|24h|rund um die uhr|24ωρ|ολο το 24)",
    re.IGNORECASE,
)
_DAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
_DAY_INDEX = {
    "monday": 0, "mon": 0, "mo": 0, "montag": 0,
    "tuesday": 1, "tue": 1, "tu": 1, "di": 1, "dienstag": 1,
    "wednesday": 2, "wed": 2, "mi": 2, "mittwoch": 2,
    "thursday": 3, "thu": 3, "th": 3, "do": 3, "donnerstag": 3,
    "friday": 4, "fri": 4, "fr": 4, "freitag": 4,
    "saturday": 5, "sat": 5, "sa": 5, "samstag": 5,
    "sunday": 6, "sun": 6, "so": 6, "sonntag": 6,
    "δευτερα": 0, "τριτη": 1, "τεταρτη": 2, "πεμπτη": 3,
    "παρασκευη": 4, "σαββατο": 5, "κυριακη": 6,
}
# Longest suffix that still leaves the full place name intact wins.
# A shorter suffix is preferable to cutting the name.
_TITLE_SUFFIXES = {
    "en": (" | VeriaGuide", " | Veria", ""),
    "de": (" | Veria Reiseführer", " | Reiseführer", " | Veria", ""),
    "el": (" | Οδηγός Βέροιας", " | Βέροια", ""),
}
_KIND = {
    "religious_site": {"en": "Church", "de": "Kirche", "el": "Ναός"},
    "museum": {"en": "Museum", "de": "Museum", "el": "Μουσείο"},
    "archaeological_site": {"en": "Archaeological site", "de": "Archäologische Stätte", "el": "Αρχαιολογικός χώρος"},
    "restaurant": {"en": "Restaurant", "de": "Restaurant", "el": "Εστιατόριο"},
    "cafe": {"en": "Café", "de": "Café", "el": "Καφέ"},
    "accommodation": {"en": "Place to stay", "de": "Unterkunft", "el": "Κατάλυμα"},
    "ski_resort": {"en": "Ski resort", "de": "Skigebiet", "el": "Χιονοδρομικό κέντρο"},
    "hiking_trail": {"en": "Hiking trail", "de": "Wanderweg", "el": "Μονοπάτι"},
    "tour": {"en": "Tour", "de": "Tour", "el": "Περιήγηση"},
    "hidden_gem": {"en": "Hidden gem", "de": "Geheimtipp", "el": "Κρυμμένος θησαυρός"},
}
_SENTENCE = {
    "en": "{name} in Veria, Imathia. Opening hours, map and visitor information.",
    "de": "{name} in Veria, Imathia. Öffnungszeiten, Karte und Hinweise für den Besuch.",
    "el": "{name} στη Βέροια Ημαθίας. Ωράριο, χάρτης και πληροφορίες επίσκεψης.",
}
_SCHEMA_TYPE = {
    "restaurant": "Restaurant",
    "cafe": "CafeOrCoffeeShop",
    "accommodation": "LodgingBusiness",
    "religious_site": "PlaceOfWorship",
    "museum": "Museum",
    "archaeological_site": "TouristAttraction",
    "hiking_trail": "TouristAttraction",
    "ski_resort": "SkiResort",
    "tour": "TouristAttraction",
    "hidden_gem": "TouristAttraction",
    "bar_club": "BarOrPub",
}
_PHONE_KEYS = ("phone", "telephone", "phone_number", "contact_phone")
_HOUR_KEYS = ("opening_hours", "operating_hours")


def strip_non_content_query(query: str) -> str:
    """Drop theme, page=1 and the literal SearchAction placeholder."""
    pairs = []
    for key, value in parse_qsl(query or "", keep_blank_values=False):
        if key in NON_CONTENT_QUERY_PARAMS or not value:
            continue
        if "{search_term_string}" in key or "{search_term_string}" in value:
            continue
        if key == "page" and value == "1":
            continue
        pairs.append((key, value))
    return urlencode(pairs)


def has_greek(text: str | None) -> bool:
    return bool(_GREEK_RE.search(text or ""))


def clamp_text(text: str | None, limit: int) -> str:
    """Shorten on a word boundary so titles and descriptions stay near the limit."""
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit].rsplit(" ", 1)[0].rstrip(".,;:-–—|")
    if len(cut) < int(limit * 0.6):
        cut = cleaned[:limit].rstrip(".,;:-–—| ")
    return cut


def _helpers():
    from app.utils import helpers as helpers

    return helpers


def _first_text(source, key: str) -> str:
    if not isinstance(source, dict) or not key:
        return ""
    raw = source.get(key)
    sanitize = _helpers().sanitize_meta_text
    if isinstance(raw, str):
        return sanitize(raw)
    if isinstance(raw, (list, tuple)):
        for entry in raw:
            if isinstance(entry, str) and entry.strip():
                return sanitize(entry)
            if isinstance(entry, dict):
                rendered = entry.get("rendered")
                if isinstance(rendered, str) and rendered.strip():
                    return sanitize(rendered)
    return ""


def field_text(item: dict, *keys: str) -> str:
    """First non-empty ACF or post-meta value, including WP list-shaped meta."""
    acf = item.get("acf") if isinstance(item, dict) and isinstance(item.get("acf"), dict) else {}
    meta = item.get("meta") if isinstance(item, dict) and isinstance(item.get("meta"), dict) else {}
    for key in keys:
        for source in (acf, meta):
            text = _first_text(source, key)
            if text:
                return text
    return ""


def _latin_ok(text: str) -> bool:
    return bool(text) and not has_greek(text)


def _description_ok(text: str, lang: str) -> bool:
    if not text:
        return False
    if lang == "el":
        return has_greek(text)
    return _latin_ok(text)


def _fold_token(token: str) -> str:
    normalized = unicodedata.normalize("NFD", (token or "").casefold())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def strip_rating_fragments(text: str | None) -> str:
    """Drop parenthetical ratings in every locale and tidy the leftover sentence."""
    def repl(match: re.Match) -> str:
        inner = _fold_token(match.group(1)).strip()
        if _RATING_INNER_RE.fullmatch(inner):
            return ""
        return match.group(0)

    cleaned = re.sub(r"\(([^)]*)\)", repl, text or "")
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def _is_hub_description(text: str) -> bool:
    """True for category slogans such as 'Hotels in Veria Greece', not a listing."""
    folded = re.sub(r"\s+", " ", (text or "")).strip().casefold()
    folded = folded.replace("&amp;", "&")
    return bool(folded) and bool(_HUB_DESCRIPTION_RE.fullmatch(folded))


def _truncate_phrase(text: str, limit: int) -> str:
    """Cut at a word boundary. Never end on a dangling article or preposition."""
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    kept: list[str] = []
    for word in cleaned.split(" "):
        candidate = " ".join([*kept, word])
        if len(candidate) > limit:
            break
        kept.append(word)
    while kept and _fold_token(kept[-1]).strip(".,;:") in _DANGLING_WORDS:
        kept.pop()
    if kept:
        return " ".join(kept)
    return cleaned[:limit].rstrip(".,;:-–—| ")


def _truncate_keeping_tail(text: str, limit: int) -> str:
    """Shorten a name without dropping the last word that distinguishes it."""
    plain = _truncate_phrase(text, limit)
    words = text.split()
    if not words:
        return plain
    last = words[-1]
    if not plain or last in plain.split():
        return plain
    tail = f"… {last}"
    if len(tail) >= limit:
        return plain
    head = _truncate_phrase(text, limit - len(tail) - 1)
    if not head or head.split()[-1] == last:
        return plain
    titled = f"{head} {tail}"
    return titled if len(titled) <= limit else plain


def _without_hub_slogan(text: str) -> str:
    """Drop a trailing category slogan such as 'Hotels in Veria Greece'."""
    parts = [part.strip() for part in re.split(r"\s+\|\s+", text or "") if part.strip()]
    if len(parts) >= 2 and _is_hub_description(parts[-1]):
        return parts[0]
    if len(parts) == 1 and _is_hub_description(parts[0]):
        return ""
    return text


def _display_name(text: str) -> str:
    cleaned = _without_hub_slogan(_helpers().sanitize_meta_text(text))
    if not cleaned:
        return ""
    return _helpers().split_display_title(cleaned)["title"] or cleaned


def place_name(item: dict, lang: str) -> str:
    """Localized listing name. EN/DE stay in Latin; EL uses title_el when it exists.

    seo_title_el and seo_title_de are full document titles, not the place name.
    """
    rendered = _display_name(((item or {}).get("title") or {}).get("rendered") or "")
    specific = _display_name(field_text(item, f"title_{lang}"))
    seo = ""
    if lang == "en":
        specific = specific or _display_name(field_text(item, "title_en"))
        seo = _display_name(field_text(item, "seo_title_en", "seo_tittle_en", "seo_title", "seo_tittle"))
    if lang == "el":
        for candidate in (specific, seo, rendered):
            if candidate:
                return candidate
        return ""
    for candidate in (specific, seo, rendered):
        if _latin_ok(candidate):
            return candidate
    return ""


def compose_document_title(name: str, lang: str) -> str:
    """Full place name plus the longest suffix that fits.

    The suffix is shortened or dropped before the name is cut. A cut stays on a
    word boundary and keeps the final word so two long names do not collapse.
    """
    clean = _helpers().sanitize_meta_text(name)
    if not clean:
        clean = {"de": "Veria", "el": "Βέροια"}.get(lang, "Veria")
    suffixes = _TITLE_SUFFIXES.get(lang, _TITLE_SUFFIXES["en"])
    for suffix in suffixes:
        if len(clean) + len(suffix) <= TITLE_LIMIT:
            return clean + suffix
    return _truncate_keeping_tail(clean, TITLE_LIMIT)


def _kind_label(post_type: str, lang: str) -> str:
    labels = _KIND.get(post_type) or _KIND["hidden_gem"]
    return labels.get(lang) or labels["en"]


def _fallback_description(name: str, lang: str, post_type: str) -> str:
    label = _kind_label(post_type, lang)
    usable = name.strip() if name else ""
    if lang == "el":
        if usable and not has_greek(usable):
            # A Latin proper name may sit inside a Greek sentence.
            pass
        elif not usable:
            usable = label
    elif not usable or has_greek(usable):
        usable = label
    sentence = _SENTENCE.get(lang, _SENTENCE["en"]).format(name=usable)
    if "Heilige" in sentence or "Heiliges" in sentence:
        sentence = sentence.replace("Heiliges", "Kloster").replace("Heilige", "Kirche")
    return sentence


def _rendered_field(item: dict, field: str) -> str:
    return _helpers().sanitize_meta_text(((item or {}).get(field) or {}).get("rendered") or "")


def _usable_description(text: str, lang: str) -> str:
    cleaned = strip_rating_fragments(text)
    if not cleaned or _is_hub_description(cleaned) or not _description_ok(cleaned, lang):
        return ""
    return clamp_text(cleaned, DESCRIPTION_LIMIT)


def locale_seo_title(item: dict, lang: str) -> str:
    """Editor-written full title for EL/DE. Empty when the locale has no override."""
    if lang not in {"el", "de"}:
        return ""
    return field_text(item, f"seo_title_{lang}")


def listing_description(item: dict, lang: str, name: str, post_type: str) -> str:
    """Per-listing excerpt or content. Hub slogans are never used on a detail page.

    seo_description_el and seo_description_de win over excerpt_{lang} when set.
    English keeps seo_description inside the existing candidate list.
    """
    if lang in {"el", "de"}:
        override = field_text(item, f"seo_description_{lang}")
        if override:
            return clamp_text(override, DESCRIPTION_LIMIT)
    seo_keys = [f"seo_description_{lang}"]
    excerpt_keys = [f"excerpt_{lang}"]
    content_keys = [f"content_{lang}"]
    if lang == "en":
        seo_keys.append("seo_description")
        excerpt_keys.append("excerpt_en")
        content_keys.append("content_en")
    candidates = [field_text(item, key) for key in (*seo_keys, *excerpt_keys)]
    # German pages do not reuse the English excerpt or body.
    if lang in {"en", "el"}:
        candidates.append(_rendered_field(item, "excerpt"))
    candidates.extend(field_text(item, key) for key in content_keys)
    if lang in {"en", "el"}:
        candidates.append(_rendered_field(item, "content"))
    for text in candidates:
        usable = _usable_description(text, lang)
        if usable:
            return usable
    return clamp_text(_fallback_description(name, lang, post_type), DESCRIPTION_LIMIT)


def listing_meta(item: dict, lang: str, post_type: str) -> tuple[str, str, str, bool]:
    """Return (document title, meta description, place name, title is verbatim)."""
    name = place_name(item, lang)
    override = locale_seo_title(item, lang)
    title = override or compose_document_title(name, lang)
    return (
        title,
        listing_description(item, lang, name, post_type),
        name,
        bool(override),
    )


def _fold_day(token: str) -> str:
    normalized = unicodedata.normalize("NFD", (token or "").casefold().strip(" ."))
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _parse_clock(token: str) -> str | None:
    match = re.fullmatch(
        r"(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?",
        (token or "").strip(),
        re.IGNORECASE,
    )
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    ampm = (match.group(3) or "").lower().replace(".", "")
    if minute > 59 or hour > 24:
        return None
    if ampm == "am":
        if hour == 12:
            hour = 0
        elif hour > 12:
            return None
    elif ampm == "pm":
        if hour == 12:
            pass
        elif hour > 12:
            return None
        else:
            hour += 12
    elif hour > 23:
        return None
    return f"{hour:02d}:{minute:02d}"


def _day_span(label: str) -> list[int] | None:
    parts = re.split(r"\s*(?:-|–|—|\bto\b|\bbis\b)\s*", label.strip(), maxsplit=1, flags=re.IGNORECASE)
    indexes = []
    for part in parts:
        key = _fold_day(part)
        if key not in _DAY_INDEX:
            return None
        indexes.append(_DAY_INDEX[key])
    if len(indexes) == 1:
        return indexes
    start, end = indexes
    if start <= end:
        return list(range(start, end + 1))
    return list(range(start, 7)) + list(range(0, end + 1))


def _specs_for_value(days: list[int], value: str) -> list[dict]:
    text = (value or "").strip()
    if not text or _CLOSED_RE.search(text):
        return []
    if _ALL_DAY_RE.search(text) and not _CLOCK_RE.search(text):
        return [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": _DAY_NAMES[day],
                "opens": "00:00",
                "closes": "23:59",
            }
            for day in days
        ]
    specs = []
    for match in _CLOCK_RE.finditer(text):
        opens = _parse_clock(match.group(1))
        closes = _parse_clock(match.group(2))
        if not opens or not closes or opens == closes:
            continue
        for day in days:
            specs.append({
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": _DAY_NAMES[day],
                "opens": opens,
                "closes": closes,
            })
    return specs


def _lines(value: str) -> list[str]:
    parts = re.split(r"\n|<br\s*/?>|;", value, flags=re.IGNORECASE)
    return [part.strip(" \t|") for part in parts if part and part.strip(" \t|")]


def opening_hours_specification(value) -> list[dict]:
    """Schema.org hours only when every included range parses unambiguously."""
    if isinstance(value, dict):
        specs = []
        for key, raw in value.items():
            days = _day_span(str(key))
            if not days or not isinstance(raw, str):
                continue
            specs.extend(_specs_for_value(days, raw))
        return specs
    if not isinstance(value, str) or not value.strip():
        return []
    text = value.strip()
    specs = []
    saw_day = False
    for line in _lines(text):
        label, rest = _split_day_line(line)
        days = _day_span(label) if label else None
        if days:
            saw_day = True
            specs.extend(_specs_for_value(days, rest))
    if specs:
        return specs
    if saw_day:
        return []
    compact = re.sub(r"\s+", " ", text).strip()
    only = _CLOCK_RE.search(compact)
    if only and only.group(0).strip() == compact:
        return _specs_for_value(list(range(7)), compact)
    if _ALL_DAY_RE.search(text):
        return _specs_for_value(list(range(7)), text)
    return []


def _split_day_line(line: str) -> tuple[str, str]:
    """Split 'Monday: 09:00-17:00' without treating the clock colon as a separator."""
    match = re.match(r"^(.+?):\s*(.+)$", line)
    if not match:
        return "", line
    if _day_span(match.group(1)):
        return match.group(1), match.group(2)
    return "", line


def hours_from_item(item: dict) -> list[dict]:
    acf = item.get("acf") if isinstance(item, dict) and isinstance(item.get("acf"), dict) else {}
    for key in _HOUR_KEYS:
        specs = opening_hours_specification(acf.get(key))
        if specs:
            return specs
    return []


def _absolute(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("/"):
        return f"{SITE_URL.rstrip('/')}{url}"
    return url


def _real_image(item: dict) -> str | None:
    helpers = _helpers()
    image = helpers.get_featured_image(item)
    if image and not helpers.is_placeholder_image(image):
        return _absolute(image)
    acf = item.get("acf") if isinstance(item.get("acf"), dict) else {}
    for field in ("photo_gallery", "gallery", "photos", "images"):
        url = helpers._acf_field_first_photo_url(acf.get(field))
        if url and not helpers.is_placeholder_image(url):
            return _absolute(url)
    return None


def _coords(item: dict) -> dict | None:
    point = _helpers().listing_map_point(item)
    if not point:
        return None
    try:
        lat = float(point.get("lat"))
        lng = float(point.get("lng"))
    except (TypeError, ValueError):
        return None
    return {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng}


def _address(item: dict) -> dict | None:
    acf = item.get("acf") if isinstance(item, dict) and isinstance(item.get("acf"), dict) else {}
    point = _helpers().listing_map_point(item) or {}
    street = _first_text(acf, "address") or _helpers().sanitize_meta_text(str(point.get("address") or ""))
    city = _first_text(acf, "city") or "Veria"
    if not street and not point:
        return None
    address = {
        "@type": "PostalAddress",
        "addressLocality": city,
        "addressRegion": "Imathia",
        "addressCountry": "GR",
    }
    if street:
        address["streetAddress"] = street
    return address


def _phone(item: dict) -> str:
    return field_text(item, *_PHONE_KEYS)


def breadcrumb_list(crumbs: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": url,
            }
            for index, (name, url) in enumerate(crumbs, start=1)
            if name and url
        ],
    }


def _dump(graph: list[dict]) -> str:
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def detail_structured_data(
    post_type: str,
    item: dict,
    category_key: str,
    name: str,
    description: str,
) -> str:
    """BreadcrumbList plus a place/business node. Empty properties are omitted."""
    from app.i18n import current_lang
    from app.utils.category_urls import get_category_url_path
    from app.utils.wp_text import category_label

    helpers = _helpers()
    lang = current_lang()
    slug = item.get("slug") or ""
    public = get_category_url_path(category_key)
    page_url = helpers.get_page_url(f"/{public}/{slug}")
    hub_url = helpers.get_page_url(f"/{public}")
    place = name or category_label(category_key, lang)
    node = {
        "@type": _SCHEMA_TYPE.get(post_type, "TouristAttraction"),
        "name": place,
        "url": page_url,
        "inLanguage": lang,
    }
    if description:
        node["description"] = description
    image = _real_image(item)
    if image:
        node["image"] = image
    address = _address(item)
    if address:
        node["address"] = address
    geo = _coords(item)
    if geo:
        node["geo"] = geo
    phone = _phone(item)
    if phone:
        node["telephone"] = phone
    hours = hours_from_item(item)
    if hours:
        node["openingHoursSpecification"] = hours
    acf = item.get("acf") if isinstance(item.get("acf"), dict) else {}
    price = _first_text(acf, "price_range")
    if price:
        node["priceRange"] = price
    cuisine = _first_text(acf, "cuisine") or _first_text(acf, "cuisine_type")
    if cuisine and node["@type"] in {"Restaurant", "CafeOrCoffeeShop"}:
        node["servesCuisine"] = cuisine
    crumbs = breadcrumb_list([
        (_tr("Home"), helpers.get_page_url("/")),
        (category_label(category_key, lang), hub_url),
        (place, page_url),
    ])
    return _dump([node, crumbs])


def webpage_jsonld(
    schema_type: str,
    name: str,
    description: str,
    url: str,
    crumbs: list[tuple[str, str]],
    main_entity: dict | None = None,
    image: str | None = None,
) -> str:
    from app.i18n import current_lang

    page = {
        "@type": schema_type,
        "name": name,
        "url": url,
        "inLanguage": current_lang(),
        "isPartOf": {
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": _helpers().get_page_url("/"),
        },
    }
    if description:
        page["description"] = description
    if image:
        page["primaryImageOfPage"] = {"@type": "ImageObject", "url": image}
    if main_entity and main_entity.get("itemListElement"):
        page["mainEntity"] = main_entity
    return _dump([page, breadcrumb_list(crumbs)])


def item_list_jsonld(items: list, category_key: str, page: int = 1, per_page: int = 12) -> dict:
    """ItemList of the listings shown on a hub page (absolute, locale-prefixed URLs)."""
    from app.utils.helpers import SITE_URL, listing_detail_href, sanitize_meta_text, strip_tags

    elements = []
    offset = max(page - 1, 0) * (per_page or 12)
    for item in items or []:
        if not isinstance(item, dict):
            continue
        href = listing_detail_href(item, category_key)
        title = item.get("title")
        name = title.get("rendered", "") if isinstance(title, dict) else (title or "")
        name = sanitize_meta_text(strip_tags(name))
        if not href or not name:
            continue
        elements.append({
            "@type": "ListItem",
            "position": offset + len(elements) + 1,
            "url": f"{SITE_URL.rstrip('/')}{href}",
            "name": name,
        })
    return {"@type": "ItemList", "numberOfItems": len(elements), "itemListElement": elements}


def _tr(text: str) -> str:
    from app.i18n import tr

    return tr(text)


def image_dims(value) -> dict:
    """Width and height when the image object actually carries them."""
    if not isinstance(value, dict):
        return {}
    width = value.get("width")
    height = value.get("height")
    details = value.get("media_details") if isinstance(value.get("media_details"), dict) else {}
    width = width or details.get("width")
    height = height or details.get("height")
    sizes = value.get("sizes") if isinstance(value.get("sizes"), dict) else {}
    if not (width and height):
        for key in ("full", "large", "medium_large", "medium"):
            sized = sizes.get(key)
            if isinstance(sized, dict) and sized.get("width") and sized.get("height"):
                width, height = sized.get("width"), sized.get("height")
                break
    try:
        width_i, height_i = int(width), int(height)
    except (TypeError, ValueError):
        return {}
    if width_i > 0 and height_i > 0:
        return {"width": width_i, "height": height_i}
    return {}
