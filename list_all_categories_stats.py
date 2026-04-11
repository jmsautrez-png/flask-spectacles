#!/usr/bin/env python3
"""Script pour lister toutes les catégories et leur nombre de compagnies"""

from app import app, db
from models.models import Show
from collections import defaultdict

with app.app_context():
    # Récupérer tous les spectacles approuvés
    shows = Show.query.filter(Show.approved.is_(True)).all()
    
    # Compter par catégorie
    category_stats = defaultdict(lambda: {'shows': 0, 'emails': set()})
    
    for show in shows:
        if show.category:
            # Extraire chaque catégorie (au cas où il y en a plusieurs)
            categories = [c.strip() for c in show.category.split(',')]
            for cat in categories:
                category_stats[cat]['shows'] += 1
                
                email = show.contact_email
                if not email and show.user:
                    email = show.user.email if hasattr(show.user, 'email') else None
                if email:
                    category_stats[cat]['emails'].add(email)
    
    print("\n" + "=" * 70)
    print("📊 STATISTIQUES PAR CATÉGORIE")
    print("=" * 70)
    print(f"\nTotal de spectacles approuvés: {len(shows)}")
    print(f"Nombre de catégories différentes: {len(category_stats)}")
    
    # Trier par nombre d'emails (décroissant)
    sorted_cats = sorted(
        category_stats.items(),
        key=lambda x: len(x[1]['emails']),
        reverse=True
    )
    
    print("\n" + "=" * 70)
    print("🎭 TOP CATÉGORIES (par nombre d'emails uniques)")
    print("=" * 70)
    
    for cat, stats in sorted_cats[:20]:  # Top 20
        num_emails = len(stats['emails'])
        num_shows = stats['shows']
        print(f"\n📂 {cat}")
        print(f"   Spectacles: {num_shows} | Emails uniques: {num_emails}")
        
        if num_emails == 11:
            print(f"   ⭐ CORRESPOND aux 11 compagnies !")
    
    print("\n" + "=" * 70)
    print("💡 SUGGESTION")
    print("=" * 70)
    print("Pour renvoyer l'appel d'offre:")
    print("1. Connectez-vous à http://127.0.0.1:5000/login")
    print("2. Menu Admin → Appels d'offre")
    print("3. Cliquez sur ✉️ à droite de l'appel souhaité")
    print("4. Sélectionnez les catégories qui vous donnent ~11 destinataires")
    print("5. Cette fois l'envoi fonctionnera ! ✅")
    print("=" * 70)
