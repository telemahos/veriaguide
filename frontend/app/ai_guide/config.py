"""Environment settings for the AI Guide. Read on every call so the flag can be toggled per process/test."""
import os

DEFAULT_MODEL = "gemini-3.8-flash"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def is_enabled() -> bool:
    return os.getenv("AI_GUIDE_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")


def api_key() -> str:
    return os.getenv("GOOGLE_API_KEY", "").strip()


def model() -> str:
    raw = (os.getenv("AI_GUIDE_MODEL") or DEFAULT_MODEL).strip()
    if "/" in raw:
        raw = raw.rsplit("/", 1)[-1]
    return raw or DEFAULT_MODEL


def max_venues() -> int:
    return max(1, min(_int("AI_GUIDE_MAX_VENUES", 25), 40))


def max_tokens() -> int:
    return _int("AI_GUIDE_MAX_TOKENS", 2500)


def timeout() -> int:
    return _int("AI_GUIDE_TIMEOUT", 45)


def rate_limit() -> int:
    """Generate calls allowed per IP per hour."""
    return _int("AI_GUIDE_RATE_LIMIT", 5)


def itinerary_ttl() -> int:
    return _int("AI_GUIDE_TTL_DAYS", 14) * 86400


SESSION_TTL = 7200
MAX_DAYS = 7
MAX_WISHES = 500


def secure_cookies() -> bool:
    return os.getenv("ENVIRONMENT", "development") not in ("development", "testing")
