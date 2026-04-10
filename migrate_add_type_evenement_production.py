#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration PRODUCTION PostgreSQL : Ajout du champ type_evenement
"""

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 70)
    print("🔧 MIGRATION PRODUCTION : Ajout colonne type_evenement")
    print("=" * 70)
    
    # Vérifier si la colonne existe
    check_query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'demande_animation' 
        AND column_name = 'type_evenement'
    """)
    
    result = db.session.execute(check_query).fetchone()
    
    if result:
        print("\n✅ La colonne 'type_evenement' existe déjà !")
    else:
        print("\n⚠️  La colonne 'type_evenement' n'existe pas. Ajout en cours...")
        
        # Ajouter la colonne
        alter_query = text("""
            ALTER TABLE demande_animation 
            ADD COLUMN type_evenement VARCHAR(200)
        """)
        
        db.session.execute(alter_query)
        db.session.commit()
        
        print("✅ Colonne 'type_evenement' ajoutée avec succès !")
        
        # Mettre à jour les anciennes demandes
        update_query = text("""
            UPDATE demande_animation 
            SET type_evenement = 'Non précisé' 
            WHERE type_evenement IS NULL
        """)
        
        db.session.execute(update_query)
        db.session.commit()
        
        print("✅ Anciennes demandes mises à jour")
    
    # Statistiques
    stats_query = text("""
        SELECT 
            COUNT(*) as total,
            COUNT(type_evenement) as avec_type
        FROM demande_animation
    """)
    
    stats = db.session.execute(stats_query).fetchone()
    print(f"\n📊 Statistiques : {stats[0]} demandes totales, {stats[1]} avec type d'événement")
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION TERMINÉE")
    print("=" * 70)
