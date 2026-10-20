"""Page profil d'une compagnie : l'épingle est le seul émoji conservé."""

import re

import pytest

from utils.seo import company_slug

PIN = "\U0001F4CD"
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")


@pytest.fixture
def page_content(client, normal_user, monkeypatch):
    """Contenu propre à la page, sans l'en-tête, le menu ni le pied de page communs à tout le site."""
    import app as app_module
    from models import db
    from models.models import Show

    # Le bloc de coordonnées directes est masqué par défaut : on l'affiche pour le contrôler aussi
    monkeypatch.setattr(app_module, "MASQUER_COORDONNEES_DIRECTES", False)
    normal_user.raison_sociale = "Cie Test"
    normal_user.region = "Bretagne"
    normal_user.site_internet = "https://cie.example.test"
    normal_user.telephone = "0102030405"
    db.session.add(Show(title="Mon spectacle", user_id=normal_user.id, approved=True,
                        category="Cirque", age_range="enfant", region="Bretagne"))
    db.session.commit()

    response = client.get("/compagnie/" + company_slug(normal_user))
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    return html[html.index('aria-label="fil d\'ariane"'):html.index("Retour au catalogue complet")]


def test_emoji_detection_covers_every_icon_that_was_removed():
    assert set(EMOJI.findall("\U0001F3AD\U0001F3AA\U0001F310\u2709\ufe0f\U0001F4DE\U0001F476" + PIN)) >= {
        "\U0001F3AD", "\U0001F3AA", "\U0001F310", "\u2709", "\U0001F4DE", "\U0001F476", PIN,
    }


def test_only_the_pin_emoji_is_kept(page_content):
    assert set(EMOJI.findall(page_content)) == {PIN}
    # une épingle devant la région de la compagnie, une devant celle du spectacle
    assert page_content.count(PIN) == 2


def test_removing_the_icons_keeps_the_texts(page_content):
    for text in ("Cie Test", "1 spectacle au catalogue", "Spectacles de Cie Test", "Site officiel",
                 "user@test.com", "0102030405", "Mon spectacle", "enfant", "Bretagne"):
        assert text in page_content
