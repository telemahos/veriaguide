"""Cookie-consent helpers for the site-wide banner and analytics gating."""

from fastapi import Request

COOKIE_NAME = "cookie_consent"
# Values: "1" = essential + Google Analytics; "essential" = essential only.
ACCEPTED_VALUES = frozenset({"1", "essential"})
ANALYTICS_VALUE = "1"
MAX_AGE_SECONDS = 365 * 24 * 60 * 60  # 12 months


def consent_choice(request: Request) -> str:
    raw = (request.cookies.get(COOKIE_NAME) or "").strip()
    return raw if raw in ACCEPTED_VALUES else ""


def has_consent(request: Request) -> bool:
    return bool(consent_choice(request))


def analytics_allowed(request: Request) -> bool:
    return consent_choice(request) == ANALYTICS_VALUE
