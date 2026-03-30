#!/usr/bin/env python3
"""
Script de migration SQL brut - contourne le chargement des modèles
À exécuter AVANT de redémarrer l'application
"""

import sys
import os
import sqlite3

# Chemin vers la base de données SQLite locale (pour test)
DB_PATH = "instance/app.db"

def migrate_local():
    """Migration pour SQLite local"""
    if not os.path.exists(DB_PATH):
        print(f"⚠️  Base de données locale non trouvée : {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📊 Migration SQLite locale...\n")
        
        # 1. Ajouter is_private à demande_animation
        print("1️⃣ Colonne demande_animation.is_private...")
        try:
            cursor.execute("ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT 0")
            conn.commit()
            print("   ✅ Colonne is_private ajoutée")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("   ✓ Colonne is_private existe déjà")
            else:
                print(f"   ⚠️ {e}")
        
        # 2. Ajouter email à users
        print("\n2️⃣ Colonne users.email...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
            conn.commit()
            print("   ✅ Colonne email ajoutée")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("   ✓ Colonne email existe déjà")
            else:
                print(f"   ⚠️ {e}")
        
        # 3. Ajouter created_at à users
        print("\n3️⃣ Colonne users.created_at...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
            conn.commit()
            print("   ✅ Colonne created_at ajoutée")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print("   ✓ Colonne created_at existe déjà")
            else:
                print(f"   ⚠️ {e}")
        
        # 4. Recréer table shows avec location et category à 500
        print("\n4️⃣ Extension shows.location et shows.category à 500 caractères...")
        try:
            # Vérifier si déjà migré
            cursor.execute("PRAGMA table_info(shows)")
            cols = cursor.fetchall()
            location_col = [c for c in cols if c[1] == 'location']
            
            if location_col and '500' not in str(location_col[0][2]):
                print("   ➜ Recréation de la table shows...")
                cursor.execute("""
                    CREATE TABLE shows_new (
                        id INTEGER PRIMARY KEY,
                        raison_sociale VARCHAR(200),
                        title VARCHAR(150) NOT NULL,
                        description TEXT,
                        region VARCHAR(200),
                        location VARCHAR(500),
                        category VARCHAR(500),
                        date DATE,
                        age_range VARCHAR(50),
                        file_name VARCHAR(255),
                        file_mimetype VARCHAR(120),
                        created_at DATETIME,
                        approved BOOLEAN,
                        contact_email VARCHAR(255),
                        contact_phone VARCHAR(20),
                        site_internet VARCHAR(255),
                        user_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                cursor.execute("INSERT INTO shows_new SELECT * FROM shows")
                cursor.execute("DROP TABLE shows")
                cursor.execute("ALTER TABLE shows_new RENAME TO shows")
                conn.commit()
                print("   ✅ Table shows migrée")
            else:
                print("   ✓ Colonnes déjà à 500 caractères")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        conn.close()
        print("\n" + "="*60)
        print("✅ Migration locale terminée !")
        print("="*60)
        return True
        
    except Exception as e:
        conn.close()
        print(f"\n❌ Erreur : {e}")
        return False

def print_postgres_commands():
    """Affiche les commandes PostgreSQL pour production"""
    print("\n" + "="*60)
    print("🐘 COMMANDES POSTGRESQL POUR PRODUCTION")
    print("="*60 + "\n")
    print("Exécutez ces commandes via psql ou Render Shell :\n")
    print("-- 1. Colonne is_private")
    print("ALTER TABLE demande_animation ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE;\n")
    print("-- 2. Colonne email")
    print("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);\n")
    print("-- 3. Colonne created_at")
    print("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;\n")
    print("-- 4. Extension location")
    print("ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500);\n")
    print("-- 5. Extension category")
    print("ALTER TABLE shows ALTER COLUMN category TYPE VARCHAR(500);\n")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("\n🔧 MIGRATION RAPIDE - SQL BRUT\n")
    
    # Migration locale SQLite
    if os.path.exists(DB_PATH):
        migrate_local()
    else:
        print("⚠️  Pas de base SQLite locale trouvée\n")
    
    # Afficher commandes PostgreSQL
    print_postgres_commands()
    
    print("📝 Pour appliquer en production :")
    print("   1. Connectez-vous à votre serveur de production")
    print("   2. Copiez-collez les commandes PostgreSQL ci-dessus")
    print("   3. OU exécutez : python migrate_production.py")
    print()
