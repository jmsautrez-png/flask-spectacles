#!/usr/bin/env python3
"""
Script pour créer un utilisateur Artémisia et associer le spectacle Mahé
À exécuter dans le Shell Render
"""

from app import app, db
from models.models import User, Show
from datetime import datetime

with app.app_context():
    print("=" * 70)
    print("🔧 CRÉATION UTILISATEUR ARTÉMISIA ET ASSOCIATION SPECTACLE")
    print("=" * 70)
    
    # 1. Vérifier si l'utilisateur existe déjà
    existing_user = User.query.filter(
        (User.username == 'Artemisia') | 
        (User.raison_sociale.like('%Artémisia%'))
    ).first()
    
    if existing_user:
        print(f"✅ Utilisateur trouvé : {existing_user.username}")
        user = existing_user
    else:
        # 2. Créer l'utilisateur Artémisia
        print("📝 Création du compte Artémisia...")
        user = User(
            username='Artemisia',
            raison_sociale='Compagnie Artémisia',
            email='artemisia@spectacle.fr',  # Email fictif, à modifier si besoin
            is_admin=False,
            is_subscribed=False,
            created_at=datetime.utcnow()
        )
        # Définir un mot de passe temporaire
        user.set_password('Artemisia2026')  # Mot de passe à changer
        
        db.session.add(user)
        db.session.commit()
        print(f"✅ Utilisateur créé : {user.username} (ID: {user.id})")
        print(f"   📧 Email : {user.email}")
        print(f"   🔑 Mot de passe temporaire : Artemisia2026")
    
    # 3. Récupérer le spectacle Mahé
    show = Show.query.get(83)
    
    if not show:
        print("❌ Spectacle ID 83 introuvable !")
    else:
        print(f"\n📋 Spectacle trouvé : {show.title}")
        print(f"   Ancien user_id : {show.user_id}")
        
        # 4. Associer le spectacle à l'utilisateur
        show.user_id = user.id
        db.session.commit()
        
        print(f"   ✅ Nouveau user_id : {show.user_id}")
        print(f"\n🎉 Association réussie !")
        print(f"   '{show.title}' est maintenant lié à '{user.username}'")
    
    # 5. Vérification finale
    print("\n" + "=" * 70)
    print("📊 VÉRIFICATION FINALE")
    print("=" * 70)
    
    show_check = Show.query.get(83)
    if show_check and show_check.user:
        print(f"✅ Spectacle : {show_check.title}")
        print(f"✅ Propriétaire : {show_check.user.username}")
        print(f"✅ Raison sociale : {show_check.user.raison_sociale}")
        print(f"✅ Email : {show_check.user.email}")
        print("\n🎊 Tout fonctionne correctement !")
    else:
        print("❌ Erreur lors de la vérification")
    
    print("=" * 70)
