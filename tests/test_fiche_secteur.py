"""Une fiche = un secteur : cartes de choix, refus d'un mélange, raccourci « créer aussi l'autre fiche »."""

import io
import re
from html import unescape
from html.parser import HTMLParser

import pytest

from tests.test_secteur_demande import SecteurPage
from utils.animations import MSG_FICHE_MIXTE, fiche_reprise_depuis

SPECTACLE = "Cirque"
ANIMATION = "Manège"


class Cases(HTMLParser):
    """Cases à cocher (nom, valeur, cochée) d'une page."""

    def __init__(self, html):
        super().__init__()
        self.cases = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "input" and a.get("type") == "checkbox":
            self.cases.append((a.get("name"), a.get("value"), "checked" in a))

    def checked(self, name):
        return [v for n, v, on in self.cases if n == name and on]


def value_of(html, name):
    match = re.search(r'name="%s"[^>]*?value="([^"]*)"' % name, html)
    return unescape(match.group(1)) if match else None


def make_show(user, specialites=SPECTACLE, **overrides):
    from models import db
    from models.models import Show

    fields = dict(
        title="Fiche test", user_id=user.id, approved=True, specialites=specialites,
        raison_sociale="Cie Test", contact_email="cie@example.test", contact_phone="0600000000",
        location="Brest", code_postal="29200", region="Bretagne", departement="Finistère (29)",
        regions_intervention="Bretagne,Normandie", lieux_intervention="Extérieur,Salle équipée",
        public_categories="famille", public_sous_options="fam_10", nb_comediens=2,
    )
    fields.update(overrides)
    show = Show(**fields)
    db.session.add(show)
    db.session.commit()
    return show


def shows_count():
    from models.models import Show

    return Show.query.count()


def saved_specialites(show_id):
    from models import db
    from models.models import Show

    db.session.rollback()
    db.session.expire_all()
    return Show.query.get(show_id).specialites


def publish(client, specialites, **extra):
    data = {
        "raison_sociale": "Cie Test", "title": "Ma fiche", "description": "<p>Une description</p>",
        "contact_email": "cie@example.test", "contact_phone": "0600000000",
        "code_postal": "35000", "location": "Rennes", "region": "Bretagne",
        "specialites": specialites, "regions_intervention": ["Bretagne"],
        "lieux_intervention": ["Extérieur"], "public_categories": ["famille"],
        "public_sous_options": ["fam_10"], "nb_comediens": "2", "prix_min": "250",
        "file": (io.BytesIO(b"fake"), "a.jpg"), "file2": (io.BytesIO(b"fake"), "b.jpg"),
    }
    data.update(extra)
    return client.post("/submit", data=data, content_type="multipart/form-data", follow_redirects=True)


@pytest.fixture
def no_upload(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "upload_file_local", lambda f: "fake-photo.jpg")
    monkeypatch.setattr(app_module, "validate_file_size", lambda f: (True, None))


def page_text(response):
    return unescape(response.get_data(as_text=True))


# ── Cartes sur le formulaire de publication ─────────────────────────────

def test_publish_form_offers_two_cards_with_both_accordions_hidden(logged_in_client):
    html = logged_in_client.get("/submit").get_data(as_text=True)
    page = SecteurPage(html)
    assert [r["value"] for r in page.radios] == ["spectacle", "animation"]
    assert page.checked() == []
    assert page.hidden("spectacle") and page.hidden("animation")
    assert "Que présente votre fiche ?" in html
    assert "(cliquer sur l'un ou l'autre suivant votre choix)" in html
    assert re.findall(r'<span class="secteur-titre">(.*?)</span>', html) == ["Un spectacle", "Une animation"]
    cartes = re.search(r'<fieldset[^>]*id="secteur-choix".*?</fieldset>', html, re.S).group(0)
    assert "730" not in cartes and "Tarifs habituels" not in cartes and "Petit budget" not in cartes
    assert cartes.count('<span class="secteur-cta" aria-hidden="true">Cliquez pour choisir</span>') == 2
    assert 'id="secteur-error"' in html and 'id="prix-aide"' in html


def assert_cards_sit_right_before_the_specialty_accordions(html):
    cards = html.index('id="secteur-choix"')
    first_bloc = html.index("data-secteur-bloc=")
    assert (
        html.index('<input type="text" name="title"') < html.index('<textarea id="description"')
        < html.index('<input type="file" name="file" ') < cards < first_bloc
    )
    assert "matching-accordion-section" not in html[cards:first_bloc]


def test_publish_form_puts_the_cards_right_before_the_specialty_accordions(logged_in_client):
    assert_cards_sit_right_before_the_specialty_accordions(logged_in_client.get("/submit").get_data(as_text=True))


def test_edit_form_puts_the_cards_right_before_the_specialty_accordions(logged_in_client, normal_user):
    show = make_show(normal_user, SPECTACLE)
    assert_cards_sit_right_before_the_specialty_accordions(
        logged_in_client.get(f"/my/shows/{show.id}/edit").get_data(as_text=True))


def test_publish_form_keeps_title_and_description_together_and_asks_the_price_after_the_specialties(logged_in_client):
    html = logged_in_client.get("/submit").get_data(as_text=True)
    after_title = html.index("</label>", html.index('<input type="text" name="title"'))
    between = re.sub(r"\s+", "", html[after_title:html.index('<span class="label-text">Description')])
    assert re.sub(r"<div[^>]*>", "<div>", between) == "</label></div><div><label>"
    assert html.count('<input type="number" name="prix_min"') == 1
    assert html.index('data-secteur-bloc="animation"') < html.index('<input type="number" name="prix_min"') < html.index('id="lieux-warning"')


@pytest.mark.parametrize("secteur,other", [("animation", "spectacle"), ("spectacle", "animation")])
def test_publish_form_preselects_the_sector_from_the_link(logged_in_client, secteur, other):
    page = SecteurPage(logged_in_client.get("/submit", query_string={"secteur": secteur}).get_data(as_text=True))
    assert page.checked() == [secteur]
    assert not page.hidden(secteur) and page.hidden(other)


def test_publish_form_ignores_an_unknown_sector(logged_in_client):
    page = SecteurPage(logged_in_client.get("/submit?secteur=autre").get_data(as_text=True))
    assert page.checked() == [] and page.hidden("spectacle") and page.hidden("animation")


# ── Refus d'un mélange (serveur) ────────────────────────────────────────

def test_mixed_publication_is_refused_and_not_saved(logged_in_client, no_upload):
    response = publish(logged_in_client, [SPECTACLE, ANIMATION])
    assert unescape(MSG_FICHE_MIXTE) in page_text(response)
    assert shows_count() == 0


def test_pure_sector_passes_the_check_and_reaches_the_next_validation(logged_in_client):
    response = publish(logged_in_client, [ANIMATION], file=(io.BytesIO(b""), ""), file2=(io.BytesIO(b""), ""))
    text = page_text(response)
    assert "minimum 2 photos" in text
    assert unescape(MSG_FICHE_MIXTE) not in text


def test_admin_publication_stays_free(admin_client, no_upload):
    response = publish(admin_client, [SPECTACLE, ANIMATION])
    assert unescape(MSG_FICHE_MIXTE) not in page_text(response)
    assert shows_count() == 1


def test_owner_cannot_turn_a_fiche_into_a_mixed_one(logged_in_client, normal_user):
    show = make_show(normal_user)
    response = logged_in_client.post(f"/my/shows/{show.id}/edit", data={
        "title": "Autre titre", "specialites": [SPECTACLE, ANIMATION], "regions_intervention": ["Bretagne"],
        "nb_comediens": "2"}, follow_redirects=True)
    assert unescape(MSG_FICHE_MIXTE) in page_text(response)
    assert saved_specialites(show.id) == SPECTACLE


def test_owner_can_still_save_a_pure_fiche(logged_in_client, normal_user):
    show = make_show(normal_user)
    response = logged_in_client.post(f"/my/shows/{show.id}/edit", data={
        "title": "Titre modifié", "specialites": [ANIMATION], "regions_intervention": ["Bretagne"],
        "nb_comediens": "2"})
    assert response.status_code == 200
    assert "Spectacle mis à jour" in page_text(response)
    assert saved_specialites(show.id) == ANIMATION


def test_admin_editing_stays_free_and_keeps_a_mixed_fiche(admin_client, normal_user):
    show = make_show(normal_user)
    response = admin_client.post(f"/my/shows/{show.id}/edit", data={
        "title": "Titre", "specialites": [SPECTACLE, ANIMATION], "regions_intervention": ["Bretagne"],
        "nb_comediens": "2"})
    assert response.status_code == 200
    assert set(saved_specialites(show.id).split(",")) == {SPECTACLE, ANIMATION}


# ── Cartes sur le formulaire de modification ────────────────────────────

@pytest.mark.parametrize("specialites,expected", [(ANIMATION, "animation"), (SPECTACLE, "spectacle")])
def test_edit_form_preselects_the_sector_of_a_pure_fiche(logged_in_client, normal_user, specialites, expected):
    show = make_show(normal_user, specialites)
    html = logged_in_client.get(f"/my/shows/{show.id}/edit").get_data(as_text=True)
    page = SecteurPage(html)
    assert page.checked() == [expected]
    assert not page.hidden(expected) and page.hidden("animation" if expected == "spectacle" else "spectacle")
    assert 'id="prix-aide"' in html


def test_edit_form_of_a_fiche_without_specialties_offers_the_choice(logged_in_client, normal_user):
    show = make_show(normal_user, specialites=None)
    page = SecteurPage(logged_in_client.get(f"/my/shows/{show.id}/edit").get_data(as_text=True))
    assert page.checked() == [] and page.hidden("spectacle") and page.hidden("animation")


def test_edit_form_of_an_old_mixed_fiche_falls_back_to_the_free_form(logged_in_client, normal_user):
    show = make_show(normal_user, f"{SPECTACLE},{ANIMATION}")
    html = logged_in_client.get(f"/my/shows/{show.id}/edit").get_data(as_text=True)
    page = SecteurPage(html)
    assert page.radios == [] and page.blocs == {}
    assert set(Cases(html).checked("specialites")) == {SPECTACLE, ANIMATION}


# ── « Créer aussi l'autre fiche » ───────────────────────────────────────

def test_publication_page_offers_the_other_sector(logged_in_client, no_upload):
    response = publish(logged_in_client, [ANIMATION])
    from models.models import Show

    show = Show.query.one()
    html = response.get_data(as_text=True)
    assert "Annonce envoyée" in unescape(html)
    assert "Créer aussi une fiche de spectacle" in unescape(html)
    assert f"/submit?secteur=spectacle&amp;reprise={show.id}" in html


def test_publication_page_of_a_spectacle_offers_an_animation(logged_in_client, no_upload):
    response = publish(logged_in_client, [SPECTACLE])
    assert "Créer aussi une fiche d'animation" in page_text(response)


def test_dashboard_offers_the_shortcut_on_pure_fiches_only(logged_in_client, normal_user):
    spectacle = make_show(normal_user, SPECTACLE, title="Fiche spectacle")
    animation = make_show(normal_user, ANIMATION, title="Fiche animation")
    make_show(normal_user, f"{SPECTACLE},{ANIMATION}", title="Fiche mixte")
    make_show(normal_user, None, title="Fiche vide")

    html = logged_in_client.get("/dashboard").get_data(as_text=True)

    assert html.count("Créer aussi une fiche") == 2
    assert f"/submit?secteur=animation&amp;reprise={spectacle.id}" in html
    assert f"/submit?secteur=spectacle&amp;reprise={animation.id}" in html


def test_second_fiche_form_reuses_the_company_information(logged_in_client, normal_user):
    source = make_show(normal_user, SPECTACLE)

    html = logged_in_client.get("/submit", query_string={"secteur": "animation", "reprise": source.id}).get_data(as_text=True)

    assert "Nouvelle fiche" in html and "Fiche test" in unescape(html)
    assert SecteurPage(html).checked() == ["animation"]
    assert value_of(html, "raison_sociale") == "Cie Test"
    assert value_of(html, "contact_email") == "cie@example.test"
    assert value_of(html, "contact_phone") == "0600000000"
    assert value_of(html, "code_postal") == "29200"
    assert value_of(html, "location") == "Brest"
    assert value_of(html, "region") == "Bretagne"
    assert value_of(html, "departement") == "Finistère (29)"
    cases = Cases(html)
    assert set(cases.checked("regions_intervention")) == {"Bretagne", "Normandie"}
    assert set(cases.checked("lieux_intervention")) == {"Extérieur", "Salle équipée"}
    assert cases.checked("public_categories") == ["famille"]
    assert cases.checked("specialites") == []
    assert value_of(html, "title") is None and value_of(html, "prix_min") == ""


def test_second_fiche_form_ignores_someone_elses_fiche(logged_in_client, normal_user):
    from models import db
    from models.models import User

    other = User(username="autre", email="autre@example.test")
    other.set_password("autrepass123")
    db.session.add(other)
    db.session.commit()
    foreign = make_show(other, raison_sociale="Cie Autre", contact_email="autre@example.test")

    html = logged_in_client.get("/submit", query_string={"reprise": foreign.id}).get_data(as_text=True)

    assert "Nouvelle fiche" not in html
    assert value_of(html, "raison_sociale") != "Cie Autre"
    assert "autre@example.test" not in html


def test_admin_can_reuse_any_fiche_and_unknown_ids_are_ignored(admin_client, normal_user):
    source = make_show(normal_user)
    assert "Nouvelle fiche" in admin_client.get("/submit", query_string={"reprise": source.id}).get_data(as_text=True)
    assert "Nouvelle fiche" not in admin_client.get("/submit?reprise=99999").get_data(as_text=True)
    assert "Nouvelle fiche" not in admin_client.get("/submit?reprise=abc").get_data(as_text=True)


def test_fiche_reprise_keeps_company_information_but_not_the_showcase(normal_user, db):
    show = make_show(
        normal_user, lieux_intervention="Cour d'école", regions_intervention=" Bretagne , Normandie ",
        raison_sociale=None, location=None, departement=None, public_sous_options=None,
    )
    copie = fiche_reprise_depuis(show)

    assert copie.titre_source == "Fiche test"
    assert copie.regions == ["Bretagne", "Normandie"]
    assert copie.lieux == ["Extérieur"]
    assert (copie.raison_sociale, copie.location, copie.departement) == ("", "", "")
    assert copie.public_sous_options == [] and copie.public_categories == ["famille"]
    assert not hasattr(copie, "title") and not hasattr(copie, "prix_min")
