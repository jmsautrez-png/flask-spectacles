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

# Import minimal sans charger les modèles complets
os.environ['SKIP_MODEL_VALIDATION'] = '1'

try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy import text, inspect, create_engine
    import config
    
    print("\n" + "="*60)
    print("🔧 MIGRATION RAPIDE - BASE DE DONNÉES")
    print("="*60 + "\n")
    
    # Créer une app Flask minimale
    app = Flask(__name__)
    app.config.from_object(config)
    db = SQLAlchemy(app)
    
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
        
        # Migration 3 : users.email et users.created_at
        print("3️⃣ Vérification colonnes users (email, created_at)...")
        try:
            inspector = inspect(db.engine)
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'email' not in user_columns:
                print("   ➜ Ajout de la colonne email...")
                db.session.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(255)'))
                db.session.commit()
                print("   ✅ Colonne email ajoutée")
            else:
                print("   ✓ Colonne email existe déjà")
            
            if 'created_at' not in user_columns:
                print("   ➜ Ajout de la colonne created_at...")
                if engine_name in ['postgresql', 'postgres']:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                else:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                db.session.commit()
                print("   ✅ Colonne created_at ajoutée\n")
            else:
                print("   ✓ Colonne created_at existe déjà\n")
        except Exception as e:
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
