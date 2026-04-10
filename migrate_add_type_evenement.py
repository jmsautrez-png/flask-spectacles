#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration : Ajout du champ type_evenement à la table demande_animation
Pour dissocier le type d'événement (Festival, Arbre de Noël...) du genre de spectacle (Magie, Marionnettes...)
"""

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 70)
    print("🔧 MIGRATION : Ajout colonne type_evenement")
    print("=" * 70)
    
    # Vérifier si la colonne existe déjà
    check_query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'demande_animation' 
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
        
        # Mettre à jour les anciennes demandes avec une valeur par défaut
        update_query = text("""
            UPDATE demande_animation 
            SET type_evenement = 'Non précisé' 
            WHERE type_evenement IS NULL
        """)
        
        db.session.execute(update_query)
        db.session.commit()
        
        print("✅ Anciennes demandes mises à jour avec 'Non précisé'")
    
    # Afficher quelques exemples
    print("\n📋 Exemples de demandes :")
    examples = db.session.execute(
        text("SELECT id, structure, type_evenement, genre_recherche FROM demande_animation LIMIT 5")
    ).fetchall()
    
    for row in examples:
        print(f"   ID {row[0]}: {row[1]} - Événement: {row[2] or 'NULL'} - Spectacle: {row[3]}")
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION TERMINÉE")
    print("=" * 70)
