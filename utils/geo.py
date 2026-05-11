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


def _normalize_cp(cp: Optional[str]) -> Optional[str]:
    if not cp:
        return None
    s = "".join(ch for ch in str(cp) if ch.isdigit())
    if len(s) == 4:  # zero-pad pour CP commencant par 0
        s = "0" + s
    if len(s) != 5:
        return None
    return s


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
