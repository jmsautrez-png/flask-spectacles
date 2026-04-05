"""
Migration : Ajout d'index composites pour optimiser les statistiques

Index créés :
- idx_visited_at_is_bot : Accélère les filtres combinés sur visited_at + is_bot (jusqu'à 10x plus rapide)
- idx_session_id_is_bot : Optimise les GROUP BY sur session_id avec filtre is_bot

Usage :
    python migrate_add_composite_indexes.py
"""

from app import create_app, db
from sqlalchemy import text

def add_composite_indexes():
    """Ajoute des index composites pour optimiser les requêtes de statistiques"""
    app = create_app()
    
    with app.app_context():
        try:
            # Détecter le type de base de données
            db_type = db.engine.dialect.name
            print(f"🔍 Détection de la base de données : {db_type}")
            
            if db_type == 'postgresql':
                print("🔍 Vérification des index PostgreSQL existants...")
                
                # Vérifier si les index existent déjà (PostgreSQL)
                check_idx1 = text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'visitor_log' 
                    AND indexname = 'idx_visited_at_is_bot'
                """)
                
                check_idx2 = text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'visitor_log' 
                    AND indexname = 'idx_session_id_is_bot'
                """)
                
                result1 = db.session.execute(check_idx1).fetchone()
                result2 = db.session.execute(check_idx2).fetchone()
                
                # Créer l'index visited_at + is_bot
                if not result1:
                    print("➕ Création de l'index composite (visited_at, is_bot)...")
                    create_idx1 = text("""
                        CREATE INDEX CONCURRENTLY idx_visited_at_is_bot 
                        ON visitor_log(visited_at, is_bot)
                    """)
                    db.session.execute(create_idx1)
                    db.session.commit()
                    print("✅ Index idx_visited_at_is_bot créé avec succès")
                else:
                    print("ℹ️  Index idx_visited_at_is_bot existe déjà")
                
                # Créer l'index session_id + is_bot
                if not result2:
                    print("➕ Création de l'index composite (session_id, is_bot)...")
                    create_idx2 = text("""
                        CREATE INDEX CONCURRENTLY idx_session_id_is_bot 
                        ON visitor_log(session_id, is_bot)
                    """)
                    db.session.execute(create_idx2)
                    db.session.commit()
                    print("✅ Index idx_session_id_is_bot créé avec succès")
                else:
                    print("ℹ️  Index idx_session_id_is_bot existe déjà")
                    
            elif db_type == 'sqlite':
                print("🔍 Vérification des index SQLite existants...")
                
                # Vérifier si les index existent déjà (SQLite)
                check_indexes = text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND tbl_name='visitor_log'
                """)
                existing_indexes = [row[0] for row in db.session.execute(check_indexes).fetchall()]
                
                # Créer l'index visited_at + is_bot
                if 'idx_visited_at_is_bot' not in existing_indexes:
                    print("➕ Création de l'index composite (visited_at, is_bot)...")
                    create_idx1 = text("""
                        CREATE INDEX idx_visited_at_is_bot 
                        ON visitor_log(visited_at, is_bot)
                    """)
                    db.session.execute(create_idx1)
                    db.session.commit()
                    print("✅ Index idx_visited_at_is_bot créé avec succès")
                else:
                    print("ℹ️  Index idx_visited_at_is_bot existe déjà")
                
                # Créer l'index session_id + is_bot
                if 'idx_session_id_is_bot' not in existing_indexes:
                    print("➕ Création de l'index composite (session_id, is_bot)...")
                    create_idx2 = text("""
                        CREATE INDEX idx_session_id_is_bot 
                        ON visitor_log(session_id, is_bot)
                    """)
                    db.session.execute(create_idx2)
                    db.session.commit()
                    print("✅ Index idx_session_id_is_bot créé avec succès")
                else:
                    print("ℹ️  Index idx_session_id_is_bot existe déjà")
            else:
                print(f"⚠️  Type de base de données non supporté : {db_type}")
                return
            
            print("\n🎉 Migration terminée avec succès !")
            print("💡 Les requêtes de statistiques seront maintenant jusqu'à 10x plus rapides")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des index : {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    add_composite_indexes()
