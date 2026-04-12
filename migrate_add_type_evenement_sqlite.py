#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration SQLite : Ajout du champ type_evenement à la table demande_animation
Pour base de données SQLite locale uniquement
"""

from app import create_app, db
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    print("=" * 70)
    print("🔧 MIGRATION SQLITE : Ajout colonne type_evenement")
    print("=" * 70)
    
    # Vérifier si la colonne existe déjà
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('demande_animation')]
    
    if 'type_evenement' in columns:
        print("\n✅ La colonne 'type_evenement' existe déjà !")
        print("\n📊 Colonnes actuelles:", columns)
    else:
        print("\n⚠️  La colonne 'type_evenement' n'existe pas. Ajout en cours...")
        
        # Ajouter la colonne (SQLite syntax)
        try:
            db.session.execute(text("""
                ALTER TABLE demande_animation 
                ADD COLUMN type_evenement VARCHAR(200)
            """))
            db.session.commit()
            print("✅ Colonne 'type_evenement' ajoutée avec succès !")
            
            # Mettre à jour les anciennes demandes avec une valeur par défaut
            result = db.session.execute(text("""
                UPDATE demande_animation 
                SET type_evenement = 'Non précisé' 
                WHERE type_evenement IS NULL
            """))
            db.session.commit()
            print(f"✅ {result.rowcount} lignes mises à jour avec 'Non précisé'")
            
            # Vérifier le résultat
            inspector = inspect(db.engine)
            new_columns = [c['name'] for c in inspector.get_columns('demande_animation')]
            print("\n📊 Colonnes après migration:", new_columns)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur lors de la migration: {e}")
            raise
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION TERMINÉE")
    print("=" * 70)
