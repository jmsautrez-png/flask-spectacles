"""Secteur Animations : taxonomie, accordéons, interrupteur d'ouverture, budgets et matching."""

import re
from collections import Counter
from html import unescape
from html.parser import HTMLParser
from types import SimpleNamespace

import pytest

from constants import (
    ANIMATIONS,
    ANIMATIONS_DOSSIERS_PETIT_BUDGET,
    ANIMATIONS_MENTIONS_PRIX,
    BUDGETS_ANIMATION,
    BUDGETS_SPECTACLE,
    SPECIALITES,
)
from utils import matching
from utils.animations import (
    ANIMATIONS_LABELS,
    animations_visibles_demandeurs,
    contains_animation,
)

LEGACY_BUDGET = "À partir de 300 € — Ateliers divers, maquillage, ballons, déambulation, Père Noël, etc."

DOMICILE_ENFANT = "Spectacle à domicile (goûter d'anniversaire)"
DOMICILE_ADULTE = "Spectacle à domicile pour adulte (anniversaire etc.)"

MOVED = [
    "Passage du Père Noël",
    "Atelier maquillage", "Atelier divers", "Sculpteur de ballons", "Caricaturistes et Silhouettiste",
    "Parade de rue / Déambulation", "Échassier", "Mascotte", "Cascadeur", "Clown suiveur",
    "Manège",
    "Speaker",
    DOMICILE_ENFANT, DOMICILE_ADULTE, "Spectacle d'animation EHPAD",
]
NEW_SENIORS = [
    "Accordéoniste (seniors)",
    "Chanteur / chanteuse (tour de chant)",
    "Musicien solo ou duo (seniors)",
    "Petit groupe musical ponctuel (2 à 4 musiciens)",
    "Imitateur / Humoriste (seniors)",
    "Thé dansant / après-midi dansant (seniors)",
]


def flat(sector):
    return [name for items in sector.values() for name in items]


class Page(HTMLParser):
    """Cases à cocher, accordéons et options du déroulant de budget d'une page."""

    def __init__(self, html):
        super().__init__()
        self.boxes, self.sections, self.options = [], [], []
        self._in_budget = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "input" and a.get("type") == "checkbox":
            self.boxes.append(a)
        elif tag == "div" and "matching-accordion-section" in (a.get("class") or "").split():
            self.sections.append(a.get("data-key"))
        elif tag == "select" and a.get("id") == "budget":
            self._in_budget = True
        elif tag == "option" and self._in_budget:
            self.options.append(a)

    def handle_endtag(self, tag):
        if tag == "select":
            self._in_budget = False

    def values(self, field):
        return [b["value"] for b in self.boxes if b.get("name") == field]


@pytest.fixture
def switch_off(app, monkeypatch):
    monkeypatch.setitem(app.config, "ANIMATIONS_OUVERT_DEMANDEURS", False)


def note_text(html):
    """Texte initial de la note affichée sous le déroulant de budget."""
    match = re.search(r'id="budget-note"[^>]*>(.*?)</div>', html, re.S)
    return unescape(match.group(1)).strip()


def make_demande(**overrides):
    from models import db
    from models.models import DemandeAnimation

    fields = dict(
        structure="Mairie test", telephone="0102030405", lieu_ville="Rennes", nom="Dupont",
        dates_horaires="15/12/2027", type_espace="Salle des fêtes", genre_recherche="Passage du Père Noël",
        age_range="jp_des_3", jauge="50 à 100", budget="300 à 500 €", contact_email="mairie@example.test",
        specialites_recherchees="Passage du Père Noël",
    )
    fields.update(overrides)
    demande = DemandeAnimation(**fields)
    db.session.add(demande)
    db.session.commit()
    return demande


# ── Taxonomie ────────────────────────────────────────────────────────────

def test_names_are_unique_across_both_sectors():
    names = flat(SPECIALITES) + flat(ANIMATIONS)
    assert [n for n, count in Counter(names).items() if count > 1] == []


def test_no_name_contains_a_comma():
    # La valeur d'une case est enregistrée dans une liste séparée par des virgules
    assert [n for n in flat(SPECIALITES) + flat(ANIMATIONS) if "," in n] == []


def test_home_show_names_replace_the_old_animation_show_names():
    assert ANIMATIONS["Spectacles d'animation"] == [DOMICILE_ENFANT, DOMICILE_ADULTE]
    names = set(flat(SPECIALITES)) | set(ANIMATIONS_LABELS)
    assert "Spectacle d'animation enfant" not in names and "Spectacle d'animation adulte" not in names


def test_sector_sizes_and_folder_names():
    assert "Spectacle et Animation" not in SPECIALITES
    assert len(SPECIALITES["Spectacles"]) == 46
    assert len(flat(SPECIALITES)) == 131
    assert len(flat(ANIMATIONS)) == 21
    assert len(ANIMATIONS) == 7


def test_animation_names_moved_out_of_spectacles():
    spectacles = set(flat(SPECIALITES))
    for name in MOVED + NEW_SENIORS:
        assert name in ANIMATIONS_LABELS
        assert name not in spectacles


def test_spectacle_names_that_stay_in_spectacles():
    spectacles = set(flat(SPECIALITES))
    for name in ("Spectacle thématique de Noël", "Animation Musicale",
                 "Animation mariage (cérémonie + soirée)", "Close-up", "Sosie"):
        assert name in spectacles
        assert name not in ANIMATIONS_LABELS


def test_folder_flags_and_price_notes_point_to_existing_entries():
    assert set(ANIMATIONS_DOSSIERS_PETIT_BUDGET) <= set(ANIMATIONS)
    assert set(ANIMATIONS_MENTIONS_PRIX) <= ANIMATIONS_LABELS
    assert ANIMATIONS_MENTIONS_PRIX[DOMICILE_ENFANT] == "budget indicatif : moins de 500 €"


def test_visibility_helper_and_label_detection():
    assert animations_visibles_demandeurs({}, None) is False
    assert animations_visibles_demandeurs({"ANIMATIONS_OUVERT_DEMANDEURS": True}, None) is True
    assert animations_visibles_demandeurs({}, SimpleNamespace(is_admin=True)) is True
    assert animations_visibles_demandeurs({}, SimpleNamespace(is_admin=False)) is False
    assert contains_animation(["Prestidigitateur", " Manège "]) is True
    assert contains_animation(["Prestidigitateur"]) is False
    assert contains_animation(None) is False


# ── Budgets et matching ──────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("Moins de 300 €", (0, 300)),
    ("Moins de 500 €", (0, 500)),
    ("300 à 500 €", (300, 500)),
    ("500 à 730 €", (500, 730)),
    ("730 à 930 € — Artiste / spectacle local (région / dpt)", (730, 930)),
    ("Plus de 5000 € — Événement d'envergure", (5000, 999999)),
    (LEGACY_BUDGET, (300, 300)),
])
def test_parse_budget(text, expected):
    assert matching._parse_budget(text) == expected


def test_proposed_budgets_stay_on_their_side_of_730():
    for text in BUDGETS_ANIMATION:
        low, high = matching._parse_budget(text)
        assert low is not None and high <= 730
    for text in BUDGETS_SPECTACLE:
        low, _ = matching._parse_budget(text)
        assert low >= 730


def test_low_budget_is_compatible_with_low_priced_artists_only():
    cheap = SimpleNamespace(prix_min=250, prix_max=None)
    legacy_range = SimpleNamespace(prix_min=100, prix_max=200)
    prestige = SimpleNamespace(prix_min=800, prix_max=None)
    demande = SimpleNamespace(budget="Moins de 300 €")
    assert matching._budget_compat(cheap, demande)["compatible"] is True
    assert matching._budget_compat(legacy_range, demande)["compatible"] is True
    assert matching._budget_compat(prestige, demande)["compatible"] is False


def test_specificity_counts_both_sectors():
    assert matching._TOTAL_SPECS == len(flat(SPECIALITES)) + len(flat(ANIMATIONS))


def _show(specialites):
    return SimpleNamespace(
        specialites=specialites, lieux_intervention="", regions_intervention="",
        public_categories="", public_sous_options="",
    )


def _demande(specialites, dates):
    return SimpleNamespace(
        specialites_recherchees=specialites, lieux_souhaites="", region="",
        public_categories="", public_sous_options="", dates_horaires=dates, date_debut="",
    )


@pytest.mark.parametrize("label", ["Passage du Père Noël", "Spectacle thématique de Noël"])
def test_noel_labels_only_count_in_november_and_december(label):
    out_of_season = matching.compute_score(_show(label), _demande(label, "15/07/2027"))
    in_season = matching.compute_score(_show(label), _demande(label, "15/12/2027"))
    assert out_of_season["specialites"] == 0
    assert in_season["specialites"] > 0


# ── Écrans : artistes (toujours visible) ────────────────────────────────

def test_publish_form_offers_both_accordions_with_each_name_once(logged_in_client):
    page = Page(logged_in_client.get("/submit").get_data(as_text=True))
    values = page.values("specialites")
    assert page.sections.count("specialites") == 1 and page.sections.count("animations") == 1
    assert len(values) == len(set(values)) == 152
    assert set(MOVED + NEW_SENIORS) <= set(values)


def test_edit_form_prechecks_animation_names(logged_in_client, normal_user):
    from models import db
    from models.models import Show

    show = Show(title="Père Noël et magie", user_id=normal_user.id, approved=True,
                specialites="Passage du Père Noël,Prestidigitateur")
    db.session.add(show)
    db.session.commit()

    page = Page(logged_in_client.get(f"/my/shows/{show.id}/edit").get_data(as_text=True))
    checked = {b["value"] for b in page.boxes if b.get("name") == "specialites" and "checked" in b}
    assert checked == {"Passage du Père Noël", "Prestidigitateur"}
    assert "animations" in page.sections


# ── Écrans : demandeurs (ouverts par défaut, interrupteur de secours) ───

def test_request_form_hides_animations_when_emergency_switch_is_closed(client, switch_off):
    html = client.get("/demande_animation").get_data(as_text=True)
    page = Page(html)
    assert not set(page.values("specialites_recherchees")) & ANIMATIONS_LABELS
    assert "animations_recherchees" not in page.sections
    assert [o.get("value") for o in page.options] == ["", *BUDGETS_SPECTACLE]
    assert "À partir de 300" not in html
    assert 'id="budget-note"' in html
    assert note_text(html).startswith("Spectacles professionnels")


def test_request_form_shows_animations_and_low_tiers_by_default(client):
    html = client.get("/demande_animation").get_data(as_text=True)
    page = Page(html)
    boxes = [b for b in page.boxes if b.get("name") == "specialites_recherchees"]
    animation_boxes = [b for b in boxes if b["value"] in ANIMATIONS_LABELS]
    assert {b["value"] for b in animation_boxes} == ANIMATIONS_LABELS
    assert all(b.get("data-petit-budget") == "1" for b in animation_boxes)
    assert not any("data-petit-budget" in b for b in boxes if b["value"] not in ANIMATIONS_LABELS)
    assert page.sections.count("animations_recherchees") == 1
    assert [o["value"] for o in page.options if o.get("data-bas") == "1"] == list(BUDGETS_ANIMATION)
    assert [o["value"] for o in page.options if "data-bas" not in o][1:] == list(BUDGETS_SPECTACLE)
    assert "budget indicatif : moins de 500 €" in html
    assert note_text(html).startswith("Choisissez d'abord")


def test_admin_sees_animations_even_when_emergency_switch_is_closed(admin_client, switch_off):
    page = Page(admin_client.get("/demande_animation").get_data(as_text=True))
    assert "animations_recherchees" in page.sections


def test_failed_submission_keeps_animation_accordion_for_posted_names(client, switch_off):
    response = client.post("/demande_animation", data={"specialites_recherchees": ["Manège"]})
    assert response.status_code == 400
    page = Page(response.get_data(as_text=True))
    checked = [b["value"] for b in page.boxes if b.get("name") == "specialites_recherchees" and "checked" in b]
    assert checked == ["Manège"]
    assert "animations_recherchees" in page.sections


def test_editing_a_request_keeps_a_saved_budget_that_is_no_longer_proposed(admin_client):
    demande = make_demande(budget=LEGACY_BUDGET)
    page = Page(admin_client.get(f"/demandes-animation/edit/{demande.id}").get_data(as_text=True))
    selected = [o["value"] for o in page.options if "selected" in o]
    assert selected == [LEGACY_BUDGET]


def test_admin_creation_form_offers_animations_and_keeps_its_own_budgets(admin_client):
    html = admin_client.get("/admin/demande-animation/new").get_data(as_text=True)
    page = Page(html)
    assert "animations_recherchees" in page.sections
    assert set(page.values("specialites_recherchees")) >= ANIMATIONS_LABELS
    assert '<option value="300 à 500 €">300 à 500 €</option>' in html


def test_catalogue_filter_offers_animations_by_default_and_follows_the_switch(client, app, monkeypatch):
    html = client.get("/catalogue").get_data(as_text=True)
    assert "specialite_animations" in html
    assert '<option value="Manège">' in html

    monkeypatch.setitem(app.config, "ANIMATIONS_OUVERT_DEMANDEURS", False)
    html = client.get("/catalogue").get_data(as_text=True)
    assert "specialite_animations" not in html
    assert '<option value="Manège">' not in html


def test_switch_is_open_by_default_and_can_be_closed(monkeypatch):
    import importlib

    import config

    try:
        monkeypatch.delenv("ANIMATIONS_OUVERT_DEMANDEURS", raising=False)
        assert importlib.reload(config).Config.ANIMATIONS_OUVERT_DEMANDEURS is True
        for value in ("0", "false", "Non", "off"):
            monkeypatch.setenv("ANIMATIONS_OUVERT_DEMANDEURS", value)
            assert importlib.reload(config).Config.ANIMATIONS_OUVERT_DEMANDEURS is False
        monkeypatch.setenv("ANIMATIONS_OUVERT_DEMANDEURS", "1")
        assert importlib.reload(config).Config.ANIMATIONS_OUVERT_DEMANDEURS is True
    finally:
        monkeypatch.undo()
        importlib.reload(config)
