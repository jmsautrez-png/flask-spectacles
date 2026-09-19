"""Script one-shot : remplit `latitude` / `longitude` pour User, Show, DemandeAnimation.

Usage :
    python backfill_geo.py                # normal (skip enregistrements déjà géocodés)
    python backfill_geo.py --force        # regéocode même si lat/lon présents
    python backfill_geo.py --dry-run      # aucun commit, juste les stats

Prérequis : la colonne latitude/longitude doit exister (migrations _run_critical_migrations
appliquées automatiquement au boot de app.py, ou via ALTER TABLE manuel).

Sur Render : lancer via un shell one-shot après déploiement.
En local : `python backfill_geo.py` puis vérifier les logs.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Iterable

from app import app
from models import db
from models.models import DemandeAnimation, Show, User
from utils.geo import coords_from_cp


BATCH_COMMIT_SIZE = 20


def _backfill_batch(label: str, objs: Iterable, force: bool, dry_run: bool) -> tuple[int, int, int]:
    """Retourne (traites, geocodes, ignores)."""
    traites = 0
    geocodes = 0
    ignores = 0
    since_commit = 0

    for obj in objs:
        traites += 1
        cp = (getattr(obj, "code_postal", None) or "").strip()
        if not cp:
            ignores += 1
            continue

        has_coords = obj.latitude is not None and obj.longitude is not None
        if has_coords and not force:
            ignores += 1
            continue

        coords = coords_from_cp(cp)
        if not coords:
            ignores += 1
            continue

        obj.latitude, obj.longitude = coords
        geocodes += 1
        since_commit += 1

        if not dry_run and since_commit >= BATCH_COMMIT_SIZE:
            db.session.commit()
            since_commit = 0
            print(f"  {label} : {geocodes} géocodés / {traites} traités…", flush=True)

    if not dry_run and since_commit > 0:
        db.session.commit()

    return traites, geocodes, ignores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Regéocode même si lat/lon présents")
    parser.add_argument("--dry-run", action="store_true", help="Aucune écriture en base")
    args = parser.parse_args()

    start = time.time()

    with app.app_context():
        print(f"[backfill_geo] début (force={args.force}, dry_run={args.dry_run})", flush=True)

        # 1) Users
        users = User.query.all()
        print(f"[backfill_geo] {len(users)} users à traiter", flush=True)
        u_tot, u_geo, u_ign = _backfill_batch("users", users, args.force, args.dry_run)

        # 2) Shows
        shows = Show.query.all()
        print(f"[backfill_geo] {len(shows)} shows à traiter", flush=True)
        s_tot, s_geo, s_ign = _backfill_batch("shows", shows, args.force, args.dry_run)

        # 3) Demandes d'animation
        demandes = DemandeAnimation.query.all()
        print(f"[backfill_geo] {len(demandes)} demandes à traiter", flush=True)
        d_tot, d_geo, d_ign = _backfill_batch("demandes", demandes, args.force, args.dry_run)

    dur = time.time() - start
    print("─" * 60, flush=True)
    print(f"[backfill_geo] terminé en {dur:.1f}s", flush=True)
    print(f"  users     : {u_geo:>4} géocodés  /  {u_ign:>4} ignorés  /  {u_tot:>4} total", flush=True)
    print(f"  shows     : {s_geo:>4} géocodés  /  {s_ign:>4} ignorés  /  {s_tot:>4} total", flush=True)
    print(f"  demandes  : {d_geo:>4} géocodés  /  {d_ign:>4} ignorés  /  {d_tot:>4} total", flush=True)
    if args.dry_run:
        print("[backfill_geo] DRY-RUN : aucun changement écrit en base", flush=True)


if __name__ == "__main__":
    sys.exit(main())
