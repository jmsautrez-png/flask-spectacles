import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("instance/app.db")

def check_and_add_created_at():
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(shows)")
    columns = [row[1] for row in cursor.fetchall()]
    if "created_at" in columns:
        print("✅ La colonne 'created_at' existe déjà dans la table 'shows'.")
    else:
        print("➕ Ajout de la colonne 'created_at'...")
        cursor.execute("ALTER TABLE shows ADD COLUMN created_at TEXT")
        conn.commit()
        print("✅ Colonne 'created_at' ajoutée.")
    conn.close()

if __name__ == "__main__":
    check_and_add_created_at()
