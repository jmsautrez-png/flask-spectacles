#!/usr/bin/env python3
"""Script pour ajouter un email à l'utilisateur admin"""

from app import create_app
from models.models import db, User

app = create_app()

with app.app_context():
    # Trouver l'admin
    admin = User.query.filter_by(is_admin=True).first()
    
    if admin:
        print(f"\n✅ Admin trouvé: {admin.username}")
        print(f"   Email actuel: {admin.email if hasattr(admin, 'email') and admin.email else 'PAS D\'EMAIL'}")
        
        # Définir l'email
        email_admin = "contact@spectacleanimation.fr"  # Changez si nécessaire
        
        admin.email = email_admin
        db.session.commit()
        
        print(f"\n✅ Email ajouté avec succès!")
        print(f"   Nouvel email: {admin.email}")
    else:
        print("\n❌ Aucun admin trouvé")
