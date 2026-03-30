-- Script SQL pour mettre à jour le compteur de visites à 6800
-- À exécuter dans le shell PostgreSQL de Render

-- Vérifier si le compteur existe
SELECT * FROM page_visit WHERE page_name = 'home';

-- Mettre à jour le compteur à 6800
UPDATE page_visit SET visit_count = 6800 WHERE page_name = 'home';

-- Vérifier la mise à jour
SELECT * FROM page_visit WHERE page_name = 'home';
