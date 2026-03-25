#!/usr/bin/env python3
"""Vérification rapide d'un utilisateur dans la base de données"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from models.models import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='test_6ii3i1ok').first()
    if user:
        print("=" * 60)
        print("UTILISATEUR TROUVE DANS LA BASE DE DONNEES!")
        print("=" * 60)
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Telephone: {user.telephone}")
        print(f"Site internet: {user.site_internet}")
        print(f"Raison sociale: {user.raison_sociale}")
        print(f"Region: {user.region}")
        print("=" * 60)
        print("CONCLUSION: L'inscription a bien fonctionne!")
    else:
        print("=" * 60)
        print("UTILISATEUR NON TROUVE")
        print("=" * 60)
        print("L'utilisateur test_6ii3i1ok n'existe pas en base")
        
        # Vérifions le dernier utilisateur créé
        last_user = User.query.order_by(User.id.desc()).first()
        if last_user:
            print(f"\nDernier utilisateur cree:")
            print(f"  Username: {last_user.username}")
            print(f"  Email: {last_user.email}")
