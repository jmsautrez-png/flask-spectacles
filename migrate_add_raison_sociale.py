"""
Script de migration pour ajouter la colonne raison_sociale à la table users
ATTENTION : Ce script modifie la base de données. Faites une sauvegarde avant !
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB_PATH = Path("instance/app.db")
BACKUP_DIR = Path("instance/backups")

def main():
    # 1) Vérifier que la base existe
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return
    
    # 2) Créer une sauvegarde
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"app_backup_{timestamp}.db"
    
    print(f"📦 Création d'une sauvegarde : {backup_path}")
    shutil.copy2(DB_PATH, backup_path)
    print("✅ Sauvegarde créée avec succès")
    
    # 3) Ajouter la colonne
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "raison_sociale" in columns:
        print("ℹ️  La colonne 'raison_sociale' existe déjà dans la table 'users'")
        conn.close()
        return
    
    # Ajouter la colonne
    print("🔧 Ajout de la colonne 'raison_sociale' à la table 'users'...")
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN raison_sociale VARCHAR(200)")
        conn.commit()
        print("✅ Colonne ajoutée avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne : {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print(f"\n✨ Migration terminée !")
    print(f"💾 Sauvegarde disponible dans : {backup_path}")

if __name__ == "__main__":
    main()
