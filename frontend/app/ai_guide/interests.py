"""Wizard interests mapped to live public categories. Tours are never part of the guide."""
from app.config import POST_TYPES

EXCLUDED = frozenset({"tours"})

INTEREST_CATEGORIES: dict[str, tuple[str, ...]] = {
    "heritage": ("archaeological_sites", "hidden_gems"),
    "churches": ("religious_sites",),
    "museums": ("museums",),
    "food": ("restaurants", "cafes"),
    "nature": ("hiking_trails",),
    "winter": ("ski_resorts",),
}

INTEREST_LABELS = {
    "heritage": "Heritage & archaeology",
    "churches": "Churches & monasteries",
    "museums": "Museums",
    "food": "Food & cafés",
    "nature": "Nature & hiking",
    "winter": "Winter & skiing",
}

DEFAULT_INTERESTS = ("heritage", "churches", "museums", "food")


def categories_for(interests: list[str]) -> list[str]:
    """Return live category keys for the chosen interests, in order, without tours."""
    chosen = [i for i in interests if i in INTEREST_CATEGORIES] or list(DEFAULT_INTERESTS)
    seen: list[str] = []
    for interest in chosen:
        for category in INTEREST_CATEGORIES[interest]:
            if category in POST_TYPES and category not in EXCLUDED and category not in seen:
                seen.append(category)
    return seen
