"""
Script d'agrégation des statistiques quotidiennes
Calcule et stocke les stats de la veille dans daily_stats

À exécuter quotidiennement (via cron ou Render cron job) : tous les jours à 00:30
"""
from app import app, db
from models.models import VisitorLog
from sqlalchemy import text, func
from datetime import datetime, timedelta
import sys

def aggregate_yesterday_stats():
    """Agrège les statistiques de la veille"""
    with app.app_context():
        # Calculer la date d'hier
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        
        print("=" * 70)
        print(f"📊 AGRÉGATION STATISTIQUES DU {yesterday.strftime('%d/%m/%Y')}")
        print("=" * 70)
        
        # Vérifier si déjà agrégé
        existing = db.session.execute(
            text("SELECT COUNT(*) as cnt FROM daily_stats WHERE stat_date = :date"),
            {"date": yesterday}
        ).fetchone()
        
        if existing and existing[0] > 0:
            print(f"⚠️  Statistiques du {yesterday} déjà agrégées.")
            
            # Proposer de forcer la mise à jour
            if "--force" in sys.argv:
                print("🔄 Option --force activée : Mise à jour forcée...")
                db.session.execute(
                    text("DELETE FROM daily_stats WHERE stat_date = :date"),
                    {"date": yesterday}
                )
                db.session.commit()
            else:
                print("💡 Utilisez --force pour forcer la mise à jour")
                return
        
        # Calculer les statistiques de la veille
        start_of_day = datetime.combine(yesterday, datetime.min.time())
        end_of_day = datetime.combine(yesterday, datetime.max.time())
        
        # Total de pages vues
        total_page_views = db.session.query(func.count(VisitorLog.id)).filter(
            VisitorLog.visited_at >= start_of_day,
            VisitorLog.visited_at <= end_of_day
        ).scalar() or 0
        
        # Nombre de sessions uniques (visiteurs uniques)
        unique_sessions = db.session.query(func.count(func.distinct(VisitorLog.session_id))).filter(
            VisitorLog.visited_at >= start_of_day,
            VisitorLog.visited_at <= end_of_day
        ).scalar() or 0
        
        # Insérer dans daily_stats
        if total_page_views > 0:
            db.session.execute(
                text("""
                    INSERT INTO daily_stats (stat_date, total_visitors, total_page_views, unique_sessions)
                    VALUES (:date, :visitors, :page_views, :sessions)
                    ON CONFLICT (stat_date) DO UPDATE SET
                        total_visitors = :visitors,
                        total_page_views = :page_views,
                        unique_sessions = :sessions
                """),
                {
                    "date": yesterday,
                    "visitors": unique_sessions,
                    "page_views": total_page_views,
                    "sessions": unique_sessions
                }
            )
            db.session.commit()
            
            print(f"✅ Statistiques agrégées :")
            print(f"   📅 Date : {yesterday}")
            print(f"   👥 Visiteurs uniques : {unique_sessions}")
            print(f"   📄 Pages vues : {total_page_views}")
            print(f"   📊 Pages/visiteur : {total_page_views / unique_sessions:.1f}" if unique_sessions > 0 else "   📊 Pages/visiteur : 0")
        else:
            print(f"⚠️  Aucune visite enregistrée le {yesterday}")
            print("💡 Aucune donnée à agréger")
        
        print("=" * 70)

def aggregate_all_historical_data():
    """Agrège TOUTES les données historiques (une seule fois au début)"""
    with app.app_context():
        print("=" * 70)
        print("📊 AGRÉGATION DE TOUTES LES DONNÉES HISTORIQUES")
        print("=" * 70)
        
        # Récupérer toutes les dates ayant des visites
        dates_with_visits = db.session.query(
            func.date(VisitorLog.visited_at).label('visit_date')
        ).distinct().order_by('visit_date').all()
        
        total_days = len(dates_with_visits)
        print(f"📅 {total_days} jour(s) de données à agréger...")
        print()
        
        for idx, (visit_date,) in enumerate(dates_with_visits, 1):
            # Vérifier si déjà agrégé
            existing = db.session.execute(
                text("SELECT COUNT(*) as cnt FROM daily_stats WHERE stat_date = :date"),
                {"date": visit_date}
            ).fetchone()
            
            if existing and existing[0] > 0:
                print(f"[{idx}/{total_days}] ⏭️  {visit_date} déjà agrégé")
                continue
            
            # Calculer les stats pour cette date
            start_of_day = datetime.combine(visit_date, datetime.min.time())
            end_of_day = datetime.combine(visit_date, datetime.max.time())
            
            total_page_views = db.session.query(func.count(VisitorLog.id)).filter(
                VisitorLog.visited_at >= start_of_day,
                VisitorLog.visited_at <= end_of_day
            ).scalar() or 0
            
            unique_sessions = db.session.query(func.count(func.distinct(VisitorLog.session_id))).filter(
                VisitorLog.visited_at >= start_of_day,
                VisitorLog.visited_at <= end_of_day
            ).scalar() or 0
            
            # Insérer
            db.session.execute(
                text("""
                    INSERT INTO daily_stats (stat_date, total_visitors, total_page_views, unique_sessions)
                    VALUES (:date, :visitors, :page_views, :sessions)
                """),
                {
                    "date": visit_date,
                    "visitors": unique_sessions,
                    "page_views": total_page_views,
                    "sessions": unique_sessions
                }
            )
            db.session.commit()
            
            print(f"[{idx}/{total_days}] ✅ {visit_date} : {unique_sessions} visiteurs, {total_page_views} pages")
        
        print()
        print("=" * 70)
        print("✅ AGRÉGATION HISTORIQUE TERMINÉE !")
        print("=" * 70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--historical":
        aggregate_all_historical_data()
    else:
        aggregate_yesterday_stats()
