-- Migration : Ajout de la colonne site_internet à la table users
-- À exécuter sur la base de données PostgreSQL de production

-- Ajout de la colonne site_internet
ALTER TABLE users ADD COLUMN IF NOT EXISTS site_internet VARCHAR(255);

-- Vérification
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'site_internet';
