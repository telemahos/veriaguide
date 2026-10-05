from app.utils.helpers import listing_matches_query


CHURCH = {
    "id": 42,
    "slug": "church-of-christ",
    "title": {"rendered": "Church of Christ"},
    "excerpt": {"rendered": "<p>Byzantine church in Veria.</p>"},
    "content": {"rendered": "<p>English body text.</p>"},
    "meta": {
        "title_el": "Εκκλησία του Χριστού",
        "excerpt_el": "<p>Βυζαντινός ναός στη Βέροια.</p>",
        "content_el": "<p>Ο ναός είναι αφιερωμένος στον Χριστό.</p>",
    },
    "acf": {"address": "Veria"},
}

FLORETTA = {
    "id": 1400,
    "slug": "floretta",
    "type": "cafe",
    "title": {"rendered": "Floretta"},
    "excerpt": {"rendered": "<p>Cafe-bar at 54 Mitropoleos Street.</p>"},
    "content": {"rendered": "<p>Floretta is a cafe-bar in central Veria.</p>"},
    "meta": {
        "_acf_changed": True,
        "title_el": "Φλωρέττα",
        "excerpt_el": "Καφέ-μπαρ στη Μητροπόλεως 54.",
        "content_el": "<p>Η Φλωρέττα είναι καφέ-μπαρ.</p>",
    },
    "acf": {"address": "Mitropoleos 54, Veria", "city": "Veria"},
}


def test_greek_title_el_matches_without_english_title():
    assert listing_matches_query(CHURCH, "Εκκλησία του Χριστού")
    assert listing_matches_query(CHURCH, "εκκλησια του χριστου")


def test_greek_body_meta_matches():
    assert listing_matches_query(CHURCH, "αφιερωμένος")


def test_english_title_and_body_still_match():
    assert listing_matches_query(CHURCH, "Church of Christ")
    assert listing_matches_query(CHURCH, "Byzantine church")


def test_unrelated_query_does_not_match():
    assert not listing_matches_query(CHURCH, "ski resort")


def test_floretta_live_shaped_meta_matches_greek_name():
    assert listing_matches_query(FLORETTA, "Φλωρέττα")
    assert listing_matches_query(FLORETTA, "φλωρεττα")
    assert listing_matches_query(FLORETTA, "floretta")


def test_list_valued_translation_meta_matches():
    post = {
        **FLORETTA,
        "meta": {"title_el": ["Φλωρέττα"], "content_el": ["<p>Η Φλωρέττα.</p>"]},
    }
    assert listing_matches_query(post, "Φλωρέττα")


def test_search_page_returns_listing_for_greek_title_el(client, fake_wp):
    fake_wp.posts[0]["title"] = {"rendered": "Church of Christ"}
    fake_wp.posts[0]["meta"] = {
        "title_el": "Εκκλησία του Χριστού",
        "content_el": "<p>Ο ναός είναι αφιερωμένος στον Χριστό.</p>",
    }

    greek = client.get("/search", params={"q": "Εκκλησία του Χριστού"})
    assert greek.status_code == 200
    assert "Church of Christ" in greek.text
    assert "No results found for" not in greek.text

    english = client.get("/search", params={"q": "Church of Christ"})
    assert english.status_code == 200
    assert "Church of Christ" in english.text


def test_el_search_finds_floretta_by_greek_title(client, fake_wp):
    fake_wp.posts[:] = [dict(FLORETTA)]

    response = client.get("/el/search", params={"q": "Φλωρέττα"})
    assert response.status_code == 200
    assert "floretta" in response.text.lower()
    assert "No results found for" not in response.text
    assert "Δεν βρέθηκαν αποτελέσματα" not in response.text


def test_el_search_church_of_christ_returns_religious_hits(client, fake_wp):
    fake_wp.posts[:] = [
        {
            "id": 42,
            "slug": "church-of-christ",
            "type": "religious_site",
            "title": {"rendered": "Church of Christ"},
            "excerpt": {"rendered": "<p>Byzantine church.</p>"},
            "content": {"rendered": "<p>English body.</p>"},
            "meta": {"title_el": "Εκκλησία του Χριστού"},
            "acf": {},
        },
        {
            "id": 43,
            "slug": "old-metropolis",
            "type": "religious_site",
            "title": {"rendered": "Old Metropolis"},
            "excerpt": {"rendered": "<p>Church of Christ precinct.</p>"},
            "content": {"rendered": "<p>Related church.</p>"},
            "meta": {
                "title_el": "Παλαιά Μητρόπολη",
                "content_el": "<p>Κοντά στην Εκκλησία του Χριστού.</p>",
            },
            "acf": {},
        },
    ]

    response = client.get(
        "/el/search",
        params={"q": "Εκκλησία του Χριστού", "type": "religious_sites"},
    )
    assert response.status_code == 200
    assert "church-of-christ" in response.text
    assert "old-metropolis" in response.text
    assert "No results found for" not in response.text


def test_type_all_is_accepted(client, fake_wp):
    fake_wp.posts[:] = [dict(FLORETTA)]

    response = client.get("/el/search", params={"q": "Φλωρέττα", "type": "all"})
    assert response.status_code == 200
    assert response.text != "Invalid content type"
    assert "floretta" in response.text.lower()


def test_type_all_uppercase_is_accepted(client, fake_wp):
    response = client.get("/search", params={"q": "test", "type": "ALL"})
    assert response.status_code == 200
    assert "Invalid content type" not in response.text


def test_typed_category_filter_still_validates(client, fake_wp):
    ok = client.get("/search", params={"q": "test", "type": "cafes"})
    assert ok.status_code == 200

    bad = client.get("/search", params={"q": "test", "type": "spaceships"})
    assert bad.status_code == 400
    assert "Invalid content type" in bad.text


def test_category_list_search_uses_title_el(client, fake_wp):
    fake_wp.posts[0]["title"] = {"rendered": "Church of Christ"}
    fake_wp.posts[0]["meta"] = {"title_el": "Εκκλησία του Χριστού"}

    response = client.get("/religious-sites", params={"search": "Εκκλησία του Χριστού"})
    assert response.status_code == 200
    assert "Church of Christ" in response.text


def test_empty_all_posts_are_not_written_to_redis(monkeypatch, fake_wp):
    import asyncio

    from app.api.wordpress import get_all_posts_for_type
    from app.services.cache_service import CacheService

    writes = []

    async def capture_set(key, value, ttl=None, params=None):
        writes.append((key, value))
        return True

    async def miss(*args, **kwargs):
        return None

    monkeypatch.setattr(CacheService, "get", staticmethod(miss))
    monkeypatch.setattr(CacheService, "set", staticmethod(capture_set))
    fake_wp.posts = []

    result = asyncio.run(get_all_posts_for_type("cafe"))
    assert result == []
    assert writes == []


def test_nonempty_all_posts_are_cached(monkeypatch, fake_wp):
    import asyncio

    from app.api.wordpress import get_all_posts_for_type
    from app.services.cache_service import CacheService

    writes = []

    async def capture_set(key, value, ttl=None, params=None):
        writes.append((key, value))
        return True

    async def miss(*args, **kwargs):
        return None

    monkeypatch.setattr(CacheService, "get", staticmethod(miss))
    monkeypatch.setattr(CacheService, "set", staticmethod(capture_set))

    result = asyncio.run(get_all_posts_for_type("cafe"))
    assert len(result) == 1
    assert writes and writes[0][0] == "all_posts_v2_cafe"
    assert len(writes[0][1]) == 1


def test_empty_cached_all_posts_are_refetched(monkeypatch, fake_wp):
    import asyncio

    from app.api.wordpress import get_all_posts_for_type
    from app.services.cache_service import CacheService

    writes = []

    async def poisoned_get(*args, **kwargs):
        return []

    async def capture_set(key, value, ttl=None, params=None):
        writes.append((key, value))
        return True

    monkeypatch.setattr(CacheService, "get", staticmethod(poisoned_get))
    monkeypatch.setattr(CacheService, "set", staticmethod(capture_set))

    result = asyncio.run(get_all_posts_for_type("cafe"))
    assert result and result[0]["slug"] == "sample-place"
    assert writes and len(writes[0][1]) == 1
