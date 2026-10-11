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


@pytest.mark.parametrize("path,skip", [
    ("/", "Skip to main content"),
    ("/el/", "Μετάβαση στο κύριο περιεχόμενο"),
    ("/de/", "Zum Hauptinhalt springen"),
])
def test_new_theme_shell_renders_on_all_languages(client, path, skip):
    html = client.get(path, params={"theme": "new"}).text
    assert 'class="theme-new"' in html
    assert skip in html
    assert 'id="main"' in html
    assert "vg-header" in html and "vg-footer" in html
    assert "/static/css/v2/all.css" in html
    # head/SEO still comes from the classic layout
    assert 'rel="canonical"' in html and 'hreflang="de"' in html
    assert "googletagmanager.com/gtag/js" in html and 'id="cookie-consent"' in html
    assert html.count('id="favorites-count"') == 1


def test_classic_has_no_v2_assets(client):
    html = client.get("/").text
    assert "theme-new" not in html and "/static/css/v2/" not in html
    assert 'class="site-header"' in html


@pytest.mark.parametrize("path", ["/", "/el/", "/de/"])
def test_new_home_renders_hero_search_and_tiles(client, path):
    html = client.get(path, params={"theme": "new"}).text
    assert 'class="vg-hero"' in html and "<h1" in html
    assert 'fetchpriority="high"' in html
    assert 'role="combobox"' in html and "/static/js/v2/search.js" in html
    assert "vg-tiles" in html and "/static/css/v2/all.css" in html
    assert html.count("<h1") == 1


def test_new_hub_keeps_classic_script_hooks(client):
    html = client.get("/religious-sites", params={"theme": "new"}).text
    for hook in ('id="sidebar-map"', 'id="filter-form"', 'id="search-input"',
                 'id="autocomplete-results"', "initializeDirectorySidebarMap"):
        assert hook in html, hook
    assert "vg-pagehead" in html and 'class="theme-new"' in html
    assert 'class="vg-card category-listing"' in html and "add-favorite" in html and "data-vg-card-title" in html


def test_classic_home_unchanged_by_v2(client):
    html = client.get("/", params={"theme": "classic"}).text
    assert "hero-section" in html and "vg-hero" not in html


@pytest.mark.parametrize("prefix,cat", [("", "museums"), ("/el", "restaurants"), ("/de", "religious-sites"), ("", "cafes")])
def test_new_detail_has_breadcrumbs_sectionnav_and_keeps_seo(client, prefix, cat):
    r = client.get(f"{prefix}/{cat}/sample-place", params={"theme": "new"})
    assert r.status_code == 200
    html = r.text
    assert "vg-breadcrumbs" in html and "vg-sectionnav" in html
    assert "/static/js/v2/detail.js" in html and "/static/css/v2/all.css" in html
    assert html.count("<h1") == 1
    assert 'rel="canonical"' in html and 'hreflang="el"' in html
    assert "add-favorite" in html


def test_new_detail_sections_have_anchor_ids(client):
    html = client.get("/museums/sample-place", params={"theme": "new"}).text
    assert 'data-vg-section' in html and 'id="sec-about"' in html


def test_classic_detail_unchanged(client):
    html = client.get("/museums/sample-place").text
    assert "vg-breadcrumbs" not in html and "detail-page-header" in html


@pytest.mark.parametrize("path,needle", [
    ("/no-such-page-xyz", "Page Not Found"),
    ("/el/no-such-page-xyz", "Μετάβαση στο κύριο περιεχόμενο"),
    ("/de/no-such-page-xyz", "Zum Hauptinhalt springen"),
])
def test_new_404_is_v2_and_has_search(client, path, needle):
    r = client.get(path, params={"theme": "new"})
    assert r.status_code == 404
    assert "vg-error" in r.text and 'role="combobox"' in r.text
    assert needle in r.text
    assert "bootstrap" not in r.text


def test_classic_404_unchanged(client):
    r = client.get("/no-such-page-xyz")
    assert r.status_code == 404 and "error-container" in r.text


@pytest.mark.parametrize("path", ["/search", "/el/search", "/de/search"])
def test_new_search_empty_and_results(client, path):
    html = client.get(path, params={"theme": "new"}).text
    assert 'role="combobox"' in html and "vg-pagehead" in html
    html = client.get(path, params={"theme": "new", "q": "sample"}).text
    assert "vg-chips" in html and 'id="search-results-map"' in html and 'id="resultsPerPage"' in html
    assert "search-result-link" in html and html.count("<h1") == 1


def test_new_ai_guide_uses_v2_css_and_keeps_scripts(client, monkeypatch):
    monkeypatch.setenv("AI_GUIDE_ENABLED", "true")
    r = client.get("/ai-guide", params={"theme": "new"})
    if r.status_code == 404:
        pytest.skip("AI guide disabled in this test configuration")
    assert "/static/css/v2/ai-guide.css" in r.text and "/static/css/ai-guide.css" in r.text
    assert "/static/js/ai-guide.js" in r.text and 'class="ag ' in r.text


def test_v2_css_bundle_is_up_to_date():
    from scripts.build_v2_css import OUTPUT, build
    assert OUTPUT.read_text() == build(), "run: python scripts/build_v2_css.py"


@pytest.mark.parametrize("path", ["/", "/religious-sites", "/museums/sample-place", "/search", "/contact", "/about"])
def test_new_theme_does_not_load_bootstrap(client, path):
    html = client.get(path, params={"theme": "new"}).text
    assert "bootstrap" not in html.lower()
    assert "/static/css/v2/all.css" in html and "/static/js/v2/ui.js" in html


def test_new_theme_uses_trimmed_fontawesome_and_all_used_icons_exist():
    import re
    from pathlib import Path
    css = Path("static/vendor/fontawesome-lite/all.min.css").read_text()
    full = Path("static/vendor/fontawesome/css/all.min.css").read_text()
    root = Path(".")
    used = set()
    for pat in ("templates/**/*.html", "static/js/**/*.js", "app/**/*.py"):
        for p in root.glob(pat):
            if "admin" not in p.parts:
                used |= set(re.findall(r"\bfa-[a-z0-9-]+", p.read_text(errors="ignore")))
    icons_in_full = set(re.findall(r"\.(fa-[a-z0-9-]+):before", full))
    icons_in_lite = set(re.findall(r"\.(fa-[a-z0-9-]+):before", css))
    assert (used & icons_in_full) <= icons_in_lite, "run: python scripts/build_fa_lite.py"


def test_new_theme_html_loads_lite_fa_not_full(client):
    html = client.get("/", params={"theme": "new"}).text
    assert "fontawesome-lite/all.min.css" in html and "vendor/fontawesome/css" not in html
    assert "vendor/fontawesome/css" in client.get("/", params={"theme": "classic"}).text
