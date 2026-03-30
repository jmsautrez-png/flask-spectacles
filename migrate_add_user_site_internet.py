#!/usr/bin/env python3
"""
Ajoute la colonne 'site_internet' à la table 'users' si elle n'existe pas.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "app.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "site_internet" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN site_internet VARCHAR(255)")
        conn.commit()
        print("✓ Colonne 'site_internet' ajoutée à la table users !")
    else:
        print("✓ La colonne 'site_internet' existe déjà dans users.")
    conn.close()

if __name__ == "__main__":
    migrate()
