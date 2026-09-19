"""Test de non-régression Option A (géocodage stocké).

Vérifie :
  1. find_matching_shows ne fait AUCUN appel HTTP externe (patch requests.get).
  2. Le score total avec lat/lon stockés est identique à celui obtenu via distance CP live.
  3. Si lat/lon sont mis à None, fallback vers coords_from_cp fonctionne toujours.
  4. Le hook SQLAlchemy _auto_geocode_from_cp populate bien lat/lon à l'insert.
"""
from unittest.mock import patch
import time

from app import app
from models import db
from models.models import Show, User, DemandeAnimation
from utils.geo import distance_km, distance_km_objs, coords_from_cp
from utils.matching import find_matching_shows, compute_score


def fail_http(*a, **k):
    raise RuntimeError(f"HTTP interdit : {a}")


def main():
    errors = []
    with app.app_context():
        demandes = DemandeAnimation.query.all()
        shows = Show.query.filter_by(approved=True).all()
        print(f"→ {len(demandes)} demandes, {len(shows)} shows en base")

        # ── TEST 1 : matching complet sans réseau ──
        if demandes and shows:
            d = demandes[0]
            with patch("utils.geo.requests.get", side_effect=fail_http):
                t = time.time()
                results = find_matching_shows(d, shows, min_score=1)
                dur = (time.time() - t) * 1000
            print(f"[TEST 1] find_matching_shows : {len(results)} matches en {dur:.1f} ms sans HTTP  ✅")
        else:
            errors.append("Pas de données pour TEST 1")

        # ── TEST 2 : distance identique lat/lon vs CP-live ──
        d = demandes[0] if demandes else None
        s = None
        for cand in shows:
            if cand.user and cand.user.code_postal:
                s = cand
                break
        if d and s and d.code_postal and s.user.code_postal:
            dist_cp = distance_km(d.code_postal, s.user.code_postal)
            dist_obj = distance_km_objs(d, s.user)
            if dist_cp is None or dist_obj is None:
                errors.append(f"[TEST 2] distance None (cp={dist_cp}, obj={dist_obj})")
            elif abs(dist_cp - dist_obj) > 0.5:  # tolérance 0.5 km
                errors.append(f"[TEST 2] écart : cp={dist_cp:.2f} vs obj={dist_obj:.2f}")
            else:
                print(f"[TEST 2] distance identique : CP={dist_cp:.2f} km ≈ obj={dist_obj:.2f} km  ✅")
        else:
            print("[TEST 2] skip (pas de couple demande/show utilisable)")

        # ── TEST 3 : fallback CP si lat/lon = None ──
        if d and s and s.user.code_postal:
            saved_lat, saved_lon = s.user.latitude, s.user.longitude
            s.user.latitude = None
            s.user.longitude = None
            dist_fallback = distance_km_objs(d, s.user)
            s.user.latitude, s.user.longitude = saved_lat, saved_lon
            if dist_fallback is None:
                errors.append("[TEST 3] fallback CP a donné None")
            else:
                print(f"[TEST 3] fallback CP quand lat/lon=None : {dist_fallback:.2f} km  ✅")

        # ── TEST 4 : hook auto-géocode à l'insert ──
        # On crée un User factice avec un CP mais sans lat/lon, puis flush → le
        # hook before_insert doit populer lat/lon.
        # NB: on rollback ensuite pour ne pas polluer la DB.
        try:
            u = User(
                username=f"__test_geo_{int(time.time())}",
                password_hash="x" * 60,
                email=f"__test_geo_{int(time.time())}@example.invalid",
                code_postal="75001",
            )
            db.session.add(u)
            db.session.flush()
            if u.latitude is not None and u.longitude is not None:
                print(f"[TEST 4] hook auto-géocode : User.lat={u.latitude:.4f}, lon={u.longitude:.4f}  ✅")
            else:
                errors.append(f"[TEST 4] hook n'a pas populé lat/lon (lat={u.latitude}, lon={u.longitude})")
        except Exception as e:
            errors.append(f"[TEST 4] exception : {e}")
        finally:
            db.session.rollback()

        # ── TEST 5 : compute_score renvoie des données cohérentes ──
        if d and s:
            score = compute_score(s, d)
            if isinstance(score, dict) and "total" in score:
                print(f"[TEST 5] compute_score OK : total={score.get('total')}, compatible={score.get('compatible')}  ✅")
            else:
                errors.append(f"[TEST 5] compute_score forme inattendue : {type(score)} keys={list(score.keys()) if isinstance(score, dict) else 'N/A'}")

    print("─" * 60)
    if errors:
        print("❌ ÉCHECS :")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
