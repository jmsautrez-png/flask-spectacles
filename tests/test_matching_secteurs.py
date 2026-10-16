"""Matching Spectacles / Animations : un seul moteur, deux listes de cases, budgets bas."""

import re
from types import SimpleNamespace

import pytest

from constants import ANIMATIONS
from tests.test_fiche_secteur import no_upload, publish
from tests.test_secteur_demande import fake_mail, valid_form
from utils.matching import compute_score, find_matching_shows

SPECTACLE = "Prestidigitateur"
ANIMATION = "Atelier maquillage"
NOEL = "Passage du Père Noël"
DOMICILE_ENFANT, DOMICILE_ADULTE = ANIMATIONS["Spectacles d'animation"]
BUDGET_SPECTACLE = "730 à 930 € — Artiste / spectacle local (région / dpt)"
BUDGET_BAS = "Moins de 300 €"
BUDGET_MOYEN = "300 à 500 €"


@pytest.fixture(autouse=True)
def no_geo_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("le matching ne doit appeler aucun service de géolocalisation")

    for name in ("_fetch_coords", "_fetch_dept_coords", "_fetch_city_coords"):
        monkeypatch.setattr(f"utils.geo.{name}", refuse)


def make_show(user, title, specialites, prix_min=None):
    from models import db
    from models.models import Show

    show = Show(
        title=title, user=user, approved=True, specialites=specialites,
        category=specialites.split(",")[0], region="Bretagne", contact_email=user.email, prix_min=prix_min,
    )
    db.session.add(show)
    db.session.commit()
    return show


def make_demande(specialites, budget, **overrides):
    from models import db
    from models.models import DemandeAnimation

    fields = dict(
        structure="Mairie test", telephone="0102030405", lieu_ville="Rennes", nom="Dupont",
        dates_horaires="15/06/2027", type_espace="Salle des fêtes", genre_recherche=specialites.split(",")[0],
        age_range="jp_des_3", jauge="50 à 100", budget=budget, contact_email="mairie@example.test",
        specialites_recherchees=specialites, region="Bretagne", approved=True,
    )
    fields.update(overrides)
    demande = DemandeAnimation(**fields)
    db.session.add(demande)
    db.session.commit()
    return demande


def matches(demande, min_score=10):
    from models.models import Show

    return find_matching_shows(demande, Show.query.filter(Show.approved.is_(True)).all(), min_score=min_score)


def titles(result):
    return [show.title for show, _ in result]


@pytest.fixture
def fiches(db, normal_user):
    return SimpleNamespace(
        animation=make_show(normal_user, "Atelier couleurs", ANIMATION, prix_min=250),
        spectacle=make_show(normal_user, "Grand magicien", SPECTACLE, prix_min=900),
        mixte=make_show(normal_user, "Fiche mixte", f"{ANIMATION},{SPECTACLE}", prix_min=250),
    )


# ── Moteur : chaque demande retrouve les fiches de son secteur ──────────

def test_animation_request_finds_animation_and_mixed_fiches_only(fiches):
    result = matches(make_demande(ANIMATION, BUDGET_BAS))
    assert set(titles(result)) == {"Atelier couleurs", "Fiche mixte"}
    assert all(score["budget"]["compatible"] is True for _, score in result)


def test_spectacle_request_finds_prestige_and_mixed_fiches_and_ranks_over_budget_last(db, normal_user, fiches):
    make_show(normal_user, "Spectacle tres cher", SPECTACLE, prix_min=1500)
    result = matches(make_demande(SPECTACLE, BUDGET_SPECTACLE))
    assert set(titles(result)) == {"Grand magicien", "Fiche mixte", "Spectacle tres cher"}
    assert titles(result)[-1] == "Spectacle tres cher"
    assert result[-1][1]["budget"]["compatible"] is False
    assert all(score["budget"]["compatible"] is True for _, score in result[:-1])


def test_prestige_priced_fiche_is_kept_but_ranked_last_for_a_low_budget_request(db, normal_user, fiches):
    make_show(normal_user, "Mixte cher", f"{ANIMATION},{SPECTACLE}", prix_min=900)
    result = matches(make_demande(ANIMATION, BUDGET_BAS))
    assert set(titles(result)) == {"Atelier couleurs", "Fiche mixte", "Mixte cher"}
    assert titles(result)[-1] == "Mixte cher"
    assert result[-1][1]["budget"]["compatible"] is False


def test_request_with_both_sectors_matches_both(fiches):
    result = matches(make_demande(f"{ANIMATION},{SPECTACLE}", BUDGET_SPECTACLE))
    assert set(titles(result)) == {"Atelier couleurs", "Grand magicien", "Fiche mixte"}


def test_fiche_without_any_shared_name_is_not_matched(db, normal_user):
    make_show(normal_user, "Sculpteur", "Sculpteur de ballons", prix_min=200)
    assert matches(make_demande(ANIMATION, BUDGET_BAS)) == []


def test_ticking_many_names_across_both_catalogues_dilutes_the_score(db, normal_user):
    autres = [name for items in ANIMATIONS.values() for name in items if name != ANIMATION][:9]
    ciblee = make_show(normal_user, "Ciblee", ANIMATION)
    dispersee = make_show(normal_user, "Dispersee", ",".join([ANIMATION, *autres]))
    demande = make_demande(ANIMATION, BUDGET_BAS)
    assert compute_score(ciblee, demande)["specialites"] > compute_score(dispersee, demande)["specialites"] > 0


# ── Règles par nom de case ───────────────────────────────────────────────

@pytest.mark.parametrize("date,expected", [("15/07/2027", []), ("15/12/2027", ["Pere Noel"]), ("", ["Pere Noel"])])
def test_pere_noel_fiches_only_match_november_and_december_requests(db, normal_user, date, expected):
    make_show(normal_user, "Pere Noel", NOEL, prix_min=250)
    assert titles(matches(make_demande(NOEL, BUDGET_BAS, dates_horaires=date))) == expected


def test_home_show_names_match_whatever_the_case_and_stay_separate(db, normal_user):
    make_show(normal_user, "Gouter maison", DOMICILE_ENFANT, prix_min=300)
    make_show(normal_user, "Adulte maison", DOMICILE_ADULTE, prix_min=300)
    assert titles(matches(make_demande(DOMICILE_ENFANT.upper(), BUDGET_MOYEN))) == ["Gouter maison"]
    assert titles(matches(make_demande(DOMICILE_ADULTE, BUDGET_MOYEN))) == ["Adulte maison"]
    both = matches(make_demande(f"{DOMICILE_ENFANT},{DOMICILE_ADULTE}", BUDGET_MOYEN))
    assert set(titles(both)) == {"Gouter maison", "Adulte maison"}


def test_name_missing_from_both_catalogues_still_matches_itself(db, normal_user):
    make_show(normal_user, "Ancienne fiche", "Magie et Magicien", prix_min=800)
    make_show(normal_user, "Autre fiche", SPECTACLE, prix_min=800)
    assert titles(matches(make_demande("Magie et Magicien", BUDGET_SPECTACLE))) == ["Ancienne fiche"]


# ── Écrans qui s'appuient sur le matching ────────────────────────────────

def test_admin_send_page_lists_the_matching_fiches_of_each_sector(admin_client, fiches):
    for specialites, budget, expected in [
        (ANIMATION, BUDGET_BAS, {fiches.animation, fiches.mixte}),
        (SPECTACLE, BUDGET_SPECTACLE, {fiches.spectacle, fiches.mixte}),
    ]:
        demande = make_demande(specialites, budget)
        response = admin_client.get(f"/admin/envoyer-demande/{demande.id}")
        assert response.status_code == 200
        ids = set(re.findall(r'name="matched_show_ids" value="(\d+)"', response.get_data(as_text=True)))
        assert ids == {str(show.id) for show in expected}


def test_admin_send_page_shows_the_parsed_low_budget(admin_client, fiches):
    html = admin_client.get(f"/admin/envoyer-demande/{make_demande(ANIMATION, BUDGET_BAS).id}").get_data(as_text=True)
    assert "Budget demande : 0–300 €" in html


def test_catalogue_filters_fiches_by_name_for_both_catalogues(client, db, normal_user, fiches):
    make_show(normal_user, "Gouter maison", DOMICILE_ENFANT, prix_min=300)
    tous = ("Atelier couleurs", "Grand magicien", "Fiche mixte", "Gouter maison")
    for name, expected in [
        (ANIMATION, {"Atelier couleurs", "Fiche mixte"}),
        (SPECTACLE, {"Grand magicien", "Fiche mixte"}),
        (DOMICILE_ENFANT, {"Gouter maison"}),
    ]:
        html = client.get("/catalogue", query_string={"specialite": name}).get_data(as_text=True)
        assert {title for title in tous if f">{title}</h3>" in html} == expected


# ── Pages thématiques (filtres sur la catégorie et les spécialités) ─────

@pytest.mark.parametrize("page", ["/animations-enfants", "/spectacles-enfants"])
def test_children_pages_list_the_children_home_show_fiches_wherever_the_name_is_ticked(client, db, normal_user, page):
    make_show(normal_user, "Gouter premier", DOMICILE_ENFANT)
    make_show(normal_user, "Gouter second", f"{SPECTACLE},{DOMICILE_ENFANT}")
    make_show(normal_user, "Soiree adulte", DOMICILE_ADULTE)
    make_show(normal_user, "Bal seniors", "Accordéoniste (seniors)")
    html = client.get(page).get_data(as_text=True)
    listed = {title for title in ("Gouter premier", "Gouter second", "Soiree adulte", "Bal seniors") if f"<h3>{title}</h3>" in html}
    assert listed == {"Gouter premier", "Gouter second"}


# ── Parcours complet : formulaires publics → page admin de matching ─────

@pytest.mark.parametrize("name,budget,expected", [
    (ANIMATION, BUDGET_BAS, "Atelier du formulaire"),
    (SPECTACLE, BUDGET_SPECTACLE, "Magie du formulaire"),
])
def test_fiches_and_requests_made_with_the_public_forms_find_each_other(
        logged_in_client, normal_user, admin_user, no_upload, fake_mail, name, budget, expected):
    from models import db
    from models.models import DemandeAnimation, Show

    normal_user.latitude, normal_user.longitude = 48.1173, -1.6778
    db.session.commit()
    for title, specialite, prix in (("Atelier du formulaire", ANIMATION, "250"), ("Magie du formulaire", SPECTACLE, "900")):
        publish(logged_in_client, [specialite], title=title, prix_min=prix)
    shows = {show.title: show for show in Show.query.all()}
    assert set(shows) == {"Atelier du formulaire", "Magie du formulaire"}
    for show in shows.values():
        show.approved = True
    db.session.commit()

    with logged_in_client.session_transaction() as session:
        session.pop("username")
    response = logged_in_client.post("/demande_animation", data=valid_form([name], budget=budget))
    assert response.status_code == 302
    demande = DemandeAnimation.query.one()

    with logged_in_client.session_transaction() as session:
        session["username"] = "testadmin"
    html = logged_in_client.get(f"/admin/envoyer-demande/{demande.id}").get_data(as_text=True)
    assert set(re.findall(r'name="matched_show_ids" value="(\d+)"', html)) == {str(shows[expected].id)}
    assert "✓ Compatible" in html
