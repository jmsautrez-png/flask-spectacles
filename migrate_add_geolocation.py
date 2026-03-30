#!/usr/bin/env python3
"""
Migration : Ajouter les colonnes de géolocalisation à visitor_log
Colonnes ajoutées : city, region, country, isp
"""

import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def migrate():
    """Ajouter les colonnes de géolocalisation"""
    with app.app_context():
        try:
            # Colonnes à ajouter
            columns_to_add = [
                ("city", "VARCHAR(100)"),
                ("region", "VARCHAR(100)"),
                ("country", "VARCHAR(50)"),
                ("isp", "VARCHAR(150)")
            ]
            
            # Détecter le type de base de données
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            is_postgres = 'postgresql' in db_uri
            
            print("🔍 Vérification et ajout des colonnes de géolocalisation...")
            print(f"   Base de données : {'PostgreSQL' if is_postgres else 'SQLite'}")
            
            for column_name, column_type in columns_to_add:
                try:
                    # Vérifier si la colonne existe déjà
                    if is_postgres:
                        # PostgreSQL : utiliser information_schema
                        result = db.session.execute(
                            text(f"SELECT column_name FROM information_schema.columns WHERE table_name='visitor_log' AND column_name='{column_name}'")
                        ).fetchone()
                    else:
                        # SQLite : utiliser PRAGMA
                        result = db.session.execute(
                            text(f"PRAGMA table_info(visitor_log)")
                        ).fetchall()
                        # Chercher la colonne dans les résultats
                        column_exists = any(row[1] == column_name for row in result)
                        result = column_name if column_exists else None
                    
                    if result:
                        print(f"  ⚪ Colonne '{column_name}' existe déjà")
                    else:
                        # Ajouter la colonne
                        db.session.execute(
                            text(f"ALTER TABLE visitor_log ADD COLUMN {column_name} {column_type}")
                        )
                        db.session.commit()
                        print(f"  ✅ Colonne '{column_name}' ajoutée avec succès")
                        
                except Exception as e:
                    print(f"  ❌ Erreur pour '{column_name}': {e}")
                    db.session.rollback()
            
            print("\n✅ Migration terminée avec succès !")
            print("\nColonnes ajoutées :")
            print("  - city : Ville du visiteur (ex: Paris)")
            print("  - region : Région (ex: Île-de-France)")
            print("  - country : Pays (ex: France)")
            print("  - isp : Fournisseur d'accès (ex: Orange)")
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la migration : {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    migrate()
