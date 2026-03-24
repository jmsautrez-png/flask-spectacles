#!/usr/bin/env python3
"""
Script pour vérifier et gérer les utilisateurs
Usage: python check_user.py [username ou email]
"""
import sys
from app import create_app
from models.models import User

def check_user(identifier):
    """Vérifie si un utilisateur existe par nom d'utilisateur ou email"""
    app = create_app()
    with app.app_context():
        # Chercher par username
        user = User.query.filter_by(username=identifier).first()
        if not user:
            # Chercher par email
            user = User.query.filter_by(email=identifier).first()
        
        if user:
            print("\n✓ UTILISATEUR TROUVÉ")
            print("=" * 50)
            print(f"ID: {user.id}")
            print(f"Nom d'utilisateur: {user.username}")
            print(f"Email: {user.email or 'Non renseigné'}")
            print(f"Raison sociale: {user.raison_sociale or 'Non renseignée'}")
            print(f"Téléphone: {user.telephone or 'Non renseigné'}")
            print(f"Région: {user.region or 'Non renseignée'}")
            print(f"Site internet: {user.site_internet or 'Non renseigné'}")
            print(f"Admin: {'Oui' if user.is_admin else 'Non'}")
            print(f"Abonné: {'Oui' if user.is_subscribed else 'Non'}")
            print(f"Créé le: {user.created_at}")
            print("=" * 50)
            
            # Proposer de supprimer
            if not user.is_admin:
                choice = input("\n⚠️  Voulez-vous supprimer cet utilisateur ? (oui/non): ").strip().lower()
                if choice == 'oui':
                    from models import db
                    db.session.delete(user)
                    db.session.commit()
                    print(f"✓ Utilisateur '{user.username}' supprimé avec succès!")
                else:
                    print("✓ Aucune modification effectuée")
            else:
                print("\n⚠️  Cet utilisateur est ADMIN - impossible de le supprimer via ce script")
        else:
            print(f"\n✗ AUCUN UTILISATEUR trouvé avec '{identifier}'")
            
            # Suggestions
            print("\nVoulez-vous chercher des utilisateurs similaires ?")
            all_users = User.query.all()
            print(f"\nTotal: {len(all_users)} utilisateurs dans la base")
            
            similar = [u for u in all_users if identifier.lower() in (u.username or '').lower() 
                      or identifier.lower() in (u.email or '').lower()
                      or identifier.lower() in (u.raison_sociale or '').lower()]
            
            if similar:
                print(f"\nUtilisateurs similaires trouvés ({len(similar)}):")
                for u in similar[:10]:  # Limiter à 10 résultats
                    print(f"  - {u.username} ({u.email or 'Pas d\'email'})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_user.py [username ou email]")
        print("Exemple: python check_user.py julie")
        print("         python check_user.py julie@email.fr")
        sys.exit(1)
    
    identifier = sys.argv[1]
    check_user(identifier)
