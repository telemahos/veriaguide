from app.utils.category_urls import (
    build_category_list_url,
    get_category_key_from_url_path,
    get_category_url_path,
    normalize_public_url,
    resolve_legacy_category_path,
)


def test_public_path_uses_hyphens():
    assert get_category_url_path("religious_sites") == "religious-sites"
    assert get_category_url_path("hidden_gems") == "hidden-gems"
    assert get_category_url_path("museums") == "museums"


def test_url_path_maps_back_to_key():
    assert get_category_key_from_url_path("hiking-trails") == "hiking_trails"
    assert get_category_key_from_url_path("nope") is None


def test_legacy_paths_resolve():
    assert resolve_legacy_category_path("/religious_sites") == "/religious-sites"
    assert resolve_legacy_category_path("/ski_resorts/kaimaktsalan") == "/ski-resorts/kaimaktsalan"
    assert resolve_legacy_category_path("/api/religious_sites/autocomplete") == "/api/religious-sites/autocomplete"
    assert resolve_legacy_category_path("/museums") is None
    assert resolve_legacy_category_path("/religious_sitesX") is None


def test_normalize_public_url_keeps_query_and_host():
    assert normalize_public_url("/tours?page=2") == "/tours?page=2"
    assert normalize_public_url("/hidden_gems?page=2") == "/hidden-gems?page=2"
    assert normalize_public_url("https://site.test/ski_resorts/x") == "https://site.test/ski-resorts/x"
    assert normalize_public_url("#") == "#"


def test_build_category_list_url():
    assert build_category_list_url("hiking_trails") == "/hiking-trails"
    assert build_category_list_url("tours", page=3, query_params={"search": "wine", "page": "1"}) == (
        "/tours?search=wine&page=3"
    )
