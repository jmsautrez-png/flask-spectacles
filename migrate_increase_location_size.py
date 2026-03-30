"""
Script de migration pour augmenter la taille de la colonne location
de 200 à 500 caractères pour permettre plusieurs villes

SQLite ne supporte pas ALTER COLUMN directement, on doit :
1. Créer une nouvelle table avec la bonne structure
2. Copier les données
3. Supprimer l'ancienne table
4. Renommer la nouvelle table
"""

from app import app
from models import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Vérifier le type de base de données
            engine_name = db.engine.dialect.name
            print(f"📊 Type de base de données détecté : {engine_name}")
            
            if engine_name == 'sqlite':
                # Pour SQLite : recréer la table
                print("🔄 Migration SQLite : recréation de la table...")
                
                # 1. Créer une table temporaire avec la nouvelle structure
                db.session.execute(text("""
                    CREATE TABLE shows_new (
                        id INTEGER PRIMARY KEY,
                        raison_sociale VARCHAR(200),
                        title VARCHAR(150) NOT NULL,
                        description TEXT,
                        region VARCHAR(200),
                        location VARCHAR(500),
                        category VARCHAR(80),
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
                
                # 2. Copier les données
                db.session.execute(text("""
                    INSERT INTO shows_new 
                    SELECT * FROM shows
                """))
                
                # 3. Supprimer l'ancienne table
                db.session.execute(text("DROP TABLE shows"))
                
                # 4. Renommer la nouvelle table
                db.session.execute(text("ALTER TABLE shows_new RENAME TO shows"))
                
            elif engine_name in ['mysql', 'mariadb']:
                # Pour MySQL/MariaDB
                db.session.execute(text("ALTER TABLE shows MODIFY COLUMN location VARCHAR(500)"))
            
            elif engine_name == 'postgresql':
                # Pour PostgreSQL
                db.session.execute(text("ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500)"))
            
            else:
                print(f"⚠️  Type de base de données non supporté : {engine_name}")
                return
            
            db.session.commit()
            print("✅ Migration réussie : colonne 'location' étendue à 500 caractères")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration : {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate()
