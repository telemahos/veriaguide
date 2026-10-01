from app.utils.church_slugs import public_church_slug


def test_public_church_slug_strips_seo_tails():
    assert public_church_slug(
        "agios-antonios-a-14th-century-byzantine-church-in-veria"
    ) == "agios-antonios"
    assert public_church_slug("exploring-the-panagia-in-veria-greece") == "panagia"
    assert public_church_slug("short-name") == "short-name"
    assert public_church_slug("") == ""
