"""Switchable themes: "classic" (current design) and "new" (2026 redesign).

Selection order: ?theme=... (also stored in a cookie), then the vg_theme cookie,
then DEFAULT_THEME. For the new theme a template `v2/<name>` is used when it
exists; otherwise the classic template is rendered, so pages can migrate one by one.
"""
import contextvars
import os
from urllib.parse import parse_qs

import jinja2

COOKIE_NAME = "vg_theme"
COOKIE_MAX_AGE = 31536000
THEMES = ("classic", "new")
V2_PREFIX = "v2/"

_theme: contextvars.ContextVar[str] = contextvars.ContextVar("vg_theme", default="classic")


def default_theme() -> str:
    value = os.getenv("DEFAULT_THEME", "classic").strip().lower()
    return value if value in THEMES else "classic"


def current_theme() -> str:
    return _theme.get()


def set_theme(theme: str):
    return _theme.set(theme if theme in THEMES else "classic")


def reset_theme(token) -> None:
    _theme.reset(token)


class ThemedEnvironment(jinja2.Environment):
    """Resolve `name` to `v2/name` for the new theme when that template exists."""

    def _themed(self, name):
        if (
            isinstance(name, str)
            and current_theme() == "new"
            and not name.startswith(V2_PREFIX)
            and self.loader is not None
        ):
            candidate = V2_PREFIX + name
            try:
                self.loader.get_source(self, candidate)
            except jinja2.TemplateNotFound:
                return name
            return candidate
        return name

    def get_template(self, name, parent=None, globals=None):
        return super().get_template(self._themed(name), parent, globals)

    def select_template(self, names, parent=None, globals=None):
        return super().select_template(
            [self._themed(n) for n in names], parent, globals
        )


def make_environment(directory: str = "templates") -> ThemedEnvironment:
    return ThemedEnvironment(
        loader=jinja2.FileSystemLoader(directory), autoescape=True
    )


def _read(scope) -> tuple[str | None, str | None]:
    """Return (theme from query, theme from cookie); each None when absent/invalid."""
    query = parse_qs((scope.get("query_string") or b"").decode("latin-1"))
    from_query = (query.get("theme") or [None])[0]
    from_cookie = None
    for key, value in scope.get("headers") or []:
        if key == b"cookie":
            for part in value.decode("latin-1").split(";"):
                name, _, val = part.strip().partition("=")
                if name == COOKIE_NAME:
                    from_cookie = val
    ok = lambda v: v if v in THEMES else None
    return ok(from_query), ok(from_cookie)


class ThemeMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].startswith("/static/"):
            await self.app(scope, receive, send)
            return

        from_query, from_cookie = _read(scope)
        theme = from_query or from_cookie or default_theme()
        scope = dict(scope)
        state = dict(scope.get("state") or {})
        state["theme"] = theme
        scope["state"] = state

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers") or [])
                content_type = next(
                    (v for k, v in headers if k.lower() == b"content-type"), b""
                )
                if content_type.startswith(b"text/html"):
                    headers.append((b"vary", b"Cookie"))
                    if from_query:
                        headers.append((b"x-robots-tag", b"noindex"))
                if from_query and from_query != from_cookie:
                    secure = "; Secure" if scope.get("scheme") == "https" else ""
                    headers.append((
                        b"set-cookie",
                        f"{COOKIE_NAME}={from_query}; Path=/; Max-Age={COOKIE_MAX_AGE}; SameSite=Lax{secure}".encode(),
                    ))
                message = {**message, "headers": headers}
            await send(message)

        token = set_theme(theme)
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            reset_theme(token)
