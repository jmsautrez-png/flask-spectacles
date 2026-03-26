"""
Migration PostgreSQL : Ajoute la colonne 'is_featured' à la table shows
Exécuter sur Render via : python migrate_add_is_featured_postgres.py
"""
from app import app, db
import os

def migrate():
    with app.app_context():
        try:
            print("🔧 Ajout de la colonne 'is_featured' à la table 'shows' (PostgreSQL)...")
            
            # Pour PostgreSQL, utiliser IF NOT EXISTS
            db.session.execute(db.text("""
                ALTER TABLE shows 
                ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE
            """))
            
            db.session.commit()
            print("✅ Colonne 'is_featured' ajoutée avec succès!")
            
            # Vérification
            result = db.session.execute(db.text("""
                SELECT COUNT(*) as total_featured 
                FROM shows 
                WHERE is_featured = TRUE
            """))
            count = result.scalar()
            
            print(f"ℹ️  Nombre de spectacles actuellement 'à la une' : {count}")
            print("ℹ️  L'admin peut cocher 'À la une' dans l'interface d'édition pour marquer des spectacles.")
            
        except Exception as e:
            db.session.rollback()
            error_str = str(e).lower()
            if "already exists" in error_str or "duplicate column" in error_str:
                print("ℹ️  La colonne 'is_featured' existe déjà.")
            else:
                print(f"❌ Erreur lors de la migration : {e}")
                raise

if __name__ == "__main__":
    migrate()
