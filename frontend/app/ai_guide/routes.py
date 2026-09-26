"""/ai-guide wizard, generation and result pages. /el and /de are handled by LocaleMiddleware."""
import hashlib
import hmac
import os
import secrets
from collections.abc import Callable
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.ai_guide import config, session
from app.ai_guide.interests import INTEREST_CATEGORIES, INTEREST_LABELS
from app.ai_guide.llm import ItineraryError, generate
from app.ai_guide.models import BUDGETS, PARTIES, WizardState
from app.ai_guide.prompt import build_messages
from app.ai_guide.retrieval import retrieve
from app.ai_guide.routing import alternatives, route_for_itinerary
from app.ai_guide.store import get_store
from app.i18n import current_lang, lang_prefix
from app.utils.helpers import get_meta_data
from app.utils.logging_config import get_logger

logger = get_logger("ai_guide")

STEPS = ("dates", "party", "interests", "budget", "wishes", "review")


def require_enabled() -> None:
    if not config.is_enabled():
        raise HTTPException(status_code=404)


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(f"{lang_prefix()}/ai-guide{path}", status_code=303)


def _step_done(state: WizardState, step: str) -> bool:
    return {
        "dates": state.start_date is not None,
        "party": state.party is not None,
        "interests": state.interests_done,
        "budget": state.budget is not None,
        "wishes": state.wishes_done,
        "review": False,
    }[step]


def _can_open(state: WizardState, step: str) -> bool:
    return all(_step_done(state, previous) for previous in STEPS[: STEPS.index(step)])


def _day_dates(start: str | None, count: int) -> list[str]:
    try:
        first = date.fromisoformat(start or "")
    except ValueError:
        return [""] * count
    return [(first + timedelta(days=offset)).strftime("%d.%m.%Y") for offset in range(count)]


ADMIN_COOKIE = "vg_aiguide_admin"


def _admin_token() -> str:
    secret = os.getenv("ADMIN_API_KEY", "").strip()
    if not secret:
        return ""
    return hmac.new(secret.encode(), b"veriaguide-ai-guide", hashlib.sha256).hexdigest()


def _admin_unlocked(request: Request) -> bool:
    expected = _admin_token()
    got = request.cookies.get(ADMIN_COOKIE, "")
    return bool(expected and got) and hmac.compare_digest(got, expected)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _apply(state: WizardState, step: str, form) -> str | None:
    """Validate one step's form into state. Returns an error message or None."""
    if step == "dates":
        try:
            start = date.fromisoformat(str(form.get("start_date", "")))
            end = date.fromisoformat(str(form.get("end_date", "")))
        except ValueError:
            return "Please choose valid dates."
        if start < date.today() - timedelta(days=1) or end < start:
            return "Please choose valid dates."
        if (end - start).days + 1 > config.MAX_DAYS:
            return f"Trips can be at most {config.MAX_DAYS} days."
        state.start_date, state.end_date = start, end
    elif step == "party":
        party = form.get("party")
        if party not in PARTIES:
            return "Please choose who is travelling."
        state.party = party
    elif step == "interests":
        state.interests = [i for i in form.getlist("interests") if i in INTEREST_CATEGORIES]
        state.interests_done = True
    elif step == "budget":
        budget = form.get("budget")
        if budget not in BUDGETS:
            return "Please choose a budget."
        state.budget = budget
    elif step == "wishes":
        state.wishes = " ".join(str(form.get("wishes", "")).split())[: config.MAX_WISHES]
        state.wishes_done = True
    return None


def create_router(templates: Jinja2Templates, common_data: Callable) -> APIRouter:
    router = APIRouter(prefix="/ai-guide", dependencies=[Depends(require_enabled)])

    def render(name: str, commons: dict, status_code: int = 200, **context) -> HTMLResponse:
        data = {
            **commons,
            "meta": get_meta_data(title="AI Travel Guide", robots="noindex, nofollow"),
            "steps": STEPS,
            **context,
        }
        response = templates.TemplateResponse(
            request=commons["request"], name=f"ai_guide/{name}", context=data, status_code=status_code
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    async def check_csrf(request: Request, state: WizardState):
        form = await request.form()
        if not secrets.compare_digest(str(form.get("csrf", "")), state.csrf):
            raise HTTPException(status_code=400, detail="Invalid form token")
        return form

    async def run_generation(request: Request, state: WizardState, commons: dict):
        store = get_store()
        if not _admin_unlocked(request):
            hits = await store.incr(f"rate:{_client_ip(request)}", 3600)
            if hits > config.rate_limit():
                return render("retry.html", commons, status_code=429, reason="rate_limit", state=state)
        venues = await retrieve(state, config.max_venues())
        if not venues:
            return render("retry.html", commons, reason="no_venues", state=state)
        lang = current_lang()
        messages = build_messages(state, venues, lang)
        try:
            itinerary = await generate(messages, {v["id"] for v in venues}, max(1, state.days))
        except ItineraryError:
            return render("retry.html", commons, reason="llm", state=state)
        trip_id = secrets.token_urlsafe(12)
        record = {
            "itinerary": itinerary.model_dump(mode="json"),
            "venues": {str(v["id"]): v for v in venues},
            "state": state.model_dump(mode="json"),
            "lang": lang,
            "edit_token": secrets.token_urlsafe(16),
        }
        await store.set(f"it:{trip_id}", record, config.itinerary_ttl())
        return _redirect(f"/trip/{trip_id}")

    @router.get("", response_class=HTMLResponse)
    async def start_page(commons: dict = Depends(common_data)):
        return render("start.html", commons)

    @router.post("/start")
    async def start():
        response = _redirect("/dates")
        await session.create(response)
        return response

    @router.get("/unlock", response_class=HTMLResponse)
    async def unlock_form(commons: dict = Depends(common_data)):
        return render("unlock.html", commons, error=False)

    @router.post("/unlock")
    async def unlock_submit(request: Request):
        form = await request.form()
        expected = os.getenv("ADMIN_API_KEY", "").strip()
        given = str(form.get("key", ""))
        if not expected or not hmac.compare_digest(given, expected):
            raise HTTPException(status_code=403, detail="Unauthorized")
        response = _redirect("")
        response.set_cookie(
            ADMIN_COOKIE,
            _admin_token(),
            max_age=12 * 3600,
            httponly=True,
            secure=config.secure_cookies(),
            samesite="lax",
            path="/",
        )
        return response

    @router.post("/generate", response_class=HTMLResponse)
    async def generate_trip(request: Request, commons: dict = Depends(common_data)):
        state = await session.load(request)
        if not state or not _can_open(state, "review"):
            return _redirect("")
        await check_csrf(request, state)
        return await run_generation(request, state, commons)

    @router.get("/trip/{trip_id}", response_class=HTMLResponse)
    async def trip_page(trip_id: str, request: Request, commons: dict = Depends(common_data)):
        record = await get_store().get(f"it:{trip_id}") if len(trip_id) <= 32 else None
        if not record:
            raise HTTPException(status_code=404)
        if not record.get("edit_token"):
            record["edit_token"] = secrets.token_urlsafe(16)
            await get_store().set(f"it:{trip_id}", record, config.itinerary_ttl())
        state = await session.load(request)
        itinerary = record["itinerary"]
        venues = record["venues"]
        used = {int(slot["venue_id"]) for day in itinerary["days"] for slot in day["slots"]}
        choices = {}
        for day in itinerary["days"]:
            for index, slot in enumerate(day["slots"]):
                current = venues.get(str(slot["venue_id"]))
                if current:
                    choices[f"{day['day']}-{index}"] = alternatives(current, venues, used)
        return render(
            "result.html",
            commons,
            trip_id=trip_id,
            itinerary=itinerary,
            venues=venues,
            trip=record["state"],
            day_dates=_day_dates(record["state"].get("start_date"), len(itinerary["days"])),
            stop_count=sum(
                1 for day in itinerary["days"] for slot in day["slots"] if str(slot["venue_id"]) in venues
            ),
            csrf=state.csrf if state else None,
            edit_token=record["edit_token"],
            choices=choices,
            route=await route_for_itinerary(itinerary, venues),
            needs_leaflet=True,
            interest_labels=INTEREST_LABELS,
        )

    @router.post("/trip/{trip_id}/swap")
    async def swap_stop(trip_id: str, request: Request):
        record = await get_store().get(f"it:{trip_id}") if len(trip_id) <= 32 else None
        if not record:
            raise HTTPException(status_code=404)
        form = await request.form()
        if not hmac.compare_digest(str(form.get("edit_token", "")), str(record.get("edit_token", ""))):
            raise HTTPException(status_code=403, detail="Unauthorized")
        try:
            day_number = int(form.get("day"))
            slot_index = int(form.get("slot"))
            venue_id = int(form.get("venue_id"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid stop") from None
        if str(venue_id) not in record["venues"]:
            raise HTTPException(status_code=400, detail="Unknown place")
        for day in record["itinerary"]["days"]:
            if int(day["day"]) != day_number:
                continue
            if slot_index < 0 or slot_index >= len(day["slots"]):
                break
            day["slots"][slot_index]["venue_id"] = venue_id
            day["slots"][slot_index]["note"] = ""
            await get_store().set(f"it:{trip_id}", record, config.itinerary_ttl())
            return _redirect(f"/trip/{trip_id}#day-{day_number}")
        raise HTTPException(status_code=400, detail="Invalid stop")

    @router.post("/trip/{trip_id}/regenerate", response_class=HTMLResponse)
    async def regenerate(trip_id: str, request: Request, commons: dict = Depends(common_data)):
        state = await session.load(request)
        record = await get_store().get(f"it:{trip_id}") if len(trip_id) <= 32 else None
        if not state or not record:
            return _redirect("")
        await check_csrf(request, state)
        return await run_generation(request, WizardState.model_validate(record["state"]), commons)

    @router.get("/{step}", response_class=HTMLResponse)
    async def step_page(step: str, request: Request, commons: dict = Depends(common_data)):
        if step not in STEPS:
            raise HTTPException(status_code=404)
        state = await session.load(request)
        if not state or not _can_open(state, step):
            return _redirect("")
        return render(
            "review.html" if step == "review" else "step.html",
            commons,
            step=step,
            state=state,
            parties=PARTIES,
            budgets=BUDGETS,
            interest_labels=INTEREST_LABELS,
            today=date.today().isoformat(),
            max_days=config.MAX_DAYS,
        )

    @router.post("/{step}", response_class=HTMLResponse)
    async def step_submit(step: str, request: Request, commons: dict = Depends(common_data)):
        if step not in STEPS or step == "review":
            raise HTTPException(status_code=404)
        state = await session.load(request)
        if not state or not _can_open(state, step):
            return _redirect("")
        form = await check_csrf(request, state)
        error = _apply(state, step, form)
        if error:
            return render(
                "step.html",
                commons,
                status_code=422,
                step=step,
                state=state,
                error=error,
                parties=PARTIES,
                budgets=BUDGETS,
                interest_labels=INTEREST_LABELS,
                today=date.today().isoformat(),
                max_days=config.MAX_DAYS,
            )
        await session.save(request, state)
        return _redirect(f"/{STEPS[STEPS.index(step) + 1]}")

    return router
