-- Migration PostgreSQL : Ajout de la colonne approved pour le système de validation des appels d'offre
-- Date : 2026-04-09
-- Objectif : Empêcher la publication automatique des appels d'offre sans validation admin

-- Étape 1 : Ajouter la colonne approved avec valeur par défaut FALSE
ALTER TABLE demande_animation 
ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT FALSE;

-- Étape 2 : Mettre à jour les cartes existantes
-- Les cartes privées restent non approuvées (approved = FALSE)
-- Les cartes publiques existantes sont marquées comme approuvées (approved = TRUE)
UPDATE demande_animation 
SET approved = TRUE 
WHERE is_private = FALSE;

-- Étape 3 : Afficher le résultat
SELECT 
    COUNT(*) FILTER (WHERE approved = TRUE) as cartes_approuvees,
    COUNT(*) FILTER (WHERE approved = FALSE) as cartes_en_attente,
    COUNT(*) as total
FROM demande_animation;
