"""
Ajoute le label « pro_verifie » à TOUS les spectacles, en une passe.

Idempotent et non destructif :
  - préserve les labels déjà présents ;
  - n'ajoute pas « pro_verifie » s'il y est déjà ;
  - respecte le maximum de 2 labels (un show déjà plein est laissé tel quel) ;
  - ignore les shows portant « edition_libre » (sémantiquement opposé) ;
  - dry-run par défaut : AUCUNE écriture sans l'option --apply.

Cible la base configurée par l'app (DATABASE_URL distant si présent, sinon SQLite local).

Usage :
    python set_label_pro_verifie.py            # dry-run (simulation)
    python set_label_pro_verifie.py --apply    # applique réellement
"""
from __future__ import annotations

import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import app as appmod
from models.models import db, Show

NEW_LABEL = "pro_verifie"
NEUTRAL = "edition_libre"
MAX_LABELS = 2


def merge_label(existing: str | None) -> tuple[str | None, str]:
    """Retourne (nouvelle_valeur, action)."""
    codes = [c.strip() for c in (existing or "").split(",") if c.strip()]
    if NEUTRAL in codes:
        return existing, "ignore_edition_libre"
    if NEW_LABEL in codes:
        return existing, "deja_present"
    if len(codes) >= MAX_LABELS:
        return existing, "ignore_plein"
    codes.append(NEW_LABEL)
    return ",".join(codes), "ajoute"


def main() -> None:
    apply = "--apply" in sys.argv

    with appmod.app.app_context():
        url = str(db.engine.url)
        cible = url.split("@")[-1].split("/")[0] if "@" in url else url
        print(f"Base cible : {cible}")
        print(f"Mode       : {'APPLICATION REELLE' if apply else 'DRY-RUN (simulation)'}")
        print("-" * 60)

        shows = Show.query.all()
        stats = {"ajoute": 0, "deja_present": 0, "ignore_plein": 0, "ignore_edition_libre": 0}

        for show in shows:
            new_value, action = merge_label(show.labels)
            stats[action] += 1
            if action == "ajoute" and apply:
                show.labels = new_value

        if apply:
            db.session.commit()

        total = len(shows)
        print(f"Spectacles total          : {total}")
        print(f"  + pro_verifie ajoute     : {stats['ajoute']}")
        print(f"  = deja pro_verifie       : {stats['deja_present']}")
        print(f"  ~ ignores (2 labels max) : {stats['ignore_plein']}")
        print(f"  ~ ignores (edition_libre): {stats['ignore_edition_libre']}")
        print("-" * 60)
        if apply:
            print("OK : modifications enregistrees.")
        else:
            print("Dry-run : aucune ecriture. Relancez avec --apply pour appliquer.")


if __name__ == "__main__":
    main()
