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


def test_search_page_returns_listing_for_greek_title_el(client, fake_wp):
    fake_wp.posts[0]["title"] = {"rendered": "Church of Christ"}
    fake_wp.posts[0]["meta"] = {
        "title_el": "Εκκλησία του Χριστού",
        "content_el": "<p>Ο ναός είναι αφιερωμένος στον Χριστό.</p>",
    }

    greek = client.get("/search", params={"q": "Εκκλησία του Χριστού"})
    assert greek.status_code == 200
    assert "Church of Christ" in greek.text
    assert "No Results Found" not in greek.text

    english = client.get("/search", params={"q": "Church of Christ"})
    assert english.status_code == 200
    assert "Church of Christ" in english.text


def test_category_list_search_uses_title_el(client, fake_wp):
    fake_wp.posts[0]["title"] = {"rendered": "Church of Christ"}
    fake_wp.posts[0]["meta"] = {"title_el": "Εκκλησία του Χριστού"}

    response = client.get("/religious-sites", params={"search": "Εκκλησία του Χριστού"})
    assert response.status_code == 200
    assert "Church of Christ" in response.text
