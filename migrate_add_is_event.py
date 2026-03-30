#!/usr/bin/env python3
"""
Migration : Ajoute la colonne is_event à la table shows
pour distinguer les spectacles du catalogue des événements annoncés.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "app.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(shows)")
    columns = [col[1] for col in cursor.fetchall()]

    if "is_event" in columns:
        print("✅ La colonne 'is_event' existe déjà.")
    else:
        cursor.execute("ALTER TABLE shows ADD COLUMN is_event BOOLEAN DEFAULT 0")
        conn.commit()
        print("✅ Colonne 'is_event' ajoutée avec succès.")

    conn.close()

if __name__ == "__main__":
    migrate()
