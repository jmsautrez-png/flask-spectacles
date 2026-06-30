"""Geo helpers : Haversine + lookup CP -> (lat, lon).

Utilise l'API gratuite https://geo.api.gouv.fr/communes (sans cle).
Mise en cache disque dans instance/cp_coords_cache.json.
"""
from __future__ import annotations

import json
import os
import threading
from math import radians, sin, cos, asin, sqrt
from pathlib import Path
from typing import Optional, Tuple

try:
    import requests
except ImportError:  # pragma: no cover - dep deja presente
    requests = None

# ---------------------------------------------------------------------------
# Cache disque
# ---------------------------------------------------------------------------
_LOCK = threading.Lock()
_CACHE: dict[str, Optional[list[float]]] = {}
_CACHE_LOADED = False
_INSTANCE_DIR = Path(__file__).resolve().parent.parent / "instance"
_CACHE_FILE = _INSTANCE_DIR / "cp_coords_cache.json"

_CITY_CACHE: dict[str, Optional[list[float]]] = {}
_CITY_CACHE_LOADED = False
_CITY_CACHE_FILE = _INSTANCE_DIR / "city_coords_cache.json"


def _load_cache() -> None:
    global _CACHE_LOADED
    if _CACHE_LOADED:
        return
    with _LOCK:
        if _CACHE_LOADED:
            return
        try:
            if _CACHE_FILE.exists():
                _CACHE.update(json.loads(_CACHE_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
        _CACHE_LOADED = True


def _save_cache() -> None:
    try:
        _INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps(_CACHE, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    except Exception:
        pass


def _load_city_cache() -> None:
    global _CITY_CACHE_LOADED
    if _CITY_CACHE_LOADED:
        return
    with _LOCK:
        if _CITY_CACHE_LOADED:
            return
        try:
            if _CITY_CACHE_FILE.exists():
                _CITY_CACHE.update(json.loads(_CITY_CACHE_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
        _CITY_CACHE_LOADED = True


def _save_city_cache() -> None:
    try:
        _INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        _CITY_CACHE_FILE.write_text(
            json.dumps(_CITY_CACHE, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    except Exception:
        pass


def _normalize_cp(cp: Optional[str]) -> Optional[str]:
    if not cp:
        return None
    s = "".join(ch for ch in str(cp) if ch.isdigit())
    if len(s) == 4:  # zero-pad pour CP commencant par 0
        s = "0" + s
    if len(s) != 5:
        return None
    return s


def _normalize_city(city: Optional[str]) -> Optional[str]:
    if not city:
        return None
    s = str(city).strip()
    if not s:
        return None
    for sep in ("·", ",", " / ", " - "):
        if sep in s:
            s = s.split(sep, 1)[0].strip()
    return s or None


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------
def coords_from_cp(cp: Optional[str]) -> Optional[Tuple[float, float]]:
    """Retourne (lat, lon) pour un code postal francais, ou None.

    Resultats mis en cache (memoire + disque).
    """
    cp = _normalize_cp(cp)
    if not cp:
        return None
    _load_cache()
    if cp in _CACHE:
        v = _CACHE[cp]
        return (v[0], v[1]) if v else None
    coords = _fetch_coords(cp)
    with _LOCK:
        _CACHE[cp] = list(coords) if coords else None
        _save_cache()
    return coords


def coords_from_city(
    city: Optional[str],
    cp: Optional[str] = None,
    dept: Optional[str] = None,
) -> Optional[Tuple[float, float]]:
    """Retourne (lat, lon) pour une commune francaise, ou None.

    Utilise geo.api.gouv.fr/communes avec cache memoire + disque.
    Le code postal est utilise en priorité lorsqu'il est disponible.
    """
    city = _normalize_city(city)
    if not city:
        return None
    cp_norm = _normalize_cp(cp)
    dept_norm = _normalize_dept(dept)
    cache_key = f"{city.casefold()}|{cp_norm or ''}|{dept_norm or ''}"
    _load_city_cache()
    if cache_key in _CITY_CACHE:
        v = _CITY_CACHE[cache_key]
        return (v[0], v[1]) if v else None
    coords = _fetch_city_coords(city, cp_norm, dept_norm)
    with _LOCK:
        _CITY_CACHE[cache_key] = list(coords) if coords else None
        _save_city_cache()
    return coords


def _fetch_city_coords(
    city: str,
    cp: Optional[str] = None,
    dept: Optional[str] = None,
) -> Optional[Tuple[float, float]]:
    if requests is None:
        return None
    try:
        params = {
            "nom": city,
            "fields": "centre,nom,code,codePostal",
            "format": "json",
            "boost": "population",
        }
        if cp:
            params["codePostal"] = cp
        if dept:
            params["codeDepartement"] = dept
        r = requests.get("https://geo.api.gouv.fr/communes", params=params, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        first = data[0] or {}
        centre = first.get("centre") or {}
        coords = centre.get("coordinates")
        if coords and len(coords) == 2:
            return float(coords[1]), float(coords[0])
        return None
    except Exception:
        return None


def _fetch_coords(cp: str) -> Optional[Tuple[float, float]]:
    if requests is None:
        return None
    try:
        r = requests.get(
            "https://geo.api.gouv.fr/communes",
            params={"codePostal": cp, "fields": "centre", "format": "json"},
            timeout=5,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        # Plusieurs communes peuvent partager un CP : on moyenne pour avoir
        # un point representatif.
        lats, lons = [], []
        for commune in data:
            centre = commune.get("centre") or {}
            coords = centre.get("coordinates")
            if coords and len(coords) == 2:
                lons.append(float(coords[0]))
                lats.append(float(coords[1]))
        if not lats:
            return None
        return (sum(lats) / len(lats), sum(lons) / len(lons))
    except Exception:
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance a vol d'oiseau en km entre deux points (lat, lon en degres)."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


def distance_km(cp_a: Optional[str], cp_b: Optional[str]) -> Optional[float]:
    """Distance entre deux codes postaux, ou None si l'un est introuvable."""
    a = coords_from_cp(cp_a)
    b = coords_from_cp(cp_b)
    if not a or not b:
        return None
    return haversine_km(a[0], a[1], b[0], b[1])


# ---------------------------------------------------------------------------
# Fallback departement : centroide du dpt via geo.api.gouv.fr
# ---------------------------------------------------------------------------
_DEPT_CACHE: dict[str, Optional[list[float]]] = {}
_DEPT_CACHE_FILE = _INSTANCE_DIR / "dept_coords_cache.json"
_DEPT_CACHE_LOADED = False


def _load_dept_cache() -> None:
    global _DEPT_CACHE_LOADED
    if _DEPT_CACHE_LOADED:
        return
    with _LOCK:
        if _DEPT_CACHE_LOADED:
            return
        try:
            if _DEPT_CACHE_FILE.exists():
                _DEPT_CACHE.update(json.loads(_DEPT_CACHE_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
        _DEPT_CACHE_LOADED = True


def _save_dept_cache() -> None:
    try:
        _INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        _DEPT_CACHE_FILE.write_text(
            json.dumps(_DEPT_CACHE, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    except Exception:
        pass


def _normalize_dept(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    s = str(code).strip().upper()
    # Garde lettres+chiffres (Corse 2A/2B)
    s = "".join(ch for ch in s if ch.isalnum())
    if not s:
        return None
    # Departements metropolitains numeriques sur 2 chiffres
    if s.isdigit() and len(s) == 1:
        s = "0" + s
    return s[:3] if s.startswith("97") else s[:2]


def coords_from_dept(code: Optional[str]) -> Optional[Tuple[float, float]]:
    """Centroide approximatif d'un departement (lat, lon), ou None."""
    code = _normalize_dept(code)
    if not code:
        return None
    _load_dept_cache()
    if code in _DEPT_CACHE:
        v = _DEPT_CACHE[code]
        return (v[0], v[1]) if v else None
    coords = _fetch_dept_coords(code)
    with _LOCK:
        _DEPT_CACHE[code] = list(coords) if coords else None
        _save_dept_cache()
    return coords


def _fetch_dept_coords(code: str) -> Optional[Tuple[float, float]]:
    if requests is None:
        return None
    try:
        r = requests.get(
            f"https://geo.api.gouv.fr/departements/{code}/communes",
            params={"fields": "centre", "format": "json"},
            timeout=5,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        lats, lons = [], []
        for commune in data:
            centre = commune.get("centre") or {}
            coords = centre.get("coordinates")
            if coords and len(coords) == 2:
                lons.append(float(coords[0]))
                lats.append(float(coords[1]))
        if not lats:
            return None
        return (sum(lats) / len(lats), sum(lons) / len(lons))
    except Exception:
        return None


def distance_km_approx(
    cp_a: Optional[str],
    cp_b: Optional[str],
    dept_a: Optional[str] = None,
    dept_b: Optional[str] = None,
) -> Tuple[Optional[float], bool]:
    """Distance entre deux points avec fallback departement.

    Retourne (km, is_approx).
    - is_approx=False : calcul base sur les CP (precis).
    - is_approx=True  : au moins un cote utilise le centroide du departement.
    - (None, False)   : aucune information geo exploitable.
    """
    a = coords_from_cp(cp_a)
    b = coords_from_cp(cp_b)
    approx = False
    if not a:
        a = coords_from_dept(dept_a)
        if a:
            approx = True
    if not b:
        b = coords_from_dept(dept_b)
        if b:
            approx = True
    if not a or not b:
        return None, False
    return haversine_km(a[0], a[1], b[0], b[1]), approx



def distance_score(km: Optional[float]) -> float:
    """Convertit une distance (km) en ratio 0..1 pour le matching.

    <= 50 km   -> 1.00
    <= 100 km  -> 0.85
    <= 200 km  -> 0.65
    <= 300 km  -> 0.40
    <= 500 km  -> 0.20
    > 500 km   -> 0.0
    None       -> None (le caller decide du fallback)
    """
    if km is None:
        return 0.0
    if km <= 50:
        return 1.0
    if km <= 100:
        return 0.85
    if km <= 200:
        return 0.65
    if km <= 300:
        return 0.40
    if km <= 500:
        return 0.20
    return 0.0


# ---------------------------------------------------------------------------
# Centroides departements (fallback statique, lat/lon approximatifs)
# Permet d'eviter des appels reseau a geo.api.gouv.fr lors du filtrage par rayon
# ---------------------------------------------------------------------------
DEPT_CENTROIDS_STATIC: dict[str, Tuple[float, float]] = {
    "01": (46.10, 5.35), "02": (49.55, 3.55), "03": (46.40, 3.20), "04": (44.10, 6.25),
    "05": (44.65, 6.40), "06": (43.92, 7.15), "07": (44.75, 4.40), "08": (49.60, 4.65),
    "09": (42.95, 1.50), "10": (48.30, 4.10), "11": (43.10, 2.50), "12": (44.30, 2.70),
    "13": (43.55, 5.10), "14": (49.10, -0.30), "15": (45.05, 2.65), "16": (45.70, 0.20),
    "17": (45.85, -0.80), "18": (47.05, 2.50), "19": (45.35, 1.85), "21": (47.45, 4.75),
    "22": (48.50, -2.85), "23": (46.10, 2.05), "24": (45.10, 0.75), "25": (47.15, 6.40),
    "26": (44.75, 5.15), "27": (49.10, 1.10), "28": (48.45, 1.45), "29": (48.25, -4.00),
    "2A": (41.85, 8.95), "2B": (42.45, 9.15), "30": (44.05, 4.20), "31": (43.40, 1.45),
    "32": (43.65, 0.55), "33": (44.85, -0.45), "34": (43.60, 3.40), "35": (48.15, -1.65),
    "36": (46.80, 1.55), "37": (47.25, 0.70), "38": (45.25, 5.55), "39": (46.70, 5.75),
    "40": (43.95, -0.85), "41": (47.60, 1.40), "42": (45.65, 4.30), "43": (45.10, 3.80),
    "44": (47.30, -1.65), "45": (47.85, 2.30), "46": (44.60, 1.65), "47": (44.35, 0.60),
    "48": (44.55, 3.50), "49": (47.40, -0.55), "50": (49.10, -1.30), "51": (49.05, 4.15),
    "52": (48.10, 5.15), "53": (48.10, -0.65), "54": (48.85, 6.15), "55": (49.00, 5.40),
    "56": (47.85, -2.85), "57": (49.05, 6.65), "58": (47.10, 3.55), "59": (50.45, 3.15),
    "60": (49.40, 2.45), "61": (48.65, 0.10), "62": (50.50, 2.30), "63": (45.75, 3.15),
    "64": (43.30, -0.80), "65": (43.05, 0.15), "66": (42.60, 2.55), "67": (48.65, 7.65),
    "68": (47.85, 7.30), "69": (45.85, 4.65), "70": (47.60, 6.05), "71": (46.65, 4.55),
    "72": (47.95, 0.15), "73": (45.50, 6.40), "74": (46.05, 6.40), "75": (48.86, 2.35),
    "76": (49.65, 1.00), "77": (48.60, 3.05), "78": (48.80, 1.85), "79": (46.55, -0.30),
    "80": (49.95, 2.30), "81": (43.85, 2.15), "82": (44.05, 1.30), "83": (43.45, 6.20),
    "84": (44.00, 5.15), "85": (46.70, -1.40), "86": (46.55, 0.45), "87": (45.85, 1.20),
    "88": (48.20, 6.45), "89": (47.80, 3.55), "90": (47.65, 6.95), "91": (48.55, 2.25),
    "92": (48.85, 2.25), "93": (48.90, 2.45), "94": (48.80, 2.45), "95": (49.10, 2.10),
    "971": (16.25, -61.55), "972": (14.65, -61.00), "973": (4.00, -53.10),
    "974": (-21.10, 55.55), "976": (-12.85, 45.15),
}

# Libelles humains pour affichage dans des <select>
DEPT_LABELS: dict[str, str] = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse",
    "24": "Dordogne", "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir",
    "29": "Finistère", "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde",
    "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire",
    "38": "Isère", "39": "Jura", "40": "Landes", "41": "Loir-et-Cher", "42": "Loire",
    "43": "Haute-Loire", "44": "Loire-Atlantique", "45": "Loiret", "46": "Lot",
    "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche",
    "51": "Marne", "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle",
    "55": "Meuse", "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord",
    "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône",
    "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie",
    "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne",
    "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort", "91": "Essonne",
    "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis", "94": "Val-de-Marne",
    "95": "Val-d'Oise", "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
    "974": "La Réunion", "976": "Mayotte",
}

# Mapping département (code) → région (nom officiel)
DEPT_TO_REGION = {
    # Île-de-France
    "75": "Île-de-France", "77": "Île-de-France", "78": "Île-de-France",
    "91": "Île-de-France", "92": "Île-de-France", "93": "Île-de-France",
    "94": "Île-de-France", "95": "Île-de-France",
    # Hauts-de-France
    "02": "Hauts-de-France", "59": "Hauts-de-France", "60": "Hauts-de-France",
    "62": "Hauts-de-France", "80": "Hauts-de-France",
    # Grand Est
    "08": "Grand Est", "10": "Grand Est", "51": "Grand Est", "52": "Grand Est",
    "54": "Grand Est", "55": "Grand Est", "57": "Grand Est", "88": "Grand Est",
    # Normandie
    "14": "Normandie", "27": "Normandie", "50": "Normandie", "61": "Normandie", "76": "Normandie",
    # Bretagne
    "22": "Bretagne", "29": "Bretagne", "35": "Bretagne", "56": "Bretagne",
    # Pays de la Loire
    "44": "Pays de la Loire", "49": "Pays de la Loire", "53": "Pays de la Loire", "72": "Pays de la Loire", "85": "Pays de la Loire",
    # Centre-Val de Loire
    "18": "Centre-Val de Loire", "28": "Centre-Val de Loire", "36": "Centre-Val de Loire",
    "37": "Centre-Val de Loire", "41": "Centre-Val de Loire", "45": "Centre-Val de Loire",
    # Bourgogne-Franche-Comté
    "21": "Bourgogne-Franche-Comté", "25": "Bourgogne-Franche-Comté", "39": "Bourgogne-Franche-Comté",
    "58": "Bourgogne-Franche-Comté", "70": "Bourgogne-Franche-Comté", "71": "Bourgogne-Franche-Comté",
    "89": "Bourgogne-Franche-Comté", "90": "Bourgogne-Franche-Comté",
    # Auvergne-Rhône-Alpes
    "01": "Auvergne-Rhône-Alpes", "03": "Auvergne-Rhône-Alpes", "07": "Auvergne-Rhône-Alpes",
    "15": "Auvergne-Rhône-Alpes", "26": "Auvergne-Rhône-Alpes", "38": "Auvergne-Rhône-Alpes",
    "42": "Auvergne-Rhône-Alpes", "43": "Auvergne-Rhône-Alpes", "63": "Auvergne-Rhône-Alpes",
    "69": "Auvergne-Rhône-Alpes", "73": "Auvergne-Rhône-Alpes", "74": "Auvergne-Rhône-Alpes",
    # Nouvelle-Aquitaine
    "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine", "19": "Nouvelle-Aquitaine",
    "23": "Nouvelle-Aquitaine", "24": "Nouvelle-Aquitaine", "33": "Nouvelle-Aquitaine",
    "40": "Nouvelle-Aquitaine", "47": "Nouvelle-Aquitaine", "64": "Nouvelle-Aquitaine",
    "79": "Nouvelle-Aquitaine", "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
    # Occitanie
    "09": "Occitanie", "11": "Occitanie", "12": "Occitanie", "30": "Occitanie",
    "31": "Occitanie", "32": "Occitanie", "34": "Occitanie", "46": "Occitanie",
    "48": "Occitanie", "65": "Occitanie", "66": "Occitanie", "81": "Occitanie", "82": "Occitanie",
    # Provence-Alpes-Côte d'Azur
    "04": "Provence-Alpes-Côte d'Azur", "05": "Provence-Alpes-Côte d'Azur",
    "06": "Provence-Alpes-Côte d'Azur", "13": "Provence-Alpes-Côte d'Azur",
    "83": "Provence-Alpes-Côte d'Azur", "84": "Provence-Alpes-Côte d'Azur",
    # Corse
    "20": "Corse", "2A": "Corse", "2B": "Corse",
    # Outre-mer
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
    "974": "La Réunion", "976": "Mayotte",
}


def dept_to_region(dept_code: Optional[str]) -> Optional[str]:
    """Retourne le nom de la région pour un code département donné.
    
    Args:
        dept_code: Code département (ex: "75", "2A") ou None
        
    Returns:
        Nom de la région (ex: "Île-de-France") ou None si non trouvé
    """
    if not dept_code:
        return None
    code = dept_code.strip().upper()
    return DEPT_TO_REGION.get(code)


def depts_within_radius(code: Optional[str], radius_km: float) -> list[str]:
    """Retourne la liste des codes departements dont le centroide est dans le rayon.

    Inclut toujours le departement lui-meme s'il est connu. Utilise les centroides
    statiques (DEPT_CENTROIDS_STATIC) pour eviter des appels reseau.
    """
    norm = _normalize_dept(code)
    if not norm or norm not in DEPT_CENTROIDS_STATIC:
        return []
    if radius_km <= 0:
        return [norm]
    lat0, lon0 = DEPT_CENTROIDS_STATIC[norm]
    res: list[str] = []
    for c, (lat, lon) in DEPT_CENTROIDS_STATIC.items():
        if haversine_km(lat0, lon0, lat, lon) <= radius_km:
            res.append(c)
    return res
