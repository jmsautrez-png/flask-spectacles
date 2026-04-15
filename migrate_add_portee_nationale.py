"""Migration: ajouter la colonne portee_nationale à demande_animation."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db

app = create_app()

with app.app_context():
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    columns = [c["name"] for c in inspector.get_columns("demande_animation")]

    if "portee_nationale" not in columns:
        dialect = db.engine.dialect.name
        if dialect == "postgresql":
            db.session.execute(text(
                "ALTER TABLE demande_animation ADD COLUMN portee_nationale BOOLEAN DEFAULT TRUE"
            ))
        else:
            db.session.execute(text(
                "ALTER TABLE demande_animation ADD COLUMN portee_nationale BOOLEAN DEFAULT 1"
            ))
        db.session.commit()
        print("✓ Colonne portee_nationale ajoutée (default=True = toute la France)")
    else:
        print("⦿ Colonne portee_nationale existe déjà")
