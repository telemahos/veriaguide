"""Normalize HEAD requests so GET routes respond with headers and an empty body."""
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class HeadMethodMiddleware:
    """Treat HEAD like GET for all routes (fixes FastAPI/Starlette 405 on HEAD)."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or scope.get("method") != "HEAD":
            await self.app(scope, receive, send)
            return

        scope = dict(scope)
        scope["method"] = "GET"

        async def send_head(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (k, v)
                    for k, v in message.get("headers", [])
                    if k.lower() != b"content-length"
                ]
                await send({**message, "headers": headers})
                return
            if message["type"] == "http.response.body":
                # Discard payload frames; emit a single empty body at the end.
                if message.get("more_body", False):
                    return
                await send({"type": "http.response.body", "body": b"", "more_body": False})
                return
            await send(message)

        await self.app(scope, receive, send_head)
