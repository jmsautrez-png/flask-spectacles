"""
Script de migration complet pour appliquer toutes les modifications de schéma
Ce script est sûr et peut être exécuté plusieurs fois - il détecte automatiquement
ce qui a déjà été migré.
"""

import sys
from app import app, db
from sqlalchemy import text, inspect

def column_exists(table_name, column_name):
    """Vérifie si une colonne existe dans une table"""
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification de la colonne {column_name}: {e}")
        return False

def get_column_type(table_name, column_name):
    """Récupère le type d'une colonne"""
    try:
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)
        for col in columns:
            if col['name'] == column_name:
                return str(col['type'])
        return None
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération du type: {e}")
        return None

def migrate_is_private():
    """Ajoute la colonne is_private à demande_animation"""
    if column_exists('demande_animation', 'is_private'):
        print("  ✓ Colonne is_private existe déjà")
        return True
    
    try:
        engine_name = db.engine.dialect.name
        if engine_name == 'sqlite':
            db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT 0'))
        elif engine_name in ['postgresql', 'postgres']:
            db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT FALSE'))
        elif engine_name in ['mysql', 'mariadb']:
            db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT 0'))
        else:
            print(f"  ⚠️ Type de base de données non supporté : {engine_name}")
            return False
        
        db.session.commit()
        print("  ✅ Colonne is_private ajoutée")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"  ❌ Erreur lors de l'ajout de is_private: {e}")
        return False

def migrate_location_size():
    """Augmente la taille de la colonne location à 500 caractères"""
    col_type = get_column_type('shows', 'location')
    if col_type and '500' in col_type:
        print("  ✓ Colonne location déjà à 500 caractères")
        return True
    
    try:
        engine_name = db.engine.dialect.name
        
        if engine_name == 'sqlite':
            # SQLite nécessite une recréation de table
            print("  🔄 SQLite : recréation de la table shows pour location...")
            db.session.execute(text("""
                CREATE TABLE shows_temp (
                    id INTEGER PRIMARY KEY,
                    raison_sociale VARCHAR(200),
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    region VARCHAR(200),
                    location VARCHAR(500),
                    category VARCHAR(500),
                    date DATE,
                    age_range VARCHAR(50),
                    file_name VARCHAR(255),
                    file_mimetype VARCHAR(120),
                    created_at DATETIME,
                    approved BOOLEAN,
                    contact_email VARCHAR(255),
                    contact_phone VARCHAR(20),
                    site_internet VARCHAR(255),
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            db.session.execute(text("INSERT INTO shows_temp SELECT * FROM shows"))
            db.session.execute(text("DROP TABLE shows"))
            db.session.execute(text("ALTER TABLE shows_temp RENAME TO shows"))
            
        elif engine_name in ['mysql', 'mariadb']:
            db.session.execute(text("ALTER TABLE shows MODIFY COLUMN location VARCHAR(500)"))
            db.session.execute(text("ALTER TABLE shows MODIFY COLUMN category VARCHAR(500)"))
        
        elif engine_name in ['postgresql', 'postgres']:
            db.session.execute(text("ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500)"))
            db.session.execute(text("ALTER TABLE shows ALTER COLUMN category TYPE VARCHAR(500)"))
        
        else:
            print(f"  ⚠️ Type de base de données non supporté : {engine_name}")
            return False
        
        db.session.commit()
        print("  ✅ Colonnes location et category étendues à 500 caractères")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"  ❌ Erreur lors de l'extension de location/category: {e}")
        return False

def main():
    with app.app_context():
        engine_name = db.engine.dialect.name
        print(f"\n📊 Base de données : {engine_name}")
        print(f"📊 URL : {db.engine.url}\n")
        
        print("🔄 Migration 1/2 : Ajout colonne is_private")
        success1 = migrate_is_private()
        
        print("\n🔄 Migration 2/2 : Extension location et category à 500 caractères")
        success2 = migrate_location_size()
        
        print("\n" + "="*60)
        if success1 and success2:
            print("✅ Toutes les migrations ont été appliquées avec succès !")
            return 0
        else:
            print("⚠️ Certaines migrations ont échoué. Vérifiez les messages ci-dessus.")
            return 1

if __name__ == "__main__":
    sys.exit(main())
