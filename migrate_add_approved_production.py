#!/usr/bin/env python3
"""
Migration PostgreSQL Production : Ajout colonne approved
Exécuter ce script sur Render pour ajouter la colonne approved à la base de production
"""

import os
import sys

def migrate_production():
    try:
        import psycopg2
        from config import Config
        import os
        
        print("=" * 70)
        print("🔧 MIGRATION POSTGRESQL - Ajout colonne approved")
        print("=" * 70)
        
        # Récupérer l'URL de la base de données
        database_url = os.environ.get("DATABASE_URL")
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        if not database_url:
            print("❌ ERREUR : DATABASE_URL non défini dans l'environnement")
            print("   Cette migration est uniquement pour PostgreSQL de production")
            return False
        
        # Connexion à PostgreSQL
        print("\n📡 Connexion à la base PostgreSQL de production...")
        print(f"   URL: {database_url[:20]}...{database_url[-20:]}")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ Connecté à PostgreSQL\n")
        
        # Étape 1 : Ajouter la colonne
        print("📝 Étape 1/3 : Ajout de la colonne approved...")
        cursor.execute("""
            ALTER TABLE demande_animation 
            ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT FALSE;
        """)
        print("   ✅ Colonne approved ajoutée (ou déjà existante)")
        
        # Étape 2 : Mettre à jour les cartes existantes
        print("\n📝 Étape 2/3 : Mise à jour des cartes existantes...")
        cursor.execute("""
            UPDATE demande_animation 
            SET approved = TRUE 
            WHERE is_private = FALSE;
        """)
        updated_count = cursor.rowcount
        print(f"   ✅ {updated_count} carte(s) publique(s) marquée(s) comme approuvée(s)")
        
        # Étape 3 : Afficher le résultat
        print("\n📝 Étape 3/3 : Vérification...")
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE approved = TRUE) as approuvees,
                COUNT(*) FILTER (WHERE approved = FALSE) as en_attente,
                COUNT(*) as total
            FROM demande_animation;
        """)
        result = cursor.fetchone()
        approuvees, en_attente, total = result
        
        print("\n" + "=" * 70)
        print("📊 RÉSULTAT DE LA MIGRATION")
        print("=" * 70)
        print(f"  ✅ Cartes approuvées :    {approuvees}")
        print(f"  ⏳ Cartes en attente :    {en_attente}")
        print(f"  📦 Total :                {total}")
        print("=" * 70)
        
        # Commit
        conn.commit()
        print("\n✅ Migration committée avec succès !")
        
        # Fermeture
        cursor.close()
        conn.close()
        
        print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS !\n")
        return True
        
    except ImportError as e:
        print(f"❌ ERREUR : Module manquant - {e}")
        print("   Installer psycopg2 avec : pip install psycopg2-binary")
        return False
        
    except Exception as e:
        print(f"\n❌ ERREUR DURANT LA MIGRATION :")
        print(f"   {type(e).__name__}: {e}")
        print("\n💡 Solutions possibles :")
        print("   1. Vérifier que DATABASE_URL est bien configuré")
        print("   2. Vérifier les permissions sur la base de données")
        print("   3. Exécuter le script SQL directement depuis le dashboard Render")
        return False

if __name__ == "__main__":
    success = migrate_production()
    sys.exit(0 if success else 1)
