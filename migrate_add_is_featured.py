"""
Migration : Ajoute la colonne 'is_featured' à la table shows
Pour contrôler quels spectacles apparaissent "à la une" sur la page d'accueil
"""
from app import app, db

def migrate():
    with app.app_context():
        try:
            print("🔧 Ajout de la colonne 'is_featured' à la table 'shows'...")
            
            # Ajouter la colonne is_featured (par défaut False)
            db.session.execute(db.text("""
                ALTER TABLE shows 
                ADD COLUMN is_featured BOOLEAN DEFAULT FALSE
            """))
            
            db.session.commit()
            print("✅ Colonne 'is_featured' ajoutée avec succès!")
            print("ℹ️  Par défaut, aucun spectacle n'est 'à la une'.")
            print("ℹ️  L'admin peut maintenant cocher 'À la une' pour les spectacles à mettre en avant.")
            
        except Exception as e:
            db.session.rollback()
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  La colonne 'is_featured' existe déjà.")
            else:
                print(f"❌ Erreur lors de la migration : {e}")
                raise

if __name__ == "__main__":
    migrate()
