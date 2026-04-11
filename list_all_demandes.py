#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script pour afficher tous les appels d'offre avec leurs statuts"""

from app import create_app
from models.models import DemandeAnimation

app = create_app()

with app.app_context():
    demandes = DemandeAnimation.query.order_by(DemandeAnimation.created_at.desc()).all()
    
    print(f"\n{'='*80}")
    print(f"📋 TOUS LES APPELS D'OFFRE ({len(demandes)} total)")
    print(f"{'='*80}\n")
    
    if demandes:
        for d in demandes:
            statut_private = "🔒 PRIVÉ" if d.is_private else "📢 PUBLIC"
            statut_approved = "✅ APPROUVÉ" if d.approved else "⏳ EN ATTENTE"
            visible = "👁️ VISIBLE" if (not d.is_private and d.approved) else "❌ NON VISIBLE"
            
            print(f"ID {d.id}: {d.intitule or d.genre_recherche}")
            print(f"  ├─ Structure: {d.structure}")
            print(f"  ├─ Lieu: {d.lieu_ville}")
            print(f"  ├─ Email: {d.contact_email}")
            print(f"  ├─ Créé: {d.created_at}")
            print(f"  ├─ Statut: {statut_private} | {statut_approved} | {visible}")
            print()
    else:
        print("Aucun appel d'offre dans la base de données.\n")
    
    # Statistiques
    public_approved = DemandeAnimation.query.filter_by(is_private=False, approved=True).count()
    public_pending = DemandeAnimation.query.filter_by(is_private=False, approved=False).count()
    private_approved = DemandeAnimation.query.filter_by(is_private=True, approved=True).count()
    private_pending = DemandeAnimation.query.filter_by(is_private=True, approved=False).count()
    
    print(f"{'='*80}")
    print(f"📊 STATISTIQUES DÉTAILLÉES")
    print(f"{'='*80}")
    print(f"📢 Publics approuvés (VISIBLES sur le site) : {public_approved}")
    print(f"⏳ Publics en attente (NON VISIBLES) : {public_pending}")
    print(f"🔒 Privés approuvés : {private_approved}")
    print(f"🔒 Privés en attente : {private_pending}")
    print(f"{'='*80}\n")
