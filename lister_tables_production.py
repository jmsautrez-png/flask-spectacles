#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour lister toutes les tables en production
"""

from app import create_app, db
from sqlalchemy import text

# Créer l'application
app = create_app()

with app.app_context():
    print("=" * 70)
    print("📋 LISTE DES TABLES EN PRODUCTION")
    print("=" * 70)
    
    # Lister toutes les tables
    result = db.session.execute(
        text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
    ).fetchall()
    
    print(f"\n✅ {len(result)} tables trouvées:\n")
    for row in result:
        print(f"   - {row[0]}")
    
    print("\n" + "=" * 70)
    print("RECHERCHE DE LA TABLE UTILISATEUR")
    print("=" * 70)
    
    # Essayer de trouver la table avec les colonnes is_admin
    for table_name in [row[0] for row in result]:
        try:
            columns_result = db.session.execute(
                text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
            ).fetchall()
            
            columns = [col[0] for col in columns_result]
            
            if 'is_admin' in columns or 'username' in columns:
                print(f"\n✅ Table probable pour users: {table_name}")
                print(f"   Colonnes: {', '.join(columns)}")
        except:
            pass
    
    print("\n" + "=" * 70)
