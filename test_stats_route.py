"""Test de la route des statistiques pour voir les erreurs"""
from app import app, db
from models.models import VisitorLog
from datetime import datetime, timedelta
from sqlalchemy import func, text

with app.app_context():
    print("🔍 Test de la requête SQL pour les statistiques")
    
    # Période = aujourd'hui
    date_limit = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Vérifier le type de base de données
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    is_postgres = 'postgresql' in db_uri
    
    print(f"📊 Base de données: {'PostgreSQL' if is_postgres else 'SQLite'}")
    print(f"🗄️  URI: {db_uri[:50]}...")
    
    try:
        if is_postgres:
            print("\n❌ Test avec PostgreSQL (DATE_TRUNC)...")
            visitors_by_day = db.session.query(
                func.date_trunc('hour', VisitorLog.visited_at).label('date'),
                func.count(func.distinct(VisitorLog.session_id)).label('visitors')
            ).filter(
                VisitorLog.visited_at >= date_limit,
                VisitorLog.is_bot == False
            ).group_by(func.date_trunc('hour', VisitorLog.visited_at)).\
                order_by(func.date_trunc('hour', VisitorLog.visited_at)).all()
        else:
            print("\n✅ Test avec SQLite (strftime)...")
            visitors_by_day = db.session.query(
                func.strftime('%Y-%m-%d %H:00:00', VisitorLog.visited_at).label('date'),
                func.count(func.distinct(VisitorLog.session_id)).label('visitors')
            ).filter(
                VisitorLog.visited_at >= date_limit,
                VisitorLog.is_bot == False
            ).group_by(func.strftime('%Y-%m-%d %H:00:00', VisitorLog.visited_at)).\
                order_by(func.strftime('%Y-%m-%d %H:00:00', VisitorLog.visited_at)).all()
        
        print(f"\n✅ Requête réussie! {len(visitors_by_day)} heures trouvées")
        for row in visitors_by_day[:5]:  # Afficher les 5 premières
            print(f"   {row.date}: {row.visitors} visiteurs")
            
    except Exception as e:
        print(f"\n❌ ERREUR: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        print("\n📋 Traceback:")
        traceback.print_exc()
