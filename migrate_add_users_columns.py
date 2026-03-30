"""
Script de migration pour ajouter les colonnes email et created_at à la table users
"""

import sys
from app import app, db
from sqlalchemy import text, inspect
from datetime import datetime

def column_exists(table_name, column_name):
    """Vérifie si une colonne existe dans une table"""
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification de la colonne {column_name}: {e}")
        return False

def migrate_users_columns():
    """Ajoute les colonnes email et created_at à la table users"""
    with app.app_context():
        try:
            engine_name = db.engine.dialect.name
            print(f"\n📊 Type de base de données détecté : {engine_name}")
            
            # Migration 1: Colonne email
            print("\n1️⃣ Vérification colonne email...")
            if column_exists('users', 'email'):
                print("   ✓ Colonne email existe déjà")
            else:
                print("   ➜ Ajout de la colonne email...")
                if engine_name in ['postgresql', 'postgres']:
                    db.session.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(255)'))
                elif engine_name in ['mysql', 'mariadb']:
                    db.session.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(255)'))
                elif engine_name == 'sqlite':
                    db.session.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(255)'))
                db.session.commit()
                print("   ✅ Colonne email ajoutée")
            
            # Migration 2: Colonne created_at
            print("\n2️⃣ Vérification colonne created_at...")
            if column_exists('users', 'created_at'):
                print("   ✓ Colonne created_at existe déjà")
            else:
                print("   ➜ Ajout de la colonne created_at...")
                if engine_name in ['postgresql', 'postgres']:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                elif engine_name in ['mysql', 'mariadb']:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                elif engine_name == 'sqlite':
                    db.session.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                db.session.commit()
                print("   ✅ Colonne created_at ajoutée")
            
            print("\n" + "="*60)
            print("✅ Migration des colonnes users terminée avec succès !")
            print("="*60 + "\n")
            return 0
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la migration : {e}")
            db.session.rollback()
            return 1

if __name__ == "__main__":
    sys.exit(migrate_users_columns())
