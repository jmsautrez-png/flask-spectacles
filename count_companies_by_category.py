#!/usr/bin/env python3
"""Script pour compter les compagnies par catégorie"""

from app import app, db
from models.models import Show
from sqlalchemy import or_

with app.app_context():
    # Catégories des appels d'offre récents
    categories_to_check = {
        'Marionnette': 'Marionnettes (ID 11)',
        'Ventriloque': 'Ventriloque (ID 10)',
        'Manège': 'Manège (ID 8)'
    }
    
    print("\n" + "=" * 70)
    print("📊 NOMBRE DE COMPAGNIES PAR CATÉGORIE")
    print("=" * 70)
    
    for cat, label in categories_to_check.items():
        # Rechercher les spectacles approuvés dans cette catégorie
        shows = Show.query.filter(
            Show.approved.is_(True),
            Show.category.ilike(f'%{cat}%')
        ).all()
        
        # Compter les emails uniques
        emails = set()
        for show in shows:
            email = show.contact_email
            if not email and show.user:
                email = show.user.email if hasattr(show.user, 'email') else None
            if email:
                emails.add(email)
        
        print(f"\n🎭 {label}")
        print(f"   Spectacles trouvés: {len(shows)}")
        print(f"   📧 Emails uniques: {len(emails)}")
        
        if len(emails) > 0:
            print(f"   Liste des emails:")
            for i, email in enumerate(sorted(emails), 1):
                print(f"      {i}. {email}")
    
    print("\n" + "=" * 70)
    print("💡 L'appel d'offre avec ~11 destinataires correspond probablement")
    print("   à une de ces catégories (ou à plusieurs combinées)")
    print("=" * 70)
