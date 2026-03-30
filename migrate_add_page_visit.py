#!/usr/bin/env python3
"""
Script de migration : Ajoute la table page_visit pour le compteur de visites.
"""
from app import app, db
from models.models import PageVisit

def migrate():
    """Crée la table page_visit si elle n'existe pas."""
    with app.app_context():
        # Créer la table si elle n'existe pas
        db.create_all()
        
        # Initialiser le compteur pour la page d'accueil
        existing = PageVisit.query.filter_by(page_name='home').first()
        if not existing:
            counter = PageVisit(page_name='home', visit_count=6800)
            db.session.add(counter)
            db.session.commit()
            print("✅ Table page_visit créée et initialisée avec succès à 6800 visites!")
        else:
            print("ℹ️  La table page_visit existe déjà.")

if __name__ == "__main__":
    migrate()
