"""
Script de nettoyage des données de tracking (Conformité RGPD)
Supprime automatiquement les données de visite de plus de 30 jours.

À exécuter régulièrement (quotidien recommandé) via cron ou planificateur de tâches.
"""
from app import app, db
from models.models import VisitorLog
from datetime import datetime, timedelta

def clean_old_visitor_logs(days=30):
    """Supprime les logs de visiteurs de plus de X jours"""
    with app.app_context():
        # Calculer la date limite
        date_limit = datetime.utcnow() - timedelta(days=days)
        
        # Compter les enregistrements à supprimer
        old_logs = VisitorLog.query.filter(VisitorLog.visited_at < date_limit).all()
        count = len(old_logs)
        
        if count == 0:
            print(f"✅ Aucune donnée de plus de {days} jours à supprimer.")
            return
        
        # Supprimer les anciens logs
        VisitorLog.query.filter(VisitorLog.visited_at < date_limit).delete()
        db.session.commit()
        
        print(f"✅ {count} enregistrements de plus de {days} jours supprimés.")
        print(f"📊 Conformité RGPD : Données nettoyées le {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')}")

if __name__ == "__main__":
    print("🗑️  Nettoyage des données de tracking...")
    clean_old_visitor_logs(30)  # Supprimer les données de plus de 30 jours
