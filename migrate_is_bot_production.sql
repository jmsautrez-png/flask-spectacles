-- Migration PostgreSQL : Ajouter colonne is_bot à visitor_log
-- Date : 30 mars 2026
-- À exécuter directement sur la base de données PostgreSQL de production

-- 1. Ajouter la colonne is_bot
ALTER TABLE visitor_log 
ADD COLUMN is_bot BOOLEAN DEFAULT FALSE NOT NULL;

-- 2. Créer un index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_visitor_log_is_bot 
ON visitor_log(is_bot);

-- 3. Marquer comme bots basé sur le User-Agent
UPDATE visitor_log 
SET is_bot = TRUE 
WHERE LOWER(user_agent) LIKE '%bot%'
   OR LOWER(user_agent) LIKE '%crawler%'
   OR LOWER(user_agent) LIKE '%spider%'
   OR LOWER(user_agent) LIKE '%scraper%'
   OR LOWER(user_agent) LIKE '%wget%'
   OR LOWER(user_agent) LIKE '%curl%'
   OR LOWER(user_agent) LIKE '%python%'
   OR LOWER(user_agent) LIKE '%go-http%';

-- 4. Marquer comme bots basé sur l'ISP (datacenters sans navigateur)
UPDATE visitor_log 
SET is_bot = TRUE 
WHERE (
    LOWER(isp) LIKE '%amazon%'
    OR LOWER(isp) LIKE '%aws%'
    OR LOWER(isp) LIKE '%google cloud%'
    OR LOWER(isp) LIKE '%microsoft corporation%'
    OR LOWER(isp) LIKE '%tencent%'
    OR LOWER(isp) LIKE '%alibaba%'
)
AND (
    user_agent NOT LIKE '%Chrome%'
    AND user_agent NOT LIKE '%Firefox%'
    AND user_agent NOT LIKE '%Safari%'
    AND user_agent NOT LIKE '%Edge%'
);

-- 5. Afficher les statistiques
SELECT 
    COUNT(*) as total_visiteurs,
    SUM(CASE WHEN is_bot = TRUE THEN 1 ELSE 0 END) as robots,
    SUM(CASE WHEN is_bot = FALSE THEN 1 ELSE 0 END) as humains,
    ROUND(100.0 * SUM(CASE WHEN is_bot = TRUE THEN 1 ELSE 0 END) / COUNT(*), 1) as pourcentage_robots
FROM visitor_log;
