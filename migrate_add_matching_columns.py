"""
Migration : Ajout des colonnes de matching (3 axes + régions)
- Show : specialites, evenements, lieux_intervention, regions_intervention
- DemandeAnimation : specialites_recherchees, evenements_contexte, lieux_souhaites

Compatible SQLite (local) et PostgreSQL (production Render).
"""
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app

app = create_app()

COLUMNS_SHOW = [
    ("shows", "specialites", "TEXT"),
    ("shows", "evenements", "TEXT"),
    ("shows", "lieux_intervention", "TEXT"),
    ("shows", "regions_intervention", "TEXT"),
]

COLUMNS_DEMANDE = [
    ("demande_animation", "specialites_recherchees", "TEXT"),
    ("demande_animation", "evenements_contexte", "TEXT"),
    ("demande_animation", "lieux_souhaites", "TEXT"),
]


def column_exists(conn, table, column):
    """Vérifie si une colonne existe déjà (SQLite + PostgreSQL)."""
    db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if "postgresql" in db_url or "postgres" in db_url:
        result = conn.execute(
            __import__("sqlalchemy").text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = :col"
            ),
            {"table": table, "col": column},
        )
        return result.fetchone() is not None
    else:
        result = conn.execute(__import__("sqlalchemy").text(f"PRAGMA table_info({table})"))
        columns = [row[1] for row in result.fetchall()]
        return column in columns


def migrate():
    with app.app_context():
        from models import db

        with db.engine.connect() as conn:
            all_columns = COLUMNS_SHOW + COLUMNS_DEMANDE
            added = 0

            for table, col, col_type in all_columns:
                if column_exists(conn, table, col):
                    print(f"  ✓ {table}.{col} existe déjà")
                else:
                    conn.execute(
                        __import__("sqlalchemy").text(
                            f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                        )
                    )
                    conn.commit()
                    print(f"  ✚ {table}.{col} ajouté")
                    added += 1

            if added:
                print(f"\n✅ Migration terminée : {added} colonne(s) ajoutée(s)")
            else:
                print("\n✅ Rien à migrer, toutes les colonnes existent déjà")


if __name__ == "__main__":
    migrate()
