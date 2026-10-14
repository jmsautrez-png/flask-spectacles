"""Distances : une lookup de departement invalide ne doit pas couper les autres distances."""
import re
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import requests

from tests.test_offre_delivery import login, offer_setup  # noqa: F401
from utils import geo
from utils.matching import _dept_code_from, compute_score

CP_COMMUNES = {
    "13001": [{"centre": {"type": "Point", "coordinates": [5.37, 43.30]}}],
    "35000": [{"centre": {"type": "Point", "coordinates": [-1.67, 48.11]}}],
    "31000": [{"centre": {"type": "Point", "coordinates": [1.44, 43.60]}}],
    "34000": [{"centre": {"type": "Point", "coordinates": [3.88, 43.61]}}],
}
DEPT_COMMUNES = {
    "35": [{"centre": {"type": "Point", "coordinates": [-1.67, 48.11]}}],
    "34": [{"centre": {"type": "Point", "coordinates": [3.50, 43.60]}}],
    "2A": [{"centre": {"type": "Point", "coordinates": [8.74, 41.92]}}],
}


class _Resp:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


def _api(url, params=None, timeout=None):
    if "/departements/" in url:
        code = url.split("/departements/", 1)[1].split("/", 1)[0]
        if code == "20":
            return _Resp(404)
        return _Resp(200, DEPT_COMMUNES.get(code, []))
    return _Resp(200, CP_COMMUNES.get((params or {}).get("codePostal"), []))


@pytest.fixture(autouse=True)
def _geo_isolee(tmp_path, monkeypatch):
    monkeypatch.setattr(geo, "_INSTANCE_DIR", tmp_path)
    monkeypatch.setattr(geo, "_CACHE_FILE", tmp_path / "cp.json")
    monkeypatch.setattr(geo, "_DEPT_CACHE_FILE", tmp_path / "dept.json")
    monkeypatch.setattr(geo, "_CITY_CACHE_FILE", tmp_path / "city.json")
    monkeypatch.setattr(geo, "_CACHE", {})
    monkeypatch.setattr(geo, "_DEPT_CACHE", {})
    monkeypatch.setattr(geo, "_CITY_CACHE", {})
    monkeypatch.setattr(geo, "_CACHE_LOADED", True)
    monkeypatch.setattr(geo, "_DEPT_CACHE_LOADED", True)
    monkeypatch.setattr(geo, "_CITY_CACHE_LOADED", True)
    monkeypatch.setattr(geo, "_GEO_DOWN_UNTIL", 0.0)
    # Jamais de vrai appel reseau, y compris depuis les fixtures (hook de geocodage a l'enregistrement).
    monkeypatch.setattr(geo, "requests", SimpleNamespace(get=_api))


def test_departement_inconnu_ne_bloque_pas_les_autres_distances():
    with patch("utils.geo.requests.get", side_effect=_api):
        km_bad, _ = geo.distance_km_approx("13001", None, "13", "20")
        km_ok, approx = geo.distance_km_approx("13001", "35000", "13", "35")
    assert km_bad is None
    assert geo._geo_is_down() is False
    assert km_ok is not None and 700 < km_ok < 850
    assert approx is False


def test_erreur_reseau_ouvre_le_disjoncteur():
    with patch("utils.geo.requests.get", side_effect=requests.ConnectionError("hors ligne")):
        assert geo.coords_from_cp("13001") is None
    assert geo._geo_is_down() is True


@pytest.mark.parametrize("status", [429, 503])
def test_erreur_serveur_ouvre_le_disjoncteur(status):
    with patch("utils.geo.requests.get", return_value=_Resp(status)):
        assert geo.coords_from_cp("13001") is None
    assert geo._geo_is_down() is True


@pytest.mark.parametrize(
    "cp, attendu",
    [
        ("20000", "2A"),
        ("20190", "2A"),
        ("20200", "2B"),
        ("20620", "2B"),
        ("97100", "971"),
        ("13001", "13"),
    ],
)
def test_code_departement_depuis_cp(cp, attendu):
    assert _dept_code_from(SimpleNamespace(departement=None, code_postal=cp)) == attendu


def test_compagnie_corse_sans_cp_utilise_le_centroide_2a():
    dept = _dept_code_from(SimpleNamespace(departement=None, code_postal="20000"))
    with patch("utils.geo.requests.get", side_effect=_api):
        km, approx = geo.distance_km_approx("13001", None, "13", dept)
    assert dept == "2A"
    assert approx is True
    assert km is not None and 280 < km < 340


def _demande(**kw):
    base = dict(
        code_postal="31000", region="Occitanie", departement="Haute-Garonne (31)",
        latitude=None, longitude=None, portee_nationale=False,
        specialites_recherchees="", lieux_souhaites="", age_range=None,
        public_categories="", public_sous_options="", date_debut=None, dates_horaires=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _compagnie(**kw):
    base = dict(
        code_postal=None, latitude=None, longitude=None, departement=None,
        region="Occitanie", ville=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _spectacle(compagnie, **kw):
    base = dict(
        specialites="", lieux_intervention="", regions_intervention="", location="",
        region="", labels="", user=compagnie, code_postal=None, departement=None,
        latitude=None, longitude=None, age_range=None,
        public_categories="", public_sous_options="",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_compte_sans_localisation_indique_cp_manquant():
    score = compute_score(_spectacle(_compagnie()), _demande())
    assert score["distance_km_display"] is None
    assert score["distance_reason"] == "cp_manquant"


def test_cp_invalide_sans_departement_indique_cp_manquant():
    score = compute_score(_spectacle(_compagnie(code_postal="123")), _demande())
    assert score["distance_km_display"] is None
    assert score["distance_reason"] == "cp_manquant"


def test_compte_avec_cp_a_une_distance_et_aucune_cause():
    score = compute_score(_spectacle(_compagnie(code_postal="34000")), _demande())
    assert 150 < score["distance_km_display"] < 250
    assert score["distance_approx"] is False
    assert score["distance_reason"] is None


def test_departement_seul_donne_une_distance_approximative_sans_cause():
    score = compute_score(_spectacle(_compagnie(departement="Hérault (34)")), _demande())
    assert score["distance_approx"] is True
    assert score["distance_km_display"] is not None
    assert score["distance_reason"] is None


def test_cp_present_mais_api_en_panne_indique_geo_indisponible():
    with patch("utils.geo.requests.get", side_effect=requests.ConnectionError("hors ligne")):
        score = compute_score(_spectacle(_compagnie(code_postal="34000")), _demande())
    assert score["distance_km_display"] is None
    assert score["distance_reason"] == "geo_indisponible"


def test_fiche_sans_compte_utilise_sa_propre_localisation():
    avec_cp = compute_score(_spectacle(None, code_postal="34000"), _demande())
    sans_cp = compute_score(_spectacle(None), _demande())
    assert avec_cp["distance_km_display"] is not None
    assert avec_cp["distance_reason"] is None
    assert sans_cp["distance_km_display"] is None
    assert sans_cp["distance_reason"] == "cp_manquant"


def _page_matching(client, admin, demande):
    login(client, admin)
    response = client.get(f"/admin/envoyer-demande/{demande.id}")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_liste_admin_signale_cp_manquant_avec_lien_vers_le_compte(client, offer_setup):
    user, admin, _, demande, _ = offer_setup
    html = _page_matching(client, admin, demande)
    assert "⚠ CP manquant" in html
    assert f'href="/admin/users#details-{user.id}" target="_blank"' in html


def test_liste_admin_affiche_les_km_quand_le_compte_a_un_cp(client, offer_setup):
    from models import db

    user, admin, _, demande, _ = offer_setup
    user.code_postal = "34000"
    demande.code_postal = "31000"
    db.session.commit()
    html = _page_matching(client, admin, demande)
    assert "CP manquant" not in html
    assert re.search(r"\b19\d km", html)


def test_liste_admin_signale_geo_indisponible_si_la_position_est_introuvable(client, offer_setup):
    from models import db

    user, admin, _, demande, _ = offer_setup
    user.code_postal = "34000"  # la demande garde son CP inconnu (99991)
    db.session.commit()
    html = _page_matching(client, admin, demande)
    assert "Géo indisponible" in html
    assert "CP manquant" not in html


def test_page_utilisateurs_ouvre_la_ligne_ciblee_par_l_ancre(client, offer_setup):
    user, admin, *_ = offer_setup
    login(client, admin)
    html = client.get("/admin/users").get_data(as_text=True)
    assert f'id="details-{user.id}"' in html
    assert "window.location.hash" in html
