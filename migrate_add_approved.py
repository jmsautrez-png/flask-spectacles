"""
Migration pour ajouter la colonne approved à la table demande_animation.
"""

import sqlite3

def migrate():
    # Connexion à la base de données
    conn = sqlite3.connect('instance/spectacles.db')
    cursor = conn.cursor()
    
    try:
        # Ajouter la colonne approved si elle n'existe pas
        print("Ajout de la colonne approved...")
        cursor.execute("""
            ALTER TABLE demande_animation 
            ADD COLUMN approved BOOLEAN DEFAULT FALSE
        """)
        print("✅ Colonne approved ajoutée.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️ Colonne approved existe déjà.")
        else:
            print(f"❌ Erreur lors de l'ajout de approved: {e}")
    
    # Mettre à jour toutes les cartes privées pour qu'elles ne soient pas approuvées
    # Les cartes publiques existantes sont approuvées par défaut
    print("Mise à jour des cartes existantes...")
    cursor.execute("""
        UPDATE demande_animation 
        SET approved = CASE 
            WHEN is_private = 1 THEN 0
            ELSE 1
        END
        WHERE approved IS NULL
    """)
    print(f"✅ {cursor.rowcount} carte(s) mise(s) à jour.")
    
    # Commit et fermeture
    conn.commit()
    conn.close()
    print("\n✅ Migration terminée avec succès !")

if __name__ == "__main__":
    migrate()
