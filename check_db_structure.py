#!/usr/bin/env python3
"""Vérifier la structure de la table demande_animation"""

from app import create_app
from models.models import db

app = create_app()

with app.app_context():
    result = db.session.execute(db.text('PRAGMA table_info(demande_animation)')).fetchall()
    
    print("=" * 70)
    print("STRUCTURE DE LA TABLE demande_animation")
    print("=" * 70)
    
    for row in result:
        print(f"{row[0]}: {row[1]} ({row[2]}) - Null:{row[3]} - Default:{row[4]}")
    
    print("\n" + "=" * 70)
    
    # Vérifier si la colonne approved existe
    columns = [row[1] for row in result]
    if 'approved' in columns:
        print("✅ La colonne 'approved' existe")
    else:
        print("❌ La colonne 'approved' N'EXISTE PAS")
        print("\nAjout de la colonne...")
        try:
            db.session.execute(db.text('ALTER TABLE demande_animation ADD COLUMN approved BOOLEAN DEFAULT 0'))
            db.session.commit()
            print("✅ Colonne ajoutée avec succès !")
        except Exception as e:
            print(f"❌ Erreur: {e}")
