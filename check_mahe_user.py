#!/usr/bin/env python3
"""Script pour trouver l'utilisateur du spectacle Mahé"""

from app import app, db
from models.models import Show, User

with app.app_context():
    # Chercher le spectacle
    show = Show.query.filter(Show.title.like('%Mahé%')).first()
    
    if show:
        print(f"📋 Spectacle trouvé : {show.title}")
        print(f"📅 Créé le : {show.created_at}")
        print(f"🆔 ID Spectacle : {show.id}")
        print()
        
        if show.user:
            print(f"👤 Utilisateur : {show.user.username}")
            print(f"🏢 Raison sociale : {show.user.raison_sociale or 'Non renseignée'}")
            print(f"📧 Email : {show.user.email or 'Non renseigné'}")
            print(f"📞 Téléphone : {show.user.telephone or 'Non renseigné'}")
            print(f"🆔 ID User : {show.user_id}")
            print(f"✅ Abonné : {'Oui' if show.user.is_subscribed else 'Non'}")
            print(f"🔑 Admin : {'Oui' if show.user.is_admin else 'Non'}")
        else:
            print("❌ Aucun utilisateur associé")
    else:
        print("❌ Spectacle 'Mahé' non trouvé dans la base de données locale")
