"""
Script one-shot : corrige les régions corrompues (mojibake) en base.
'ÃŽle-de-France' -> 'Île-de-France' et autres variantes.

Usage (Render shell) :
    python fix_mojibake_regions.py
"""
from app import app, db
from models.models import DemandeAnimation, Company, Show

# Table de correspondance mojibake -> correct
REPLACEMENTS = {
    'ÃŽle-de-France': 'Île-de-France',
    'Ã®le-de-France': 'île-de-France',
    'RhÃ´ne': 'Rhône',
    'Provence-Alpes-CÃ´te': 'Provence-Alpes-Côte',
    'BourgogneFranche-ComtÃ©': 'Bourgogne-Franche-Comté',
    'Bourgogne-Franche-ComtÃ©': 'Bourgogne-Franche-Comté',
    'Auvergne-RhÃ´ne-Alpes': 'Auvergne-Rhône-Alpes',
    "Provence-Alpes-CÃ´te d'Azur": "Provence-Alpes-Côte d'Azur",
}


def fix_value(val):
    if not val:
        return val, False
    new = val
    for bad, good in REPLACEMENTS.items():
        new = new.replace(bad, good)
    return new, (new != val)


def main():
    with app.app_context():
        total = 0

        # DemandeAnimation.region
        for d in DemandeAnimation.query.all():
            new, changed = fix_value(d.region)
            if changed:
                print(f"  DemandeAnimation#{d.id}: {d.region!r} -> {new!r}")
                d.region = new
                total += 1

        # Company.regions_intervention (CSV)
        for c in Company.query.all():
            new, changed = fix_value(c.regions_intervention)
            if changed:
                print(f"  Company#{c.id}: {c.regions_intervention!r} -> {new!r}")
                c.regions_intervention = new
                total += 1

        # Show.region si le modèle a le champ
        if hasattr(Show, 'region'):
            for s in Show.query.all():
                new, changed = fix_value(s.region)
                if changed:
                    print(f"  Show#{s.id}: {s.region!r} -> {new!r}")
                    s.region = new
                    total += 1

        db.session.commit()
        print(f"\n✅ {total} ligne(s) corrigée(s).")


if __name__ == "__main__":
    main()
