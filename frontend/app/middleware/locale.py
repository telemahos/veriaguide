"""Serve /el/... and /de/... with the same routes as English and remember the language."""
from app.i18n import PREFIX_LANGS, reset_lang, set_lang


class LocaleMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or "/"
        lang = "en"
        for code in PREFIX_LANGS:
            prefix = f"/{code}"
            if path == prefix or path.startswith(prefix + "/"):
                lang = code
                rest = path[len(prefix):] or "/"
                if not rest.startswith("/"):
                    rest = "/" + rest
                scope = dict(scope)
                scope["path"] = rest
                scope["raw_path"] = rest.encode("ascii", "ignore")
                break

        scope = dict(scope)
        state = dict(scope.get("state") or {})
        state["lang"] = lang
        scope["state"] = state

        token = set_lang(lang)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_lang(token)
