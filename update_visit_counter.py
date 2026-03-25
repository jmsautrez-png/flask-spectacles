#!/usr/bin/env python3
"""
Script pour mettre à jour le compteur de visites à une valeur spécifique.
"""
from app import app, db
from models.models import PageVisit

def update_counter(count=6800):
    """Met à jour le compteur de visites de la page d'accueil."""
    with app.app_context():
        visit_counter = PageVisit.query.filter_by(page_name='home').first()
        
        if visit_counter:
            visit_counter.visit_count = count
            db.session.commit()
            print(f"✅ Compteur mis à jour : {count:,} visites".replace(',', ' '))
        else:
            print("❌ Le compteur n'existe pas. Veuillez d'abord exécuter migrate_add_page_visit.py")

if __name__ == "__main__":
    update_counter(6800)
