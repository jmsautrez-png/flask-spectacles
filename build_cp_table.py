"""Regenere utils/cp_coords.json : coordonnees (lat, lon) de chaque code postal francais.

Source : API Decoupage administratif (https://geo.api.gouv.fr), licence ouverte Etalab 2.0.
Une seule requete (toutes les communes). Pour un code postal partage par plusieurs
communes, on moyenne leurs centres (meme regle que utils.geo._fetch_coords).

Usage : python build_cp_table.py
A relancer rarement (creation ou suppression de codes postaux).
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import requests

URL = "https://geo.api.gouv.fr/communes"
OUT = Path(__file__).resolve().parent / "utils" / "cp_coords.json"
MIN_CODES_POSTAUX = 6000  # garde-fou : une reponse tronquee ne doit pas ecraser la table


def main() -> int:
    r = requests.get(URL, params={"fields": "code,codesPostaux,centre", "format": "json"}, timeout=120)
    r.raise_for_status()

    par_cp = defaultdict(list)
    for commune in r.json():
        coords = (commune.get("centre") or {}).get("coordinates")
        if not coords or len(coords) != 2:
            continue
        for cp in commune.get("codesPostaux") or []:
            par_cp[cp].append(coords)

    table = {
        cp: [round(sum(c[1] for c in v) / len(v), 4), round(sum(c[0] for c in v) / len(v), 4)]
        for cp, v in sorted(par_cp.items())
    }
    if len(table) < MIN_CODES_POSTAUX:
        print(f"[ERREUR] {len(table)} codes postaux seulement : table non ecrite.")
        return 1

    OUT.write_text(json.dumps(table, separators=(",", ":")), encoding="utf-8")
    print(f"{len(table)} codes postaux ecrits dans {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
