#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script pour vérifier et approuver les appels d'offre en attente"""

from app import create_app
from models.models import DemandeAnimation, db

app = create_app()

with app.app_context():
    # Trouver toutes les demandes non approuvées
    demandes_pending = DemandeAnimation.query.filter_by(approved=False, is_private=False).all()
    
    print(f"\n{'='*60}")
    print(f"📋 APPELS D'OFFRE EN ATTENTE D'APPROBATION")
    print(f"{'='*60}\n")
    print(f"Nombre total : {len(demandes_pending)}\n")
    
    if demandes_pending:
        for d in demandes_pending:
            print(f"  ID {d.id}: {d.intitule or d.genre_recherche}")
            print(f"    └─ Structure: {d.structure}")
            print(f"    └─ Lieu: {d.lieu_ville}")
            print(f"    └─ Créé le: {d.created_at}")
            print()
        
        # Demander si on veut les approuver
        response = input("Voulez-vous approuver tous ces appels d'offre ? (o/n) : ").strip().lower()
        
        if response == 'o':
            for d in demandes_pending:
                d.approved = True
            db.session.commit()
            print(f"\n✅ {len(demandes_pending)} appel(s) d'offre approuvé(s) et publié(s) !\n")
        else:
            print("\n❌ Aucune modification effectuée.\n")
    else:
        print("✅ Aucun appel d'offre en attente d'approbation.\n")
    
    # Afficher un résumé
    total = DemandeAnimation.query.count()
    approved = DemandeAnimation.query.filter_by(approved=True).count()
    private = DemandeAnimation.query.filter_by(is_private=True).count()
    
    print(f"{'='*60}")
    print(f"📊 RÉSUMÉ")
    print(f"{'='*60}")
    print(f"Total d'appels d'offre : {total}")
    print(f"Approuvés et publics : {approved}")
    print(f"Privés : {private}")
    print(f"{'='*60}\n")
