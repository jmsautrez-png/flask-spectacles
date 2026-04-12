#!/usr/bin/env python3
"""
Script pour créer rapidement un appel d'offre de test
Usage: python test_creer_appel_offre.py
"""

from app import create_app
from models.models import db, DemandeAnimation
from datetime import datetime

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("📢 CRÉATION APPEL D'OFFRE DE TEST")
    print("="*70)
    
    # Créer un appel d'offre de test
    appel = DemandeAnimation(
        structure="Mairie de TEST",
        nom="Organisateur Test",
        contact_email="test@example.com",
        telephone="01 23 45 67 89",
        genre_recherche="Magie",  # Correspond au spectacle créé
        lieu_ville="Île-de-France",  # Correspond à la région
        dates_horaires="15 juin 2026, 15h-17h",
        type_espace="Salle municipale",
        age_range="Tout public",
        jauge="200",
        budget="800",
        contraintes="Parking disponible pour le matériel",
        type_evenement="Fête de la ville",
        is_private=False,  # PUBLIC
        approved=True,  # APPROUVÉ
        created_at=datetime.utcnow()
    )
    
    db.session.add(appel)
    db.session.commit()
    
    print(f"\n✅ Appel d'offre créé avec succès!")
    print(f"   - ID: {appel.id}")
    print(f"   - Structure: {appel.structure}")
    print(f"   - Genre: {appel.genre_recherche}")
    print(f"   - Lieu: {appel.lieu_ville}")
    print(f"   - Public: {not appel.is_private}")
    print(f"   - Approuvé: {appel.approved}")
    
    print("\n🎯 POUR ENVOYER CET APPEL D'OFFRE:")
    print(f"   1. Ouvrez votre navigateur: http://localhost:5000")
    print(f"   2. Connectez-vous en admin")
    print(f"   3. Allez sur: http://localhost:5000/admin/demandes-animation")
    print(f"   4. Cliquez sur 'Envoyer' pour l'appel #{appel.id}")
    print(f"   5. Prévisualisez les destinataires")
    print(f"   6. Envoyez l'email")
    
    print("\n" + "="*70)
    print("\n")
