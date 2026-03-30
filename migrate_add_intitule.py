#!/usr/bin/env python3
"""
Script de migration pour ajouter la colonne 'intitule' à la table demande_animation.
"""
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Base de données non trouvée: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='demande_animation'")
    if not cursor.fetchone():
        print("La table 'demande_animation' n'existe pas encore. Elle sera créée au premier lancement de l'application.")
        conn.close()
        return
    
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(demande_animation)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'intitule' in columns:
        print("La colonne 'intitule' existe déjà dans la table demande_animation.")
    else:
        cursor.execute("ALTER TABLE demande_animation ADD COLUMN intitule TEXT")
        conn.commit()
        print("Colonne 'intitule' ajoutée avec succès à la table demande_animation.")
    
    conn.close()

if __name__ == "__main__":
    migrate()
