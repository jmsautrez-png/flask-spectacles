#!/usr/bin/env python
"""
Script de migration pour ajouter les colonnes code_postal et region
à la table demande_animation.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "spectacles.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Base de données introuvable : {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si la table demande_animation existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='demande_animation'")
    table_exists = cursor.fetchone()

    if not table_exists:
        print("La table 'demande_animation' n'existe pas, création...")
        cursor.execute("""
            CREATE TABLE demande_animation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auto_datetime VARCHAR(50),
                structure VARCHAR(200) NOT NULL,
                telephone VARCHAR(50) NOT NULL,
                lieu_ville VARCHAR(200) NOT NULL,
                nom VARCHAR(150) NOT NULL,
                dates_horaires VARCHAR(200) NOT NULL,
                type_espace VARCHAR(100) NOT NULL,
                genre_recherche VARCHAR(100) NOT NULL,
                age_range VARCHAR(50) NOT NULL,
                jauge VARCHAR(50) NOT NULL,
                budget VARCHAR(100) NOT NULL,
                contraintes TEXT,
                accessibilite VARCHAR(100),
                contact_email VARCHAR(255) NOT NULL,
                intitule VARCHAR(1000),
                code_postal VARCHAR(10),
                region VARCHAR(100),
                is_private BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✓ Table 'demande_animation' créée avec succès !")
        conn.close()
        return

    # Vérifier si les colonnes existent déjà
    cursor.execute("PRAGMA table_info(demande_animation)")
    columns = [col[1] for col in cursor.fetchall()]

    # Ajouter code_postal si elle n'existe pas
    if "code_postal" not in columns:
        print("Ajout de la colonne 'code_postal' à la table demande_animation...")
        cursor.execute("ALTER TABLE demande_animation ADD COLUMN code_postal VARCHAR(10)")
        print("✓ Colonne 'code_postal' ajoutée avec succès.")
    else:
        print("La colonne 'code_postal' existe déjà.")

    # Ajouter region si elle n'existe pas
    if "region" not in columns:
        print("Ajout de la colonne 'region' à la table demande_animation...")
        cursor.execute("ALTER TABLE demande_animation ADD COLUMN region VARCHAR(100)")
        print("✓ Colonne 'region' ajoutée avec succès.")
    else:
        print("La colonne 'region' existe déjà.")

    conn.commit()
    conn.close()
    print("\nMigration terminée avec succès !")

if __name__ == "__main__":
    migrate()
