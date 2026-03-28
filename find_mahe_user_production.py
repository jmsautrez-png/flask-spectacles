#!/usr/bin/env python3
"""
Script pour trouver l'utilisateur du spectacle "Mahé et la forêt des Enchantés"
À exécuter dans le Shell Render
"""

from app import app, db
from models.models import Show, User

with app.app_context():
    # Chercher le spectacle Mahé
    show = Show.query.filter(Show.title.like('%Mahé%')).first()
    
    if show:
        print("=" * 70)
        print("📋 SPECTACLE TROUVÉ")
        print("=" * 70)
        print(f"Titre : {show.title}")
        print(f"ID : {show.id}")
        print(f"Catégorie : {show.category}")
        print(f"Tranche d'âge : {show.age_range}")
        print(f"Créé le : {show.created_at}")
        print(f"Approuvé : {'✅ Oui' if show.approved else '❌ Non'}")
        print()
        
        if show.user:
            print("=" * 70)
            print("👤 UTILISATEUR QUI A PUBLIÉ CE SPECTACLE")
            print("=" * 70)
            print(f"Username : {show.user.username}")
            print(f"Raison sociale : {show.user.raison_sociale or 'Non renseignée'}")
            print(f"Email : {show.user.email or 'Non renseigné'}")
            print(f"Téléphone : {show.user.telephone or 'Non renseigné'}")
            print(f"Région : {show.user.region or 'Non renseignée'}")
            print(f"Site internet : {show.user.site_internet or 'Non renseigné'}")
            print(f"ID User : {show.user_id}")
            print(f"Abonné premium : {'✅ Oui' if show.user.is_subscribed else '❌ Non'}")
            print(f"Compte créé le : {show.user.created_at}")
            print("=" * 70)
        else:
            print("❌ Aucun utilisateur associé à ce spectacle")
    else:
        print("❌ Spectacle 'Mahé' non trouvé dans la base de données")
        print()
        print("📋 Recherche de tous les spectacles contenant 'forêt' ou 'Enchantés'...")
        shows = Show.query.filter(
            (Show.title.like('%forêt%')) | 
            (Show.title.like('%Enchant%')) |
            (Show.description.like('%Mahé%'))
        ).all()
        
        if shows:
            print(f"Trouvé {len(shows)} spectacle(s) :")
            for s in shows:
                print(f"  - ID {s.id}: {s.title} (User: {s.user.username if s.user else 'N/A'})")
        else:
            print("Aucun spectacle trouvé avec ces critères")
