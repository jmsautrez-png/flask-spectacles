#!/usr/bin/env python3
"""
Ajoute la colonne 'site_internet' à la table 'shows' si elle n'existe pas.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "app.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(shows)")
    columns = [col[1] for col in cursor.fetchall()]
    if "site_internet" not in columns:
        cursor.execute("ALTER TABLE shows ADD COLUMN site_internet VARCHAR(255)")
        conn.commit()
        print("Colonne 'site_internet' ajoutée !")
    else:
        print("La colonne 'site_internet' existe déjà.")
    conn.close()

if __name__ == "__main__":
    migrate()
