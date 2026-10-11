"""Display helpers for WordPress tags and single-language ACF strings."""
from __future__ import annotations

import re

from jinja2 import pass_context

from app.i18n import current_lang, tr

# Display name regardless of whether WP still uses the misspelled term.
TAG_CANONICAL: dict[str, str] = {
    "Archeological Site": "Archaeological Site",
    "archeological site": "Archaeological Site",
    "Hicking": "Hiking",
    "hicking": "Hiking",
}

POST_TYPE_LABELS = {
    "museum": "Museum",
    "archaeological_site": "Archaeological Site",
    "religious_site": "Religious Site",
    "restaurant": "Restaurant",
    "cafe": "Café",
    "accommodation": "Accommodation",
    "ski_resort": "Ski Resort",
    "hiking_trail": "Hiking Trail",
    "hidden_gem": "Hidden Gem",
    "tour": "Tour",
}

CATEGORY_LABELS = {
    "museums": "Museums",
    "restaurants": "Restaurants",
    "cafes": "Cafés",
    "archaeological_sites": "Archaeological Sites",
    "religious_sites": "Religious Sites",
    "hiking_trails": "Hiking Trails",
    "accommodations": "Accommodations",
    "ski_resorts": "Ski Resorts",
    "tours": "Tours",
    "hidden_gems": "Hidden Gems",
}

_WEEKDAYS = {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
    "saturday": "Saturday",
    "sunday": "Sunday",
    "mon": "Monday",
    "tue": "Tuesday",
    "wed": "Wednesday",
    "thu": "Thursday",
    "fri": "Friday",
    "sat": "Saturday",
    "sun": "Sunday",
}

_PHRASE_KEYS = (
    "Free access without ticket; dress respectfully.",
    "Free access; respect ongoing worship and restoration work.",
    "Free access without ticket",
    "Open 24 hours",
    "Open 24 Hours",
    "24 hours",
    "Closed",
    "Free Access",
    "Free access",
    "Free",
    "By donation",
    "Not available",
    "Dress respectfully",
)

_TIME_RE = re.compile(
    r"(?i)\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b"
)
_DAY_LINE_RE = re.compile(
    r"(?i)\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b"
)


def canonical_tag_name(name: str | None) -> str:
    if not name:
        return ""
    text = str(name).strip()
    return TAG_CANONICAL.get(text) or TAG_CANONICAL.get(text.casefold()) or text


def tag_label(name: str | None, lang: str | None = None) -> str:
    canonical = canonical_tag_name(name)
    if not canonical:
        return ""
    return tr(canonical, lang)


def post_type_label(post_type: str | None, lang: str | None = None) -> str:
    if not post_type:
        return ""
    key = POST_TYPE_LABELS.get(post_type) or post_type.replace("_", " ").replace("-", " ").title()
    return tr(key, lang)


def category_label(category: str | None, lang: str | None = None) -> str:
    if not category:
        return ""
    key = CATEGORY_LABELS.get(category) or category.replace("_", " ").title()
    return tr(key, lang)


def _hour_24(hour: int, minute: int, ampm: str) -> str:
    ampm = ampm.lower().replace(".", "")
    if ampm == "am":
        if hour == 12:
            hour = 0
    elif hour != 12:
        hour += 12
    return f"{hour:02d}:{minute:02d}"


def _replace_times(text: str, lang: str) -> str:
    if lang == "en":
        return text

    def repl(match: re.Match) -> str:
        hour = int(match.group(1))
        minute = int(match.group(2) or "0")
        return _hour_24(hour, minute, match.group(3))

    return _TIME_RE.sub(repl, text)


def translate_hours_text(text: str | None, lang: str | None = None) -> str:
    """Translate weekday names, Closed/Free/24h, and am/pm clocks. Fall back to original."""
    if text is None:
        return ""
    raw = str(text)
    if not raw.strip():
        return raw
    lang = lang or current_lang()
    if lang == "en":
        return raw

    pieces = re.split(r"(\n|<br\s*/?>)", raw, flags=re.I)
    out = []
    for piece in pieces:
        if re.fullmatch(r"\n|<br\s*/?>", piece or "", flags=re.I):
            out.append(piece)
            continue
        translated = piece
        for phrase in _PHRASE_KEYS:
            if phrase.lower() in translated.lower():
                localized = tr(phrase if phrase != "Open 24 Hours" else "Open 24 hours", lang)
                translated = re.sub(re.escape(phrase), localized, translated, flags=re.I)
        def day_repl(match: re.Match) -> str:
            english = _WEEKDAYS.get(match.group(1).lower(), match.group(1))
            return tr(english, lang)

        translated = _DAY_LINE_RE.sub(day_repl, translated)
        translated = _replace_times(translated, lang)
        out.append(translated)
    return "".join(out)


def localize_acf_value(acf: dict | None, field: str, lang: str | None = None) -> str:
    """Prefer field_<lang> when present; otherwise translate the English ACF string."""
    lang = lang or current_lang()
    if not isinstance(acf, dict) or not field:
        return ""
    candidates = (
        f"{field}_{lang}",
        f"{field}{lang}",
        field,
    )
    value = None
    for key in candidates:
        raw = acf.get(key)
        if isinstance(raw, str) and raw.strip():
            value = raw
            if key != field:
                return value
            break
        if isinstance(raw, dict) and lang != "en":
            continue
    if value is None:
        return ""
    return display_wp_text(value, lang)


def display_wp_text(value: str | None, lang: str | None = None) -> str:
    """Translate a tag, category, price label, or hours-like string."""
    if value is None:
        return ""
    text = str(value)
    if not text.strip():
        return text
    lang = lang or current_lang()
    canonical = canonical_tag_name(text)
    labeled = tr(canonical, lang)
    if labeled != canonical:
        return labeled
    if canonical != text:
        return canonical if lang == "en" else tr(canonical, lang)
    via_table = tr(text, lang)
    if via_table != text:
        return via_table
    return translate_hours_text(text, lang)


@pass_context
def jinja_wp_text(context, value):
    lang = "en"
    if context is not None:
        lang = context.get("lang") or current_lang()
    return display_wp_text(value, lang)


@pass_context
def jinja_acf_text(context, acf, field: str):
    lang = "en"
    if context is not None:
        lang = context.get("lang") or current_lang()
    return localize_acf_value(acf, field, lang)


@pass_context
def jinja_post_type_label(context, post_type):
    lang = "en"
    if context is not None:
        lang = context.get("lang") or current_lang()
    return post_type_label(post_type, lang)


@pass_context
def jinja_category_label(context, category):
    lang = "en"
    if context is not None:
        lang = context.get("lang") or current_lang()
    return category_label(category, lang)
