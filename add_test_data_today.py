"""
Script pour ajouter des données de test pour aujourd'hui
afin de tester le graphique des statistiques
"""
from datetime import datetime, timedelta
from app import app, db
from models.models import VisitorLog
import random

def add_test_data():
    with app.app_context():
        # Supprimer les anciennes données de test si elles existent
        print("🧹 Nettoyage des anciennes données de test...")
        VisitorLog.query.filter(VisitorLog.session_id.like('test-%')).delete()
        
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        print(f"📅 Création de données de test pour {today_start.date()}")
        
        # Créer des données pour chaque heure de 8h à 18h
        for hour in range(8, 19):
            # Nombre aléatoire de visiteurs par heure (2-8)
            num_visitors = random.randint(2, 8)
            
            for visitor_num in range(num_visitors):
                # Créer plusieurs visites par visiteur (1-3 pages)
                num_pages = random.randint(1, 3)
                session_id = f"test-{today_start.date()}-{hour:02d}-visitor-{visitor_num}"
                
                for page_num in range(num_pages):
                    visit_time = today_start + timedelta(
                        hours=hour,
                        minutes=random.randint(0, 59),
                        seconds=random.randint(0, 59)
                    )
                    
                    pages = [
                        '/',
                        '/spectacles',
                        '/animations',
                        '/contact',
                        '/about',
                        '/spectacles-enfants',
                        '/animations-anniversaire'
                    ]
                    
                    visitor = VisitorLog(
                        session_id=session_id,
                        page_url=random.choice(pages),
                        visited_at=visit_time,
                        ip_anonymized=f"192.168.{random.randint(1,255)}.xxx",
                        user_agent="Mozilla/5.0 (Test Data)",
                        is_bot=False,  # Visiteurs humains uniquement
                        city="Paris",
                        region="Île-de-France",
                        country="France",
                        isp="Test ISP"
                    )
                    db.session.add(visitor)
            
            print(f"  ✓ {hour}h00 : {num_visitors} visiteurs créés")
        
        db.session.commit()
        print(f"\n✅ {db.session.query(VisitorLog).filter(VisitorLog.session_id.like('test-%')).count()} visites de test créées!")
        print(f"🌐 Allez sur http://127.0.0.1:5000/admin/statistiques")

if __name__ == "__main__":
    add_test_data()
