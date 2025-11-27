"""
Script pour ajouter la colonne contact_phone à la table shows
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("instance/app.db")

def main():
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(shows)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "contact_phone" in columns:
        print("ℹ️  La colonne 'contact_phone' existe déjà dans la table 'shows'")
        conn.close()
        return
    
    # Ajouter la colonne
    print("🔧 Ajout de la colonne 'contact_phone' à la table 'shows'...")
    try:
        cursor.execute("ALTER TABLE shows ADD COLUMN contact_phone VARCHAR(20)")
        conn.commit()
        print("✅ Colonne ajoutée avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne : {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("\n✨ Migration terminée !")

if __name__ == "__main__":
    main()
