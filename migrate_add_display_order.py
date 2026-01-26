"""
Migration: Ajouter la colonne display_order à la table shows
Pour permettre à l'admin de réorganiser l'ordre d'affichage des cartes.
"""

from app import create_app
from models import db

app = create_app()

with app.app_context():
    try:
        # Vérifier si la colonne existe déjà
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('shows')]
        
        if 'display_order' not in columns:
            db.session.execute(db.text(
                "ALTER TABLE shows ADD COLUMN display_order INTEGER DEFAULT 0"
            ))
            db.session.commit()
            print("✅ Colonne 'display_order' ajoutée avec succès à la table 'shows'.")
        else:
            print("ℹ️ La colonne 'display_order' existe déjà.")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de la migration: {e}")
