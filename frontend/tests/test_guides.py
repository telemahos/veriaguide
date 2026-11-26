"""Published guide hub, article pages, and legacy /guides redirects."""
import copy

from app.utils.canonical import GUIDE_REDIRECTS, RESERVED_GUIDE_SLUGS

GUIDE = {
    "id": 90,
    "type": "guide",
    "status": "publish",
    "slug": "weekend-in-veria",
    "modified": "2026-11-01T10:00:00",
    "title": {"rendered": "A weekend in Veria"},
    "excerpt": {"rendered": "<p>Two days in the old town.</p>"},
    "content": {
        "rendered": (
            "<p>Start at the churches.</p>"
            '<p><a href="/religious-sites/old-metropolis">Old Metropolis</a></p>'
        )
    },
    "meta": {
        "title_el": "Σαββατοκύριακο στη Βέροια",
        "excerpt_el": "<p>Δύο ημέρες στην παλιά πόλη.</p>",
        "content_el": "<p>Ξεκινήστε από τους ναούς.</p>",
        "seo_title_en": "A weekend in Veria | VeriaGuide",
        "seo_description_en": "How to spend a weekend in Veria and Imathia.",
    },
}


def test_reserved_slugs_are_not_legacy_redirects():
    for slug in RESERVED_GUIDE_SLUGS:
        assert f"/guides/{slug}" not in GUIDE_REDIRECTS
    assert "/guides" not in GUIDE_REDIRECTS


def test_published_guide_and_hub(client, fake_wp):
    fake_wp.posts.append(copy.deepcopy(GUIDE))
    draft = copy.deepcopy(GUIDE)
    draft["id"] = 91
    draft["slug"] = "ski-vermio-2026-27"
    draft["status"] = "draft"
    draft["title"] = {"rendered": "Draft ski guide"}
    fake_wp.posts.append(draft)

    detail = client.get("/guides/weekend-in-veria")
    assert detail.status_code == 200
    assert "<h1" in detail.text
    assert "A weekend in Veria" in detail.text
    assert "Two days in the old town." in detail.text
    assert "Old Metropolis" in detail.text
    assert '"@type": "Article"' in detail.text
    assert '"@type": "BreadcrumbList"' in detail.text
    assert "Home" in detail.text
    assert ">Guides<" in detail.text or "Guides" in detail.text

    greek = client.get("/el/guides/weekend-in-veria")
    assert greek.status_code == 200
    assert "Σαββατοκύριακο στη Βέροια" in greek.text
    assert "Οδηγοί" in greek.text

    german = client.get("/de/guides/weekend-in-veria")
    assert german.status_code == 200
    assert "Guides für Veria" not in german.text or "weekend" in german.text.lower() or "Veria" in german.text

    hub = client.get("/guides")
    assert hub.status_code == 200
    assert "Guides to Veria | VeriaGuide" in hub.text
    assert "weekend-in-veria" in hub.text
    assert "Draft ski guide" not in hub.text

    el_hub = client.get("/el/guides")
    assert el_hub.status_code == 200
    assert "Οδηγοί για τη Βέροια | VeriaGuide" in el_hub.text

    assert client.get("/guides/christmas-in-veria-2026").status_code == 404
    assert client.get("/guides/not-a-real-guide").status_code == 404
    assert client.get("/guides/ski-vermio-2026-27").status_code == 404

    home = client.get("/").text
    assert 'href="/guides"' in home


def test_empty_hub_has_no_nav_link_and_skips_sitemap(client):
    hub = client.get("/guides")
    assert hub.status_code == 200
    assert "No guides have been published yet." in hub.text
    home = client.get("/").text
    assert 'href="/guides"' not in home
    sitemap = client.get("/sitemap.xml").text
    assert "/guides</loc>" not in sitemap
    assert "/guides/" not in sitemap


def test_sitemap_lists_only_published_guides(client, fake_wp):
    fake_wp.posts.append(copy.deepcopy(GUIDE))
    xml = client.get("/sitemap.xml").text
    assert "/guides</loc>" in xml
    assert "/guides/weekend-in-veria</loc>" in xml
    assert "ski-vermio-2026-27" not in xml


def test_legacy_guide_slugs_still_redirect(client):
    response = client.get("/guides/kyriotissa", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/religious-sites"
    response = client.get("/guides/one-day-in-veria", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/about"
    response = client.get("/guides/barbouta", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/archaeological-sites"


def test_mu_plugin_registers_guide_and_english_seo():
    from pathlib import Path

    source = Path(__file__).resolve().parents[2].joinpath(
        "wordpress/mu-plugins/veriaguide-guides.php"
    ).read_text()
    assert "'rest_base' => 'guides'" in source
    for key in (
        "title_el", "content_el", "excerpt_el",
        "title_de", "content_de", "excerpt_de",
        "seo_title_el", "seo_description_el",
        "seo_title_de", "seo_description_de",
        "seo_title_en", "seo_description_en",
    ):
        assert f"'{key}'" in source
    for post_type in (
        "museum", "archaeological_site", "religious_site", "hiking_trail",
        "restaurant", "cafe", "accommodation", "ski_resort", "tour", "hidden_gem", "guide",
    ):
        assert f"'{post_type}'" in source
    assert "'show_in_rest' => true" in source
    assert "current_user_can('edit_posts')" in source
    assert "seo_tittle" not in source
