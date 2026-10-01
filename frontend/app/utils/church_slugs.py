"""Public church URLs drop SEO tails. WordPress keeps the long slug."""
import re

_TAIL = re.compile(
    r"-(?:a|an)-\d+(?:st|nd|rd|th)-century-.+$"
    r"|-(?:a|an)-(?:byzantine|sacred|serene|spiritual|jewel|modern|sanctuary).+$"
    r"|-verias-.+$"
    r"|-in-veria(?:-greece)?$"
    r"|-in-verias-.+$"
)
_PREFIX = re.compile(r"^(?:exploring-the-|the-)")


def public_church_slug(slug: str) -> str:
    if not slug:
        return slug
    short = _PREFIX.sub("", slug)
    short = _TAIL.sub("", short).strip("-")
    return short or slug
