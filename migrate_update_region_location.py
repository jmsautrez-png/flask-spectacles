import sqlite3
import shutil
import os

# Chemin de la base SQLite
DB_PATH = 'instance/spectacles.db'
BACKUP_PATH = 'instance/spectacles_backup.db'

# Sauvegarde de la base existante
if os.path.exists(DB_PATH):
    shutil.copy(DB_PATH, BACKUP_PATH)
    print(f'Base sauvegardée sous {BACKUP_PATH}')
else:
    print('Base de données non trouvée.')
    exit(1)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Vérifier si la table shows existe
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shows';")
if not c.fetchone():
    print("La table 'shows' n'existe pas.")
    conn.close()
    exit(1)

# Renommer l'ancienne table
c.execute('ALTER TABLE shows RENAME TO shows_old;')

# Créer la nouvelle table avec les bons champs
c.execute('''
CREATE TABLE shows (
    id INTEGER PRIMARY KEY,
    raison_sociale VARCHAR(200),
    title VARCHAR(150) NOT NULL,
    description TEXT,
    region VARCHAR(200),
    location VARCHAR(200),
    category VARCHAR(80),
    date DATE,
    age_range VARCHAR(50),
    file_name VARCHAR(255),
    file_mimetype VARCHAR(120),
    created_at DATETIME,
    approved BOOLEAN,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20)
);
''')

# Copier les données
c.execute('''
INSERT INTO shows (id, raison_sociale, title, description, region, location, category, date, age_range, file_name, file_mimetype, created_at, approved, contact_email, contact_phone)
SELECT id, raison_sociale, title, description, region, location, category, date, age_range, file_name, file_mimetype, created_at, approved, contact_email, contact_phone FROM shows_old;
''')

# Supprimer l'ancienne table
c.execute('DROP TABLE shows_old;')

conn.commit()
conn.close()

print('Migration terminée : champs region et location à 250 caractères.')
