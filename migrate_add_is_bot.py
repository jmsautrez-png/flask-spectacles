#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration : Ajouter la colonne is_bot à visitor_log pour détecter les robots/crawlers
Date : 30 mars 2026
"""

import sys
from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    """Ajoute la colonne is_bot à la table visitor_log"""
    app = create_app()
    
    with app.app_context():
        try:
            # Vérifier si la colonne existe déjà (SQLite)
            check_query = text("PRAGMA table_info(visitor_log)")
            
            result = db.session.execute(check_query).fetchall()
            columns = [row[1] for row in result]  # row[1] contient le nom de la colonne
            
            if 'is_bot' in columns:
                print("✓ La colonne 'is_bot' existe déjà dans visitor_log")
                return
            
            print("📝 Ajout de la colonne is_bot à visitor_log...")
            
            # Ajouter la colonne is_bot (BOOLEAN, default FALSE)
            db.session.execute(text("""
                ALTER TABLE visitor_log 
                ADD COLUMN is_bot BOOLEAN DEFAULT 0 NOT NULL
            """))
            
            # Créer un index pour optimiser les requêtes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_visitor_log_is_bot 
                ON visitor_log(is_bot)
            """))
            
            # Mettre à jour les anciens enregistrements pour détecter les bots
            print("🔄 Mise à jour des anciens enregistrements...")
            
            # Marquer comme bots basé sur le User-Agent
            db.session.execute(text("""
                UPDATE visitor_log 
                SET is_bot = 1
                WHERE LOWER(user_agent) LIKE '%bot%'
                   OR LOWER(user_agent) LIKE '%crawler%'
                   OR LOWER(user_agent) LIKE '%spider%'
                   OR LOWER(user_agent) LIKE '%scraper%'
                   OR LOWER(user_agent) LIKE '%wget%'
                   OR LOWER(user_agent) LIKE '%curl%'
                   OR LOWER(user_agent) LIKE '%python%'
            """))
            
            # Marquer comme bots basé sur l'ISP (datacenters)
            db.session.execute(text("""
                UPDATE visitor_log 
                SET is_bot = 1
                WHERE (
                    LOWER(isp) LIKE '%amazon%'
                    OR LOWER(isp) LIKE '%aws%'
                    OR LOWER(isp) LIKE '%google cloud%'
                    OR LOWER(isp) LIKE '%microsoft corporation%'
                    OR LOWER(isp) LIKE '%tencent%'
                    OR LOWER(isp) LIKE '%alibaba%'
                )
                AND (
                    user_agent NOT LIKE '%Chrome%'
                    AND user_agent NOT LIKE '%Firefox%'
                    AND user_agent NOT LIKE '%Safari%'
                    AND user_agent NOT LIKE '%Edge%'
                )
            """))
            
            db.session.commit()
            
            # Afficher les statistiques
            total_visitors = db.session.execute(text("SELECT COUNT(*) FROM visitor_log")).scalar()
            total_bots = db.session.execute(text("SELECT COUNT(*) FROM visitor_log WHERE is_bot = 1")).scalar()
            total_humans = total_visitors - total_bots
            
            print(f"\n✅ Migration réussie !")
            print(f"📊 Statistiques :")
            print(f"   - Total visiteurs: {total_visitors}")
            print(f"   - Robots détectés: {total_bots} ({total_bots*100//total_visitors if total_visitors > 0 else 0}%)")
            print(f"   - Humains: {total_humans} ({total_humans*100//total_visitors if total_visitors > 0 else 0}%)")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    migrate()
