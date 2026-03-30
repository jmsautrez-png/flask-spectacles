"""
Migration : Ajouter les colonnes file_name2, file_mimetype2, file_name3, file_mimetype3 à la table shows.
Ces colonnes permettent aux utilisateurs d'uploader jusqu'à 3 photos qui s'afficheront en diaporama.
"""

from app import create_app, db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        
        # Liste des colonnes à ajouter
        columns_to_add = [
            ("file_name2", "VARCHAR(255)"),
            ("file_mimetype2", "VARCHAR(120)"),
            ("file_name3", "VARCHAR(255)"),
            ("file_mimetype3", "VARCHAR(120)"),
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                # Vérifier si la colonne existe déjà
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'shows' AND column_name = :col_name"
                ), {"col_name": col_name})
                
                if result.fetchone() is None:
                    # La colonne n'existe pas, on l'ajoute
                    conn.execute(text(f"ALTER TABLE shows ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✅ Colonne '{col_name}' ajoutée avec succès.")
                else:
                    print(f"ℹ️  Colonne '{col_name}' existe déjà.")
                    
            except Exception as e:
                # Pour SQLite, la syntaxe est différente
                try:
                    conn.execute(text(f"ALTER TABLE shows ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✅ Colonne '{col_name}' ajoutée avec succès (SQLite).")
                except Exception as e2:
                    if "duplicate column" in str(e2).lower() or "already exists" in str(e2).lower():
                        print(f"ℹ️  Colonne '{col_name}' existe déjà.")
                    else:
                        print(f"❌ Erreur pour '{col_name}': {e2}")
        
        conn.close()
        print("\n🎉 Migration terminée !")
        print("Les utilisateurs peuvent maintenant uploader jusqu'à 3 photos par annonce.")


if __name__ == "__main__":
    migrate()
