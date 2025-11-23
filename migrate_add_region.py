#!/usr/bin/env python3
"""
Script de migration pour ajouter la colonne 'region' à la table 'shows'.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "database.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(shows)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "region" in columns:
        print("✓ La colonne 'region' existe déjà.")
    else:
        print("Ajout de la colonne 'region'...")
        cursor.execute("ALTER TABLE shows ADD COLUMN region VARCHAR(100)")
        conn.commit()
        print("✓ Colonne 'region' ajoutée avec succès.")
    
    conn.close()

if __name__ == "__main__":
    migrate()
