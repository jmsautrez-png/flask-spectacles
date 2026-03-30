"""
Script de migration : Ajoute la table visitor_log pour le tracking anonymisé des visiteurs.
Conforme RGPD - données anonymisées.
"""
from app import app, db
from models.models import VisitorLog

def migrate():
    """Crée la table visitor_log si elle n'existe pas."""
    with app.app_context():
        # Créer la table
        db.create_all()
        
        print("✅ Table visitor_log créée avec succès!")
        print("📊 Le tracking des visiteurs est maintenant activé.")
        print("⚠️  Pensez à mettre en place un nettoyage automatique des données > 30 jours pour RGPD.")

if __name__ == "__main__":
    migrate()
