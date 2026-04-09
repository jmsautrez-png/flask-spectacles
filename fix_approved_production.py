#!/usr/bin/env python3
"""
Script pour vérifier et corriger la colonne 'approved' en production PostgreSQL
À exécuter via: render run python fix_approved_production.py
"""

import os
from app import create_app
from models.models import db, DemandeAnimation
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("VÉRIFICATION ET CORRECTION COLONNE 'approved' EN PRODUCTION")
    print("="*70)
    
    # Vérifier si la colonne existe
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('demande_animation')]
    
    print(f"\n📋 Colonnes existantes dans 'demande_animation':")
    for col in columns:
        print(f"   - {col}")
    
    if 'approved' not in columns:
        print("\n❌ La colonne 'approved' N'EXISTE PAS")
        print("📝 Ajout de la colonne...")
        
        try:
            # Ajouter la colonne
            db.session.execute(text("""
                ALTER TABLE demande_animation 
                ADD COLUMN approved BOOLEAN DEFAULT FALSE;
            """))
            db.session.commit()
            print("✅ Colonne 'approved' ajoutée avec succès!")
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout: {e}")
            db.session.rollback()
    else:
        print("\n✅ La colonne 'approved' EXISTE")
    
    # Vérifier l'état des demandes
    print("\n📊 État des demandes:")
    total = DemandeAnimation.query.count()
    publiques = DemandeAnimation.query.filter_by(is_private=False).count()
    privees = DemandeAnimation.query.filter_by(is_private=True).count()
    
    try:
        approuvees = DemandeAnimation.query.filter_by(approved=True).count()
        en_attente = DemandeAnimation.query.filter_by(is_private=False, approved=False).count()
        
        print(f"   📊 Total: {total}")
        print(f"   📢 Publiques: {publiques}")
        print(f"   🔒 Privées: {privees}")
        print(f"   ✅ Approuvées: {approuvees}")
        print(f"   ⏳ En attente (publiques non approuvées): {en_attente}")
        
        if en_attente > 0:
            print(f"\n⚠️  Il y a {en_attente} demande(s) publique(s) non approuvée(s)")
            print("📝 Approbation automatique des demandes publiques existantes...")
            
            demandes_a_approuver = DemandeAnimation.query.filter_by(is_private=False, approved=False).all()
            for d in demandes_a_approuver:
                d.approved = True
                print(f"   ✅ Demande ID {d.id} approuvée: {d.intitule or d.genre_recherche}")
            
            db.session.commit()
            print(f"\n✅ {len(demandes_a_approuver)} demande(s) approuvée(s) avec succès!")
        else:
            print("\n✅ Toutes les demandes publiques sont déjà approuvées")
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")
        print("⚠️  La colonne 'approved' existe peut-être mais avec un problème")
    
    # Afficher les 5 dernières demandes
    print("\n📋 5 dernières demandes:")
    try:
        derniers = DemandeAnimation.query.order_by(DemandeAnimation.created_at.desc()).limit(5).all()
        for d in derniers:
            statut = "🔒 PRIVÉE" if d.is_private else ("✅ APPROUVÉE" if d.approved else "⏳ EN ATTENTE")
            print(f"   - ID {d.id}: {d.intitule or d.genre_recherche} [{statut}]")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "="*70)
    print("FIN DU TRAITEMENT")
    print("="*70 + "\n")
