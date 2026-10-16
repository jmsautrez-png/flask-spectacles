"""Une demande = un secteur : cartes de choix, refus d'un mélange, raccourci « faire aussi l'autre demande »."""

import re
from html import unescape
from html.parser import HTMLParser
from types import SimpleNamespace

import pytest

from constants import ANIMATIONS, SPECIALITES
from utils.animations import MSG_DEMANDE_MIXTE, autre_secteur, reprise_depuis, sector_of

SPECTACLE = "Cirque"
ANIMATION = "Manège"
BUDGET_SPECTACLE = "730 à 930 € — Artiste / spectacle local (région / dpt)"


class SecteurPage(HTMLParser):
    """Cartes de choix (radios « secteur ») et blocs d'accordéon d'un secteur."""

    def __init__(self, html):
        super().__init__()
        self.radios, self.blocs = [], {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "input" and a.get("type") == "radio" and a.get("name") == "secteur":
            self.radios.append(a)
        elif tag == "div" and "data-secteur-bloc" in a:
            self.blocs[a["data-secteur-bloc"]] = a

    def checked(self):
        return [r["value"] for r in self.radios if "checked" in r]

    def hidden(self, secteur):
        return "hidden" in self.blocs[secteur]


def field_value(html, field_id):
    match = re.search(r'id="%s"[^>]*?value="([^"]*)"' % field_id, html)
    return unescape(match.group(1)) if match else None


def textarea_value(html, field_id):
    match = re.search(r'id="%s"[^>]*>(.*?)</textarea>' % field_id, html, re.S)
    return unescape(match.group(1)).strip() if match else None


def form_action(html):
    return re.search(r'<form action="([^"]*)" method="POST" class="form demande-form"', html).group(1)


def valid_form(labels, budget=BUDGET_SPECTACLE, **overrides):
    data = {
        "structure": "Mairie de Test", "civilite": "Mme", "nom": "Dupont",
        "contact_email": "mairie@example.test", "telephone": "0102030405",
        "intitule": "Une fête pour les enfants", "lieu_ville": "Rennes", "code_postal": "35000",
        "region": "Bretagne", "departement": "Ille-et-Vilaine (35)",
        "date_debut": "2027-12-15", "dates_horaires": "15/12/2027",
        "age_range": "jp_des_3", "jauge": "50 à 100", "budget": budget,
        "public_categories": ["famille"], "public_sous_options": ["fam_10"],
        "lieux_souhaites": ["Salle des fêtes non équipée"],
        "specialites_recherchees": labels,
    }
    data.update(overrides)
    return data


@pytest.fixture
def fake_mail(app, monkeypatch):
    from tests.test_offre_delivery import FakeMail

    mail = FakeMail()
    monkeypatch.setattr(app, "mail", mail)
    return mail


@pytest.fixture
def switch_off(app, monkeypatch):
    monkeypatch.setitem(app.config, "ANIMATIONS_OUVERT_DEMANDEURS", False)


def make_demande(user=None, **overrides):
    from models import db
    from models.models import DemandeAnimation

    fields = dict(
        structure="Ecole test", telephone="0600000000", lieu_ville="Brest", nom="Martin",
        dates_horaires="10/06/2027", type_espace="Salle", genre_recherche=SPECTACLE,
        age_range="jp_des_3", jauge="50 à 100", budget=BUDGET_SPECTACLE,
        contact_email="ecole@example.test", specialites_recherchees=SPECTACLE,
        user_id=user.id if user else None,
    )
    fields.update(overrides)
    demande = DemandeAnimation(**fields)
    db.session.add(demande)
    db.session.commit()
    return demande


def count_demandes():
    from models.models import DemandeAnimation

    return DemandeAnimation.query.count()


# ── Secteur d'une demande ────────────────────────────────────────────────

@pytest.mark.parametrize("labels,expected", [
    ([], ""),
    ([""], ""),
    ([SPECTACLE], "spectacle"),
    ([ANIMATION], "animation"),
    ([SPECTACLE, "Humoriste et Imitateur"], "spectacle"),
    ([ANIMATION, " Speaker "], "animation"),
    ([SPECTACLE, ANIMATION], "mixte"),
    (["Magie et Magicien"], "spectacle"),
    (["Magie et Magicien", ANIMATION], "mixte"),
    (None, ""),
])
def test_sector_of(labels, expected):
    assert sector_of(labels) == expected


def test_every_catalogue_name_has_exactly_one_sector():
    assert {sector_of([n]) for items in SPECIALITES.values() for n in items} == {"spectacle"}
    assert {sector_of([n]) for items in ANIMATIONS.values() for n in items} == {"animation"}


@pytest.mark.parametrize("labels,visible,expected", [
    ([SPECTACLE], True, "animation"),
    ([SPECTACLE], False, ""),
    ([ANIMATION], True, "spectacle"),
    ([ANIMATION], False, "spectacle"),
    ([SPECTACLE, ANIMATION], True, ""),
    ([], True, ""),
])
def test_other_sector_to_offer(labels, visible, expected):
    assert autre_secteur(labels, visible) == expected


def test_reprise_keeps_contact_and_event_but_not_sector_fields(db):
    demande = make_demande(
        civilite="Mme", code_postal="29200", date_debut="2027-06-10", intitule="Fête de l'école",
        contraintes="Noir total", accessibilite="PMR", public_categories="enfants",
        public_sous_options="mat", lieux_souhaites="Extérieur", portee_nationale=False,
    )

    copie = reprise_depuis(demande)

    assert (copie.structure, copie.nom, copie.civilite, copie.contact_email) == (
        "Ecole test", "Martin", "Mme", "ecole@example.test")
    assert (copie.lieu_ville, copie.code_postal, copie.date_debut, copie.jauge) == (
        "Brest", "29200", "2027-06-10", "50 à 100")
    assert (copie.public_categories, copie.public_sous_options, copie.lieux_souhaites) == (
        "enfants", "mat", "Extérieur")
    assert copie.accessibilite == "PMR" and copie.portee_nationale is False
    assert copie.id is None
    assert (copie.intitule, copie.specialites_recherchees, copie.budget, copie.contraintes) == ("", "", "", "")


def test_reprise_turns_missing_values_into_empty_strings(db):
    copie = reprise_depuis(make_demande(portee_nationale=None))
    assert copie.date_fin == "" and copie.region == "" and copie.civilite == ""
    assert copie.portee_nationale is True


# ── Cartes de choix sur le formulaire ───────────────────────────────────

def test_form_offers_two_cards_with_no_sector_chosen_and_both_accordions_hidden(client):
    html = client.get("/demande_animation").get_data(as_text=True)
    page = SecteurPage(html)
    assert [r["value"] for r in page.radios] == ["spectacle", "animation"]
    assert page.checked() == []
    assert page.hidden("spectacle") and page.hidden("animation")
    assert "Que recherchez-vous ?" in html
    assert "(cliquer sur l'un ou l'autre suivant votre choix)" in html
    assert re.findall(r'<span class="secteur-titre">(.*?)</span>', html) == ["Un spectacle", "Une animation"]
    assert "À partir de 730 € · artistes professionnels" in html and "Petit budget · moins de 730 € possible" in html
    assert html.count('<span class="secteur-cta" aria-hidden="true">Cliquez pour choisir</span>') == 2
    assert "2) Public concerné" in html
    assert 'id="secteur-error"' in html


@pytest.mark.parametrize("secteur,other", [("animation", "spectacle"), ("spectacle", "animation")])
def test_query_parameter_preselects_a_sector(client, secteur, other):
    page = SecteurPage(client.get("/demande_animation", query_string={"secteur": secteur}).get_data(as_text=True))
    assert page.checked() == [secteur]
    assert not page.hidden(secteur) and page.hidden(other)


def test_unknown_sector_in_query_parameter_is_ignored(client):
    page = SecteurPage(client.get("/demande_animation?secteur=autre").get_data(as_text=True))
    assert page.checked() == [] and page.hidden("spectacle") and page.hidden("animation")


def test_no_cards_and_no_animation_block_when_emergency_switch_is_closed(client, switch_off):
    html = client.get("/demande_animation?secteur=animation").get_data(as_text=True)
    page = SecteurPage(html)
    assert page.radios == [] and page.blocs == {}
    assert "Que recherchez-vous ?" not in html
    assert ANIMATION not in re.findall(r'name="specialites_recherchees" value="([^"]*)"', html)


def test_failed_post_keeps_the_sector_that_was_chosen(client):
    response = client.post("/demande_animation", data={"secteur": "animation"})
    assert response.status_code == 400
    page = SecteurPage(response.get_data(as_text=True))
    assert page.checked() == ["animation"] and not page.hidden("animation")


@pytest.mark.parametrize("labels,expected", [(ANIMATION, "animation"), (SPECTACLE, "spectacle")])
def test_editing_a_pure_request_preselects_its_sector(admin_client, labels, expected):
    demande = make_demande(specialites_recherchees=labels, genre_recherche=labels)
    page = SecteurPage(admin_client.get(f"/demandes-animation/edit/{demande.id}").get_data(as_text=True))
    assert page.checked() == [expected]


def test_editing_an_old_mixed_request_falls_back_to_the_free_form(admin_client):
    demande = make_demande(specialites_recherchees=f"{SPECTACLE},{ANIMATION}")
    html = admin_client.get(f"/demandes-animation/edit/{demande.id}").get_data(as_text=True)
    page = SecteurPage(html)
    assert page.radios == [] and page.blocs == {}
    assert {SPECTACLE, ANIMATION} <= {
        v for v, attrs in re.findall(r'name="specialites_recherchees" value="([^"]*)"([^>]*)>', html)
        if "checked" in attrs}


# ── Refus d'un mélange (serveur) ────────────────────────────────────────

def test_mixed_public_request_is_refused_and_not_saved(client, fake_mail):
    response = client.post("/demande_animation", data=valid_form([SPECTACLE, ANIMATION]))
    assert response.status_code == 400
    assert unescape(MSG_DEMANDE_MIXTE) in unescape(response.get_data(as_text=True))
    assert count_demandes() == 0
    with client.session_transaction() as session:
        assert "derniere_demande_id" not in session


@pytest.mark.parametrize("labels", [[SPECTACLE], [ANIMATION], *([name] for name in ANIMATIONS["Spectacles d'animation"])])
def test_pure_public_request_is_saved_and_remembered(client, fake_mail, labels):
    response = client.post("/demande_animation", data=valid_form(
        labels, budget=BUDGET_SPECTACLE if labels == [SPECTACLE] else "300 à 500 €"))
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/demande/proposition-compte")
    assert count_demandes() == 1
    from models.models import DemandeAnimation

    saved = DemandeAnimation.query.one()
    assert saved.specialites_recherchees == labels[0]
    with client.session_transaction() as session:
        assert session["derniere_demande_id"] == saved.id


def test_owner_editing_a_request_cannot_mix_sectors(logged_in_client, normal_user):
    demande = make_demande(normal_user)
    response = logged_in_client.post(f"/mes-demandes/edit/{demande.id}", data={
        "specialites_recherchees": [SPECTACLE, ANIMATION], "lieu_ville": "Nantes"})
    assert response.status_code == 400
    assert unescape(MSG_DEMANDE_MIXTE) in unescape(response.get_data(as_text=True))
    from models import db
    from models.models import DemandeAnimation

    db.session.expire_all()
    saved = DemandeAnimation.query.get(demande.id)
    assert saved.lieu_ville == "Brest" and saved.specialites_recherchees == SPECTACLE


def test_owner_editing_a_request_still_saves_every_field(logged_in_client, normal_user):
    demande = make_demande(normal_user)
    response = logged_in_client.post(f"/mes-demandes/edit/{demande.id}", data={
        "structure": "Ecole modifiee", "telephone": "0700000000", "lieu_ville": "Nantes",
        "nom": "Durand", "specialites_recherchees": [ANIMATION]})
    assert response.status_code == 302
    from models import db
    from models.models import DemandeAnimation

    db.session.expire_all()
    saved = DemandeAnimation.query.get(demande.id)
    assert (saved.structure, saved.telephone, saved.lieu_ville, saved.nom) == (
        "Ecole modifiee", "0700000000", "Nantes", "Durand")
    assert saved.specialites_recherchees == ANIMATION


def test_admin_editing_stays_free_and_can_keep_both_sectors(admin_client):
    demande = make_demande()
    response = admin_client.post(f"/demandes-animation/edit/{demande.id}", data={
        "specialites_recherchees": [SPECTACLE, ANIMATION]})
    assert response.status_code == 302
    from models import db
    from models.models import DemandeAnimation

    db.session.expire_all()
    assert set(DemandeAnimation.query.get(demande.id).specialites_recherchees.split(",")) == {SPECTACLE, ANIMATION}


# ── « Faire aussi l'autre demande » ─────────────────────────────────────

def test_anonymous_confirmation_page_offers_the_other_sector(client, fake_mail):
    client.post("/demande_animation", data=valid_form([SPECTACLE]))
    html = client.get("/demande/proposition-compte").get_data(as_text=True)
    assert "Besoin aussi d'une animation ?" in unescape(html)
    assert "/demande_animation?secteur=animation&amp;reprise=1" in html


def test_connected_user_lands_on_a_confirmation_page_with_the_shortcut(logged_in_client, fake_mail):
    response = logged_in_client.post("/demande_animation", data=valid_form(
        [ANIMATION], budget="300 à 500 €"))
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/demande/envoyee")
    html = logged_in_client.get("/demande/envoyee").get_data(as_text=True)
    assert "Votre demande a été envoyée" in html
    assert "Besoin aussi d'un spectacle ?" in unescape(html)
    assert "/demande_animation?secteur=spectacle&amp;reprise=1" in html


def test_connected_user_goes_home_when_there_is_no_other_sector_to_offer(
    logged_in_client, fake_mail, switch_off,
):
    response = logged_in_client.post("/demande_animation", data=valid_form([SPECTACLE]))
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert "/demande/envoyee" not in response.headers["Location"]


def test_confirmation_page_needs_a_request_sent_in_this_session(client):
    response = client.get("/demande/envoyee")
    assert response.status_code == 302 and response.headers["Location"].endswith("/")


def test_second_request_form_reuses_contact_and_event_but_not_the_rest(client, fake_mail):
    client.post("/demande_animation", data=valid_form([SPECTACLE]))
    before = count_demandes()

    html = client.get("/demande_animation?secteur=animation&reprise=1").get_data(as_text=True)

    assert SecteurPage(html).checked() == ["animation"]
    assert "Seconde demande" in html
    assert form_action(html) == "/demande_animation"
    assert field_value(html, "structure") == "Mairie de Test"
    assert field_value(html, "nom") == "Dupont"
    assert field_value(html, "contact_email") == "mairie@example.test"
    assert field_value(html, "lieu_ville") == "Rennes"
    assert field_value(html, "code_postal") == "35000"
    assert field_value(html, "date_debut") == "2027-12-15"
    assert field_value(html, "date_fin") == ""
    assert field_value(html, "region") == "Bretagne"
    assert textarea_value(html, "intitule") == ""
    assert textarea_value(html, "contraintes") == ""
    assert "None" not in re.findall(r'value="([^"]*)"', html)
    assert "Envoyer la demande" in html and "Sauvegarder les modifications" not in html
    assert count_demandes() == before


def test_second_request_can_be_sent_and_creates_a_new_request(client, fake_mail):
    client.post("/demande_animation", data=valid_form([SPECTACLE]))
    response = client.post("/demande_animation", data=valid_form([ANIMATION], budget="300 à 500 €"))
    assert response.status_code == 302
    assert count_demandes() == 2


def test_reprise_never_exposes_another_visitors_request(app, client, fake_mail):
    client.post("/demande_animation", data=valid_form([SPECTACLE]))
    other = app.test_client()
    html = other.get("/demande_animation?secteur=animation&reprise=1").get_data(as_text=True)
    assert "Seconde demande" not in html
    assert field_value(html, "structure") == ""
    assert field_value(html, "contact_email") == ""


def test_reprise_without_a_sent_request_shows_a_blank_form(client):
    html = client.get("/demande_animation?reprise=1").get_data(as_text=True)
    assert "Seconde demande" not in html and field_value(html, "structure") == ""


# ── Arrivée depuis les pages d'animations ───────────────────────────────

@pytest.mark.parametrize("path", ["/animations-anniversaire", "/pere-noel-a-domicile"])
def test_small_budget_animation_pages_open_the_form_on_the_animation_sector(client, path):
    html = client.get(path).get_data(as_text=True)
    assert "/demande_animation?secteur=animation" in html


@pytest.mark.parametrize("path", ["/animations-entreprises", "/animations-enfants"])
def test_other_pages_leave_the_choice_to_the_visitor(client, path):
    html = client.get(path).get_data(as_text=True)
    assert 'href="/demande_animation"' in html
    assert "secteur=animation" not in html
