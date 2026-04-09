#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier et configurer l'email de l'admin en production
"""

from app import create_app, db
from sqlalchemy import text

# Créer l'application
app = create_app()

with app.app_context():
    print("=" * 70)
    print("🔍 VÉRIFICATION EMAIL ADMIN EN PRODUCTION")
    print("=" * 70)
    
    # Récupérer l'admin via SQL direct
    result = db.session.execute(
        text("SELECT id, username, email, is_admin FROM \"user\" WHERE is_admin = TRUE LIMIT 1")
    ).fetchone()
    
    if result:
        user_id, username, email, is_admin = result
        print(f"\n✅ Admin trouvé:")
        print(f"   ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Email: {email if email else '❌ PAS D EMAIL'}")
        print(f"   Is Admin: {is_admin}")
        
        if not email:
            print("\n⚠️  L'admin n'a PAS d'email configuré!")
            print("📧 Ajout de l'email: contact@spectacleanimation.fr")
            
            db.session.execute(
                text("UPDATE \"user\" SET email = :email WHERE id = :user_id"),
                {"email": "contact@spectacleanimation.fr", "user_id": user_id}
            )
            db.session.commit()
            
            print("✅ Email ajouté avec succès!")
            
            # Vérification
            result_check = db.session.execute(
                text("SELECT email FROM \"user\" WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            print(f"✅ Vérification: {result_check[0]}")
        else:
            print("\n✅ L'admin a déjà un email configuré!")
    else:
        print("\n❌ Aucun admin trouvé!")
    
    print("\n" + "=" * 70)
    print("FIN DE LA VÉRIFICATION")
    print("=" * 70)
