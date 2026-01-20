"""
Migration: Ajouter la colonne 'region' à la table 'users'
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "app.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données non trouvée: {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "region" in columns:
        print("✅ La colonne 'region' existe déjà dans la table 'users'")
        conn.close()
        return True

    # Ajouter la colonne
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN region VARCHAR(200)")
        conn.commit()
        print("✅ Colonne 'region' ajoutée avec succès à la table 'users'")
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
        conn.close()
        return False

    conn.close()
    return True

if __name__ == "__main__":
    migrate()
