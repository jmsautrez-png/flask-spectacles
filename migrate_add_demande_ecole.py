#!/usr/bin/env python3
"""
Migration pour créer la table demande_ecole
pour les demandes thématiques des écoles maternelles et primaires
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "shows.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la table existe déjà
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='demande_ecole'")
    if cursor.fetchone():
        print("✅ La table 'demande_ecole' existe déjà.")
        conn.close()
        return
    
    # Créer la table demande_ecole
    cursor.execute("""
        CREATE TABLE demande_ecole (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auto_datetime VARCHAR(50),
            
            -- Informations sur l'école
            nom_ecole VARCHAR(200) NOT NULL,
            type_etablissement VARCHAR(50) NOT NULL,
            adresse VARCHAR(300),
            code_postal VARCHAR(10) NOT NULL,
            ville VARCHAR(100) NOT NULL,
            region VARCHAR(100),
            
            -- Contact
            nom_contact VARCHAR(150) NOT NULL,
            fonction_contact VARCHAR(100),
            email VARCHAR(255) NOT NULL,
            telephone VARCHAR(50) NOT NULL,
            
            -- Informations sur les classes
            nombre_classes VARCHAR(20),
            nombre_eleves VARCHAR(20),
            niveaux_concernes VARCHAR(200),
            
            -- Thème pédagogique
            theme_principal VARCHAR(100) NOT NULL,
            sous_themes TEXT,
            objectifs_pedagogiques TEXT NOT NULL,
            
            -- Type d'animation souhaitée
            types_animation VARCHAR(500),
            
            -- Contraintes techniques
            salle_disponible VARCHAR(100),
            surface_approximative VARCHAR(50),
            acces_electricite BOOLEAN DEFAULT 1,
            
            -- Période et budget
            periode_souhaitee VARCHAR(100),
            date_precise VARCHAR(100),
            budget VARCHAR(50),
            
            -- Informations complémentaires
            informations_complementaires TEXT,
            
            -- Statut
            statut VARCHAR(50) DEFAULT 'nouvelle',
            notes_admin TEXT,
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    print("✅ Table 'demande_ecole' créée avec succès!")
    conn.close()

if __name__ == "__main__":
    migrate()
