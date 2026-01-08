"""Script de migration pour ajouter la colonne is_private à DemandeAnimation"""
import sys
from app import app, db
from sqlalchemy import text, inspect

def column_exists(table_name, column_name):
    """Vérifie si une colonne existe dans une table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

with app.app_context():
    try:
        # Vérifier si la colonne existe déjà
        if column_exists('demande_animation', 'is_private'):
            print("⚠️ La colonne is_private existe déjà.")
            sys.exit(0)
        
        engine_name = db.engine.dialect.name
        print(f"📊 Type de base de données détecté : {engine_name}")
        
        # Ajouter la colonne is_private selon le type de base de données
        if engine_name == 'sqlite':
            db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT 0'))
        elif engine_name in ['postgresql', 'postgres']:
            # PostgreSQL : utiliser FALSE au lieu de 0
            db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT FALSE'))
        elif engine_name in ['mysql', 'mariadb']:
            # MySQL/MariaDB
            db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT 0'))
        else:
            print(f"⚠️ Type de base de données non supporté : {engine_name}")
            sys.exit(1)
        
        db.session.commit()
        print("✅ Colonne is_private ajoutée avec succès !")
        
    except Exception as e:
        db.session.rollback()
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("⚠️ La colonne is_private existe déjà.")
        else:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
