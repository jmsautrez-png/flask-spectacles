"""Script de migration pour ajouter la colonne is_private à DemandeAnimation"""
import sys
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Ajouter la colonne is_private (compatible SQLAlchemy 2.x)
        db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT 0'))
        db.session.commit()
        print("✅ Colonne is_private ajoutée avec succès !")
    except Exception as e:
        db.session.rollback()
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("⚠️ La colonne is_private existe déjà.")
        else:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
