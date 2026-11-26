"""Published guide articles. Drafts and other post types stay off the public site."""
from html.parser import HTMLParser

from app.utils.category_urls import PUBLIC_CATEGORY_PATHS

_LISTING_PREFIXES = tuple(
    f"/{path}/"
    for key, path in PUBLIC_CATEGORY_PATHS.items()
    if key != "guides"
)


def is_public_guide(post: dict | None) -> bool:
    """True only for a published guide with a slug. Missing status counts as publish."""
    if not isinstance(post, dict):
        return False
    if post.get("type") != "guide":
        return False
    status = post.get("status") or "publish"
    if status != "publish":
        return False
    return bool(post.get("slug"))


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a" or self._href is not None:
            return
        href = dict(attrs).get("href") or ""
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._text).strip()))
            self._href = None


def _listing_path(href: str) -> str | None:
    path = (href or "").split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        return None
    for code in ("el", "de", "en"):
        prefix = f"/{code}/"
        if path.startswith(prefix):
            path = path[len(prefix) - 1:]
            break
    if any(path.startswith(prefix) for prefix in _LISTING_PREFIXES):
        return path.rstrip("/") or path
    return None


def related_listing_links(html: str) -> list[dict[str, str]]:
    """Internal directory links already written in the article body."""
    parser = _AnchorParser()
    try:
        parser.feed(html or "")
    except Exception:
        return []
    seen: set[str] = set()
    links: list[dict[str, str]] = []
    for href, text in parser.links:
        path = _listing_path(href)
        if not path or path in seen:
            continue
        seen.add(path)
        label = " ".join(text.split()) or path.rsplit("/", 1)[-1].replace("-", " ").title()
        links.append({"href": path, "label": label})
    return links
