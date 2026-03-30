#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script d'initialisation de la base de données
Crée toutes les tables définies dans les modèles SQLAlchemy
"""
import sys
import os
from sqlalchemy import inspect, text

print("=" * 70)
print("INITIALISATION BASE DE DONNÉES - spectacleanimation.fr")
print("=" * 70)

try:
    from app import app, db
    print("✓ Modules importés avec succès")
except Exception as e:
    print(f"✗ Erreur lors de l'import des modules: {e}")
    sys.exit(1)

# Afficher les informations de configuration
with app.app_context():
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    db_type = "PostgreSQL" if "postgresql" in db_uri else "SQLite" if "sqlite" in db_uri else "Inconnu"
    
    # Masquer les credentials dans l'affichage
    if db_uri:
        if '@' in db_uri:
            parts = db_uri.split('@')
            safe_uri = parts[0].split('://')[0] + "://***:***@" + parts[1]
        else:
            safe_uri = db_uri
    else:
        safe_uri = "Non configurée"
    
    print(f"\n📊 Configuration Base de Données:")
    print(f"   Type: {db_type}")
    print(f"   URI: {safe_uri}")
    print(f"   Environnement: {os.environ.get('FLASK_ENV', 'development')}")
    
    # Tester la connexion
    print(f"\n🔗 Test de connexion...")
    try:
        db.session.execute(text("SELECT 1"))
        print("   ✓ Connexion réussie")
    except Exception as e:
        print(f"   ✗ Échec de connexion: {e}")
        print("\n⚠️  Vérifiez que:")
        print("   - La base de données existe")
        print("   - DATABASE_URL est correctement configuré")
        print("   - Les credentials sont valides")
        sys.exit(1)
    
    # Créer les tables
    print(f"\n📝 Création des tables...")
    try:
        db.create_all()
        print("   ✓ Tables créées avec succès")
    except Exception as e:
        print(f"   ✗ Erreur lors de la création des tables: {e}")
        sys.exit(1)
    
    # Vérifier les tables créées
    print(f"\n🔍 Vérification des tables créées:")
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"   Nombre de tables: {len(tables)}")
            for table in sorted(tables):
                columns = inspector.get_columns(table)
                print(f"   ✓ {table} ({len(columns)} colonnes)")
        else:
            print("   ⚠️  Aucune table détectée")
    except Exception as e:
        print(f"   ⚠️  Impossible de lister les tables: {e}")
    
    # Vérifier les colonnes photos multiples dans la table shows
    print(f"\n📸 Vérification colonnes photos multiples (shows)...")
    try:
        inspector = inspect(db.engine)
        if 'shows' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('shows')]
            
            required_photo_cols = [
                'file_name', 'file_mimetype',
                'file_name2', 'file_mimetype2',
                'file_name3', 'file_mimetype3'
            ]
            
            missing = [col for col in required_photo_cols if col not in columns]
            
            if missing:
                print(f"   ⚠️  Colonnes manquantes: {', '.join(missing)}")
                print(f"   💡 Exécutez: python migrate_add_photos.py")
            else:
                print(f"   ✓ Toutes les colonnes photos présentes")
    except Exception as e:
        print(f"   ⚠️  Vérification échouée: {e}")

print("\n" + "=" * 70)
print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
print("=" * 70)
print("\n💡 Prochaines étapes:")
print("   1. Vérifier les tables avec: python list_tables.py")
print("   2. Créer un compte admin via /register")
print("   3. Publier votre premier spectacle")
print()
