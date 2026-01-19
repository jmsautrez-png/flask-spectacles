-- ======================================================
-- MIGRATIONS SQL POUR PRODUCTION (PostgreSQL)
-- A executer dans l'ordre via psql ou Render Shell
-- ======================================================

-- Migration 1: Ajouter colonne is_private a demande_animation
ALTER TABLE demande_animation ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE;

-- Migration 2: Ajouter colonne email a users
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Migration 3: Ajouter colonne created_at a users
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Migration 4: Etendre colonne location a 500 caracteres
ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500);

-- Migration 5: Etendre colonne category a 500 caracteres
ALTER TABLE shows ALTER COLUMN category TYPE VARCHAR(500);

-- Migration 6: Ajouter colonne is_event pour distinguer catalogue/evenements
ALTER TABLE shows ADD COLUMN IF NOT EXISTS is_event BOOLEAN DEFAULT FALSE;

-- ======================================================
-- VERIFICATION (optionnel)
-- ======================================================

-- Verifier les colonnes users
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY column_name;

-- Verifier les colonnes demande_animation
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'demande_animation' 
ORDER BY column_name;

-- Verifier les colonnes shows
SELECT column_name, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'shows' 
AND column_name IN ('location', 'category');
