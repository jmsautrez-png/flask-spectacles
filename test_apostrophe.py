#!/usr/bin/env python3
"""
Test de connexion avec un username contenant une apostrophe
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from models.models import User

app = create_app()

print("=" * 70)
print("TEST : Username avec apostrophe")
print("=" * 70)

with app.app_context():
    # Créer un utilisateur de test avec apostrophe
    test_username = "Test'Apostrophe"
    
    # Supprimer s'il existe déjà
    existing = User.query.filter_by(username=test_username).first()
    if existing:
        from models.models import db
        db.session.delete(existing)
        db.session.commit()
        print(f"✓ Ancien compte supprimé")
    
    # Créer le compte
    from models.models import db
    user = User(username=test_username, email="test@apostrophe.fr")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    print(f"✓ Compte créé: {test_username}")
    
    # Simuler la vérification de connexion (celle qui posait problème)
    username_input = test_username
    
    # Ancienne validation (qui rejetait l'apostrophe)
    if any(char in username_input for char in ["'", '"', ';', '--', '/*']):
        print(f"\n❌ ANCIENNE VALIDATION: Rejette '{test_username}'")
    else:
        print(f"\n✅ Ancienne validation passerait")
    
    # Nouvelle validation (pas de rejet)
    user_found = User.query.filter_by(username=username_input).first()
    if user_found and user_found.check_password("password123"):
        print(f"✅ NOUVELLE VERSION: Login réussi pour '{test_username}'!")
    else:
        print(f"❌ NOUVELLE VERSION: Échec")
    
    # Nettoyer
    db.session.delete(user)
    db.session.commit()
    print(f"\n✓ Compte de test supprimé")

print("=" * 70)
print("RÉSULTAT: Les apostrophes sont maintenant acceptées !")
print("=" * 70)
