"""
Vérification des données de visite disponibles
Pour comprendre ce qui reste avant agrégation
"""
from app import app, db
from models.models import VisitorLog
from sqlalchemy import func
from datetime import datetime, timedelta

with app.app_context():
    print("=" * 70)
    print("📊 ANALYSE DES DONNÉES VISITOR_LOG")
    print("=" * 70)
    
    # Total d'enregistrements
    total = VisitorLog.query.count()
    print(f"Total enregistrements : {total}")
    
    if total == 0:
        print("❌ AUCUNE DONNÉE ! Les visites ont été supprimées.")
        print("=" * 70)
        exit()
    
    # Date la plus ancienne et la plus récente
    oldest = db.session.query(func.min(VisitorLog.visited_at)).scalar()
    newest = db.session.query(func.max(VisitorLog.visited_at)).scalar()
    
    print(f"Plus ancienne visite : {oldest}")
    print(f"Plus récente visite : {newest}")
    
    if oldest and newest:
        days_range = (newest.date() - oldest.date()).days + 1
        print(f"Période couverte : {days_range} jour(s)")
    
    print()
    print("📅 Répartition par jour :")
    print("-" * 70)
    
    # Stats par jour
    daily_counts = db.session.query(
        func.date(VisitorLog.visited_at).label('date'),
        func.count(VisitorLog.id).label('visits'),
        func.count(func.distinct(VisitorLog.session_id)).label('sessions')
    ).group_by(func.date(VisitorLog.visited_at)).\
      order_by('date').all()
    
    for date, visits, sessions in daily_counts:
        print(f"{date} : {sessions:3d} visiteurs | {visits:4d} pages vues")
    
    print("=" * 70)
    print(f"✅ {len(daily_counts)} jour(s) de données à sauvegarder")
    print("=" * 70)
