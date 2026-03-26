-- Migration : Ajoute la colonne 'is_featured' à la table shows (PostgreSQL)
-- Pour contrôler quels spectacles apparaissent "à la une" sur la page d'accueil

-- Ajouter la colonne is_featured (par défaut FALSE)
ALTER TABLE shows 
ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;

-- Optionnel : Mettre à jour quelques spectacles existants pour les marquer "à la une"
-- Décommentez les lignes suivantes si vous voulez marquer automatiquement les 8 premiers spectacles
-- UPDATE shows 
-- SET is_featured = TRUE 
-- WHERE approved = TRUE 
-- AND id IN (
--     SELECT id FROM shows 
--     WHERE approved = TRUE 
--     ORDER BY display_order ASC, created_at DESC 
--     LIMIT 8
-- );

-- Vérification
SELECT COUNT(*) as total_featured 
FROM shows 
WHERE is_featured = TRUE;
