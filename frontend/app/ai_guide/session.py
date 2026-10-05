"""Server-side wizard state, referenced by an opaque httponly cookie."""
import secrets

from fastapi import Request, Response

from app.ai_guide import config
from app.ai_guide.models import WizardState
from app.ai_guide.store import get_store

COOKIE = "vg_aiguide"


def _key(sid: str) -> str:
    return f"sess:{sid}"


async def load(request: Request) -> WizardState | None:
    sid = request.cookies.get(COOKIE)
    if not sid or len(sid) > 64:
        return None
    data = await get_store().get(_key(sid))
    if not data:
        return None
    try:
        return WizardState.model_validate(data)
    except ValueError:
        return None


async def save(request: Request, state: WizardState) -> None:
    sid = request.cookies.get(COOKIE)
    if sid:
        await get_store().set(_key(sid), state.model_dump(mode="json"), config.SESSION_TTL)


async def create(response: Response) -> WizardState:
    sid = secrets.token_urlsafe(24)
    state = WizardState(csrf=secrets.token_urlsafe(16))
    await get_store().set(_key(sid), state.model_dump(mode="json"), config.SESSION_TTL)
    response.set_cookie(
        COOKIE,
        sid,
        max_age=config.SESSION_TTL,
        httponly=True,
        secure=config.secure_cookies(),
        samesite="lax",
        path="/",
    )
    return state
