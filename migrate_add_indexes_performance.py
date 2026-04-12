"""
Migration : Ajoute les index de performance manquants.
Colonnes indexées :
  - shows.approved, shows.is_featured, shows.category, shows.location
  - demande_animation.is_private, demande_animation.approved
Usage : python migrate_add_indexes_performance.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db

app = create_app()

INDEXES = [
    ("idx_shows_approved", "shows", "approved"),
    ("idx_shows_is_featured", "shows", "is_featured"),
    ("idx_shows_category", "shows", "category"),
    ("idx_shows_location", "shows", "location"),
    ("idx_demande_animation_is_private", "demande_animation", "is_private"),
    ("idx_demande_animation_approved", "demande_animation", "approved"),
]

with app.app_context():
    for idx_name, table, column in INDEXES:
        try:
            db.session.execute(
                db.text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column})")
            )
            print(f"✓ Index {idx_name} créé sur {table}.{column}")
        except Exception as e:
            print(f"⚠ Index {idx_name} : {e}")
            db.session.rollback()
    db.session.commit()
    print("\n✅ Migration terminée.")
