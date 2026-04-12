-- Migration pour augmenter la taille du champ region dans toutes les tables
-- Appliqué sur PostgreSQL en production
-- Raison: Certaines valeurs de région dépassent 100 caractères (multi-régions)

-- 1. Augmenter region dans la table shows de VARCHAR(100) à VARCHAR(200)
ALTER TABLE shows ALTER COLUMN region TYPE VARCHAR(200);

-- 2. Augmenter region dans la table demande_animation de VARCHAR(100) à VARCHAR(200)
ALTER TABLE demande_animation ALTER COLUMN region TYPE VARCHAR(200);

-- 3. Augmenter region dans la table demande_ecole de VARCHAR(100) à VARCHAR(200)
ALTER TABLE demande_ecole ALTER COLUMN region TYPE VARCHAR(200);

-- 4. Augmenter region dans la table visitor_logs de VARCHAR(100) à VARCHAR(200)
ALTER TABLE visitor_logs ALTER COLUMN region TYPE VARCHAR(200);

-- Vérification (optionnel)
-- SELECT table_name, column_name, data_type, character_maximum_length 
-- FROM information_schema.columns 
-- WHERE column_name = 'region' 
-- ORDER BY table_name;
