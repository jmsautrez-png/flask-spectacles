#!/usr/bin/env python3
"""
Script de migration pour ajouter la colonne site_internet à users en production.
À exécuter dans le Shell Render avec : python migrate_production_postgres.py
"""
import os
import sys

def migrate():
    # Récupérer l'URL de la base de données depuis les variables d'environnement
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL n'est pas défini")
        sys.exit(1)
    
    # Adapter l'URL pour SQLAlchemy (postgres:// -> postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"🔗 Connexion à la base de données...")
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Vérifier si la colonne existe déjà
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'site_internet'
            """))
            
            if result.fetchone():
                print("✓ La colonne site_internet existe déjà dans la table users")
            else:
                print("📝 Ajout de la colonne site_internet...")
                conn.execute(text("""
                    ALTER TABLE users ADD COLUMN site_internet VARCHAR(255)
                """))
                conn.commit()
                print("✓ Colonne site_internet ajoutée avec succès!")
            
            # Vérification finale
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'site_internet'
            """))
            
            row = result.fetchone()
            if row:
                print(f"✓ Vérification OK: {row[0]} - {row[1]}({row[2]})")
            else:
                print("❌ ERREUR: La colonne n'a pas été créée")
                
    except Exception as e:
        print(f"❌ ERREUR lors de la migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
