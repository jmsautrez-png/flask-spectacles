#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la création d'appels d'offre
"""

from app import create_app
from models.models import DemandeAnimation, db
from datetime import datetime

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("🧪 TEST DE CRÉATION D'APPEL D'OFFRE")
    print("="*80 + "\n")
    
    # Compter avant
    count_before = DemandeAnimation.query.count()
    print(f"📊 Nombre d'appels d'offre AVANT le test : {count_before}")
    
    # Créer un appel d'offre de test (comme le formulaire public)
    test_demande = DemandeAnimation(
        auto_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        structure="TEST - Structure de test",
        telephone="0601020304",
        lieu_ville="Toulouse",
        code_postal="31000",
        region="Occitanie",
        nom="Jean Test",
        dates_horaires="15 mai 2026 à 14h",
        type_espace="Salle",
        type_evenement="Festival",
        genre_recherche="Marionnettes",
        age_range="6-12 ans",
        jauge="100 personnes",
        budget="1000-1500€",
        contraintes="Aucune",
        accessibilite="PMR",
        contact_email="test@example.com",
        intitule="Spectacle de marionnettes pour festival",
        is_private=False,  # PUBLIC
        approved=True  # APPROUVÉ automatiquement
    )
    
    db.session.add(test_demande)
    db.session.commit()
    
    print(f"\n✅ Appel d'offre de test créé (ID: {test_demande.id})")
    print(f"   ├─ Intitulé: {test_demande.intitule}")
    print(f"   ├─ Structure: {test_demande.structure}")
    print(f"   ├─ is_private: {test_demande.is_private}")
    print(f"   ├─ approved: {test_demande.approved}")
    print(f"   └─ VISIBLE: {'OUI ✅' if (not test_demande.is_private and test_demande.approved) else 'NON ❌'}")
    
    # Compter après
    count_after = DemandeAnimation.query.count()
    print(f"\n📊 Nombre d'appels d'offre APRÈS le test : {count_after}")
    print(f"   └─ Différence : +{count_after - count_before}")
    
    # Vérifier qu'il est dans les résultats de la requête publique
    public_visible = DemandeAnimation.query.filter_by(
        is_private=False,
        approved=True
    ).filter(DemandeAnimation.id == test_demande.id).first()
    
    if public_visible:
        print(f"\n🎉 SUCCÈS ! L'appel d'offre est bien visible dans la requête publique !")
    else:
        print(f"\n❌ ERREUR ! L'appel d'offre n'est PAS visible dans la requête publique !")
    
    # Nettoyer (supprimer le test)
    print(f"\n🧹 Nettoyage...")
    db.session.delete(test_demande)
    db.session.commit()
    print(f"   └─ Appel d'offre de test supprimé")
    
    # Vérifier le retour à l'état initial
    count_final = DemandeAnimation.query.count()
    if count_final == count_before:
        print(f"\n✅ Base de données revenue à l'état initial ({count_final} appels d'offre)")
    else:
        print(f"\n⚠️ Attention : {count_final} appels d'offre (attendu: {count_before})")
    
    print("\n" + "="*80)
    print("🏁 TEST TERMINÉ")
    print("="*80 + "\n")
