"""
Création de la table DailyStats pour conserver les statistiques par jour
Permet des analyses à long terme sans conserver toutes les données brutes
"""
from app import app, db
from sqlalchemy import text

def create_daily_stats_table():
    with app.app_context():
        # Détecter le type de base de données
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        is_postgres = 'postgresql' in db_uri
        
        print("=" * 70)
        print("📊 CRÉATION TABLE DAILY_STATS")
        print("=" * 70)
        print(f"Base de données: {'PostgreSQL' if is_postgres else 'SQLite'}")
        
        # Créer la table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS daily_stats (
            id SERIAL PRIMARY KEY,
            stat_date DATE NOT NULL UNIQUE,
            total_visitors INTEGER DEFAULT 0,
            total_page_views INTEGER DEFAULT 0,
            unique_sessions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """ if is_postgres else """
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date DATE NOT NULL UNIQUE,
            total_visitors INTEGER DEFAULT 0,
            total_page_views INTEGER DEFAULT 0,
            unique_sessions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        db.session.execute(text(create_table_sql))
        db.session.commit()
        print("✅ Table daily_stats créée")
        
        # Créer un index sur stat_date pour les requêtes rapides
        if is_postgres:
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(stat_date);"))
        else:
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(stat_date);"))
        db.session.commit()
        print("✅ Index créé sur stat_date")
        
        print("=" * 70)
        print("✅ Migration terminée avec succès !")
        print("=" * 70)

if __name__ == "__main__":
    create_daily_stats_table()
