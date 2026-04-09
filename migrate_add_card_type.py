"""
Migration pour ajouter les colonnes card_type et is_validated à la table demande_animation.
"""

import sqlite3

def migrate():
    # Connexion à la base de données
    conn = sqlite3.connect('instance/spectacles.db')
    cursor = conn.cursor()
    
    try:
        # Ajouter la colonne card_type si elle n'existe pas
        print("Ajout de la colonne card_type...")
        cursor.execute("""
            ALTER TABLE demande_animation 
            ADD COLUMN card_type VARCHAR(50) DEFAULT 'admin_email'
        """)
        print("✅ Colonne card_type ajoutée.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️ Colonne card_type existe déjà.")
        else:
            print(f"❌ Erreur lors de l'ajout de card_type: {e}")
    
    try:
        # Ajouter la colonne is_validated si elle n'existe pas
        print("Ajout de la colonne is_validated...")
        cursor.execute("""
            ALTER TABLE demande_animation 
            ADD COLUMN is_validated BOOLEAN DEFAULT TRUE
        """)
        print("✅ Colonne is_validated ajoutée.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️ Colonne is_validated existe déjà.")
        else:
            print(f"❌ Erreur lors de l'ajout de is_validated: {e}")
    
    # Mettre à jour toutes les cartes existantes pour qu'elles soient admin_email et validées
    print("Mise à jour des cartes existantes...")
    cursor.execute("""
        UPDATE demande_animation 
        SET card_type = 'admin_email', is_validated = TRUE
        WHERE card_type IS NULL OR is_validated IS NULL
    """)
    print(f"✅ {cursor.rowcount} carte(s) mise(s) à jour.")
    
    # Commit et fermeture
    conn.commit()
    conn.close()
    print("\n✅ Migration terminée avec succès !")

if __name__ == "__main__":
    migrate()
