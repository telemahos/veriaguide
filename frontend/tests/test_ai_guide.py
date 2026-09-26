import copy
import json
from datetime import date, timedelta

import pytest

from tests.conftest import SAMPLE_POST

STEPS = ("dates", "party", "interests", "budget", "wishes", "review")


def _itinerary(venue_id=1):
    return json.dumps(
        {
            "title": "Byzantine Veria",
            "summary": "A calm day.",
            "days": [{"day": 1, "title": "Old town", "slots": [{"time": "10:00", "venue_id": venue_id, "note": "Go early"}]}],
        }
    )


@pytest.fixture
def guide(monkeypatch, fake_wp):
    from app.ai_guide import llm, store

    monkeypatch.setenv("AI_GUIDE_ENABLED", "true")
    monkeypatch.setenv("AI_GUIDE_RATE_LIMIT", "5")
    memory = store.MemoryStore()
    store.set_store(memory)
    calls = []

    async def fake_complete(messages):
        calls.append(messages)
        return _itinerary()

    llm.set_completer(fake_complete)
    tour = copy.deepcopy(SAMPLE_POST)
    tour.update(id=99, slug="wine-tour", type="tour", title={"rendered": "Secret Tours Package"})
    fake_wp.posts.append(tour)
    yield {"calls": calls, "store": memory, "wp": fake_wp, "llm": llm}
    llm.set_completer(None)
    store.set_store(store.RedisStore())


def _csrf(client, path):
    html = client.get(path).text
    marker = 'name="csrf" value="'
    return html.split(marker, 1)[1].split('"', 1)[0]


def _walk(client, prefix=""):
    response = client.post(f"{prefix}/ai-guide/start")
    assert response.status_code == 303
    assert response.headers["location"] == f"{prefix}/ai-guide/dates"
    start = date.today() + timedelta(days=3)
    forms = {
        "dates": {"start_date": start.isoformat(), "end_date": (start + timedelta(days=1)).isoformat()},
        "party": {"party": "couple"},
        "interests": {"interests": ["churches", "museums"]},
        "budget": {"budget": "mid"},
        "wishes": {"wishes": "quiet places"},
    }
    for step, data in forms.items():
        csrf = _csrf(client, f"{prefix}/ai-guide/{step}")
        response = client.post(f"{prefix}/ai-guide/{step}", data={**data, "csrf": csrf})
        assert response.status_code == 303, (step, response.text[:300])
    csrf = _csrf(client, f"{prefix}/ai-guide/review")
    return client.post(f"{prefix}/ai-guide/generate", data={"csrf": csrf})


@pytest.mark.parametrize("path", ["/ai-guide", "/el/ai-guide", "/de/ai-guide", "/ai-guide/dates", "/ai-guide/trip/abc"])
def test_flag_off_returns_404(client, monkeypatch, path):
    monkeypatch.delenv("AI_GUIDE_ENABLED", raising=False)
    assert client.get(path).status_code == 404
    assert client.post("/ai-guide/start").status_code == 404


def test_footer_hides_link_when_off(client, monkeypatch):
    monkeypatch.delenv("AI_GUIDE_ENABLED", raising=False)
    assert 'href="/ai-guide"' not in client.get("/about").text


@pytest.mark.parametrize("prefix", ["", "/de"])
def test_happy_path(client, guide, prefix):
    assert client.get(f"{prefix}/ai-guide").status_code == 200
    response = _walk(client, prefix)
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith(f"{prefix}/ai-guide/trip/")
    page = client.get(location)
    assert page.status_code == 200
    assert "noindex" in page.headers["x-robots-tag"]
    assert f'href="{prefix}/religious-sites/sample-place"' in page.text
    assert "Go early" in page.text
    assert len(guide["calls"]) == 1


def test_step_without_session_redirects(client, guide):
    for step in STEPS:
        response = client.get(f"/el/ai-guide/{step}")
        assert response.status_code == 303
        assert response.headers["location"] == "/el/ai-guide"
    client.cookies.set("vg_aiguide", "unknown")
    assert client.get("/ai-guide/budget").headers["location"] == "/ai-guide"


def test_skipping_steps_redirects(client, guide):
    client.post("/ai-guide/start")
    assert client.get("/ai-guide/review").headers["location"] == "/ai-guide"


def test_invalid_csrf_rejected(client, guide):
    client.post("/ai-guide/start")
    response = client.post("/ai-guide/dates", data={"start_date": "2030-01-01", "end_date": "2030-01-02", "csrf": "x"})
    assert response.status_code == 400


def test_prompt_never_includes_tours(client, guide, monkeypatch):
    from app.ai_guide.interests import INTEREST_CATEGORIES, categories_for

    all_interests = list(INTEREST_CATEGORIES)
    assert "tours" not in categories_for(all_interests)
    _walk(client)
    prompt = json.dumps(guide["calls"][0]).lower()
    assert "tour" not in prompt
    assert not any("/tours" in str(req[1]) for req in guide["wp"].requests)


def test_invalid_json_shows_retry_page(client, guide):
    async def broken(messages):
        return "not json {"

    guide["llm"].set_completer(broken)
    response = _walk(client)
    assert response.status_code == 200
    assert "try again" in response.text.lower()


def test_unknown_venue_ids_show_retry_page(client, guide):
    async def invented(messages):
        return _itinerary(venue_id=12345)

    guide["llm"].set_completer(invented)
    response = _walk(client)
    assert response.status_code == 200
    assert "Something went wrong" in response.text


def test_rate_limit(client, guide, monkeypatch):
    monkeypatch.setenv("AI_GUIDE_RATE_LIMIT", "1")
    assert _walk(client).status_code == 303
    csrf = _csrf(client, "/ai-guide/review")
    assert client.post("/ai-guide/generate", data={"csrf": csrf}).status_code == 429


def test_invalid_dates_show_error(client, guide):
    client.post("/ai-guide/start")
    csrf = _csrf(client, "/ai-guide/dates")
    start = date.today() + timedelta(days=1)
    response = client.post(
        "/ai-guide/dates",
        data={"start_date": start.isoformat(), "end_date": (start + timedelta(days=10)).isoformat(), "csrf": csrf},
    )
    assert response.status_code == 422
    assert "at most 7 days" in response.text
