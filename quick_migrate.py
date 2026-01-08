#!/usr/bin/env python3
"""
Script de migration rapide pour production
Peut être exécuté via Render Shell ou SSH

Usage:
    python quick_migrate.py
"""

import os
import sys

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from sqlalchemy import text, inspect
    
    print("\n" + "="*60)
    print("🔧 MIGRATION RAPIDE - BASE DE DONNÉES")
    print("="*60 + "\n")
    
    with app.app_context():
        engine_name = db.engine.dialect.name
        print(f"📊 Base de données : {engine_name}\n")
        
        # Migration 1 : is_private
        print("1️⃣ Vérification colonne is_private...")
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('demande_animation')]
            
            if 'is_private' not in columns:
                print("   ➜ Ajout de la colonne is_private...")
                if engine_name in ['postgresql', 'postgres']:
                    db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT FALSE'))
                else:
                    db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT 0'))
                db.session.commit()
                print("   ✅ Colonne is_private ajoutée\n")
            else:
                print("   ✓ Colonne is_private existe déjà\n")
        except Exception as e:
            print(f"   ⚠️ Erreur: {e}\n")
            db.session.rollback()
        
        # Migration 2 : location et category
        print("2️⃣ Vérification taille colonnes location/category...")
        try:
            if engine_name in ['postgresql', 'postgres']:
                print("   ➜ Extension des colonnes pour PostgreSQL...")
                db.session.execute(text("ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500)"))
                db.session.execute(text("ALTER TABLE shows ALTER COLUMN category TYPE VARCHAR(500)"))
                db.session.commit()
                print("   ✅ Colonnes étendues à 500 caractères\n")
            elif engine_name in ['mysql', 'mariadb']:
                print("   ➜ Extension des colonnes pour MySQL/MariaDB...")
                db.session.execute(text("ALTER TABLE shows MODIFY COLUMN location VARCHAR(500)"))
                db.session.execute(text("ALTER TABLE shows MODIFY COLUMN category VARCHAR(500)"))
                db.session.commit()
                print("   ✅ Colonnes étendues à 500 caractères\n")
            elif engine_name == 'sqlite':
                print("   ✓ SQLite détecté (probablement déjà migré localement)\n")
            else:
                print(f"   ⚠️ Type de base non supporté: {engine_name}\n")
        except Exception as e:
            error_str = str(e)
            if 'does not exist' in error_str.lower() or 'type varchar(500)' in error_str.lower():
                print("   ✓ Colonnes déjà au bon format\n")
            else:
                print(f"   ⚠️ Erreur: {e}\n")
            db.session.rollback()
        
        print("="*60)
        print("✅ MIGRATION TERMINÉE")
        print("="*60)
        print("\n➜ Redémarrez maintenant l'application\n")

except ImportError as e:
    print(f"\n❌ ERREUR: Impossible d'importer les modules nécessaires")
    print(f"   {e}")
    print("\n➜ Assurez-vous d'être dans le bon répertoire")
    print("➜ Vérifiez que requirements.txt est installé\n")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERREUR INATTENDUE: {e}\n")
    sys.exit(1)
