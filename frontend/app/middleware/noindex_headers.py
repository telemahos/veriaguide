"""X-Robots-Tag for JSON endpoints and parameterised map searches (keep them working, keep them out of the index)."""
import re
from urllib.parse import parse_qs

_API = re.compile(r"^/(?:(?:el|de|en)/)?api/")
_MAP = re.compile(r"^/(?:(?:el|de)/)?map/?$")


def noindex_value(path: str, query_string: str) -> str | None:
    if _API.match(path or ""):
        return "noindex"
    if _MAP.match(path or "") and "q" in parse_qs(query_string or "", keep_blank_values=True):
        return "noindex, follow"
    return None


class NoindexHeaderMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        value = noindex_value(scope.get("path") or "/", (scope.get("query_string") or b"").decode("latin-1"))
        if value is None:
            await self.app(scope, receive, send)
            return

        async def send_with_header(message):
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"x-robots-tag"]
                headers.append((b"x-robots-tag", value.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_header)
