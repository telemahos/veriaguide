import jinja2
import pytest

from app.theme import ThemedEnvironment, reset_theme, set_theme


def _env(tmp_path):
    (tmp_path / "v2").mkdir()
    (tmp_path / "a.html").write_text("classic-a")
    (tmp_path / "b.html").write_text("classic-b")
    (tmp_path / "v2" / "a.html").write_text("new-a")
    return ThemedEnvironment(loader=jinja2.FileSystemLoader(str(tmp_path)))


def test_new_theme_prefers_v2_and_falls_back(tmp_path):
    env = _env(tmp_path)
    token = set_theme("new")
    try:
        assert env.get_template("a.html").render() == "new-a"
        assert env.get_template("b.html").render() == "classic-b"
    finally:
        reset_theme(token)


def test_classic_theme_ignores_v2_and_cache_is_not_shared(tmp_path):
    env = _env(tmp_path)
    token = set_theme("new")
    env.get_template("a.html")
    reset_theme(token)
    assert env.get_template("a.html").render() == "classic-a"


@pytest.mark.parametrize("path", ["/", "/el/", "/de/"])
def test_theme_query_sets_cookie_and_noindex(client, path):
    r = client.get(path, params={"theme": "new"})
    assert r.status_code == 200
    assert "vg_theme=new" in r.headers["set-cookie"]
    assert r.headers["x-robots-tag"] == "noindex"
    assert "Cookie" in r.headers["vary"]
    assert "Switch to classic design" in r.text or "classic" in r.text.lower()


def test_cookie_selects_theme_without_query(client):
    client.cookies.set("vg_theme", "new")
    r = client.get("/")
    assert "?theme=classic" in r.text
    assert "x-robots-tag" not in r.headers
    client.cookies.set("vg_theme", "classic")
    assert "?theme=new" in client.get("/").text


def test_invalid_theme_ignored(client):
    r = client.get("/", params={"theme": "bogus"})
    assert r.status_code == 200
    assert "set-cookie" not in r.headers
    assert "?theme=new" in r.text


def test_footer_toggle_translated(client):
    assert "Neues Design ausprobieren" in client.get("/de/").text
    assert "Δοκιμάστε τη νέα εμφάνιση" in client.get("/el/").text
