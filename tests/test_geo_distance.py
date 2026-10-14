"""Distances : une lookup de departement invalide ne doit pas couper les autres distances."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import requests

from utils import geo
from utils.matching import _dept_code_from

CP_COMMUNES = {
    "13001": [{"centre": {"type": "Point", "coordinates": [5.37, 43.30]}}],
    "35000": [{"centre": {"type": "Point", "coordinates": [-1.67, 48.11]}}],
}
DEPT_COMMUNES = {
    "35": [{"centre": {"type": "Point", "coordinates": [-1.67, 48.11]}}],
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
