#!/usr/bin/env python3
"""Script pour afficher les appels d'offre récents"""

from app import app, db
from models.models import DemandeAnimation
from datetime import datetime, timedelta

with app.app_context():
    # Récupérer les appels d'offre des dernières 24 heures
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_demandes = DemandeAnimation.query.filter(
        DemandeAnimation.created_at >= yesterday
    ).order_by(DemandeAnimation.created_at.desc()).all()
    
    print("\n" + "=" * 70)
    print("📋 APPELS D'OFFRE RÉCENTS (dernières 24h)")
    print("=" * 70)
    
    if not recent_demandes:
        print("\n❌ Aucun appel d'offre trouvé dans les dernières 24h")
        print("\nRecherche dans tous les appels d'offre...")
        all_demandes = DemandeAnimation.query.order_by(
            DemandeAnimation.created_at.desc()
        ).limit(5).all()
        
        if all_demandes:
            print("\n" + "=" * 70)
            print("📋 5 DERNIERS APPELS D'OFFRE")
            print("=" * 70)
            for demande in all_demandes:
                print(f"\n🆔 ID: {demande.id}")
                print(f"📝 Intitulé: {demande.intitule or 'Non précisé'}")
                print(f"🏢 Structure: {demande.structure}")
                print(f"📍 Lieu: {demande.lieu_ville}")
                print(f"🎭 Genre recherché: {demande.genre_recherche}")
                print(f"📅 Dates: {demande.dates_horaires}")
                print(f"💰 Budget: {demande.budget} €")
                print(f"👥 Jauge: {demande.jauge}")
                print(f"👶 Public: {demande.age_range}")
                print(f"📧 Email contact: {demande.contact_email}")
                print(f"📱 Téléphone: {demande.telephone or 'Non renseigné'}")
                print(f"🔒 Privé: {'Oui' if demande.is_private else 'Non'}")
                print(f"✅ Approuvé: {'Oui' if demande.approved else 'Non'}")
                print(f"🕐 Créé le: {demande.created_at}")
                print("-" * 70)
    else:
        for demande in recent_demandes:
            print(f"\n🆔 ID: {demande.id}")
            print(f"📝 Intitulé: {demande.intitule or 'Non précisé'}")
            print(f"🏢 Structure: {demande.structure}")
            print(f"📍 Lieu: {demande.lieu_ville}")
            print(f"🎭 Genre recherché: {demande.genre_recherche}")
            print(f"📅 Dates: {demande.dates_horaires}")
            print(f"💰 Budget: {demande.budget} €")
            print(f"👥 Jauge: {demande.jauge}")
            print(f"👶 Public: {demande.age_range}")
            print(f"📧 Email contact: {demande.contact_email}")
            print(f"📱 Téléphone: {demande.telephone or 'Non renseigné'}")
            print(f"🔒 Privé: {'Oui' if demande.is_private else 'Non'}")
            print(f"✅ Approuvé: {'Oui' if demande.approved else 'Non'}")
            print(f"🕐 Créé le: {demande.created_at}")
            print("-" * 70)
    
    print("\n" + "=" * 70)
    print("💡 POUR RENVOYER UN APPEL D'OFFRE")
    print("=" * 70)
    print("1. Connectez-vous: http://127.0.0.1:5000/login")
    print("2. Allez dans: Appels d'offre (menu admin)")
    print("3. Cliquez sur l'icône ✉️ à droite de l'appel d'offre")
    print("4. Sélectionnez catégories et régions")
    print("5. Prévisualisez puis envoyez ✅")
    print("=" * 70)
