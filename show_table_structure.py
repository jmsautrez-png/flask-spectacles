import sqlite3

DB_PATH = 'instance/spectacles.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Affiche la structure de la table shows
c.execute("PRAGMA table_info(shows);")
print("Structure de la table 'shows':")
for row in c.fetchall():
    print(row)

conn.close()
