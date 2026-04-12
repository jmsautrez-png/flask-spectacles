#!/usr/bin/env python3
"""
Script pour appliquer la migration d'extension du champ region
Augmente la taille de VARCHAR(100) à VARCHAR(200) pour toutes les tables
"""

import os
from sqlalchemy import text
from app import app, db

def migrate_region_columns():
    """Applique la migration pour étendre le champ region"""
    
    print("\n" + "=" * 70)
    print("🔧 MIGRATION: Extension du champ 'region' à 200 caractères")
    print("=" * 70)
    
    with app.app_context():
        # Détecter le type de base de données
        db_type = db.engine.dialect.name
        print(f"\n📊 Type de base de données détecté: {db_type}")
        
        if db_type == 'sqlite':
            print("\n⚠️  SQLite détecté - Migration non nécessaire")
            print("   SQLite n'a pas de limite stricte sur VARCHAR")
            print("   Les modèles Python avec String(200) suffisent")
            print("\n✅ AUCUNE ACTION REQUISE pour SQLite")
            return
        
        if db_type != 'postgresql':
            print(f"\n⚠️  Base de données '{db_type}' non supportée par ce script")
            print("   Ce script est conçu pour PostgreSQL uniquement")
            return
        
        print("✅ PostgreSQL détecté - Application de la migration...\n")
        
        migrations = [
            {
                'table': 'shows',
                'sql': "ALTER TABLE shows ALTER COLUMN region TYPE VARCHAR(200);"
            },
            {
                'table': 'demande_animation',
                'sql': "ALTER TABLE demande_animation ALTER COLUMN region TYPE VARCHAR(200);"
            },
            {
                'table': 'demande_ecole',
                'sql': "ALTER TABLE demande_ecole ALTER COLUMN region TYPE VARCHAR(200);"
            },
            {
                'table': 'visitor_logs',
                'sql': "ALTER TABLE visitor_logs ALTER COLUMN region TYPE VARCHAR(200);"
            }
        ]
        
        try:
            for migration in migrations:
                table = migration['table']
                sql = migration['sql']
                
                print(f"\n📋 Migration de la table '{table}'...")
                
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"   ✅ Table '{table}' migrée avec succès")
                except Exception as e:
                    error_msg = str(e)
                    if "does not exist" in error_msg.lower():
                        print(f"   ⚠️  Table '{table}' n'existe pas - ignorée")
                    elif "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                        print(f"   ℹ️  Table '{table}' déjà migrée - ignorée")
                    else:
                        print(f"   ❌ Erreur sur la table '{table}': {error_msg}")
                        db.session.rollback()
                        raise
            
            print("\n" + "=" * 70)
            print("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
            print("=" * 70)
            
            # Vérification
            print("\n📊 VÉRIFICATION...")
            verify_sql = """
                SELECT table_name, column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE column_name = 'region' 
                ORDER BY table_name;
            """
            
            try:
                result = db.session.execute(text(verify_sql))
                rows = result.fetchall()
                
                if rows:
                    print("\n" + "=" * 70)
                    print("📋 État actuel du champ 'region' dans toutes les tables:")
                    print("=" * 70)
                    for row in rows:
                        table, column, dtype, max_length = row
                        status = "✅" if max_length == 200 else "❌"
                        print(f"{status} {table}.{column}: {dtype}({max_length})")
                else:
                    print("⚠️  Aucun champ 'region' trouvé dans la base")
                    
            except Exception as e:
                print(f"⚠️  Impossible de vérifier: {e}")
            
            print("\n" + "=" * 70)
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DE LA MIGRATION: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_region_columns()
