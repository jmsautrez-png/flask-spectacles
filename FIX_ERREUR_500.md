# 🚨 CORRECTION URGENTE - Erreurs 500 multiples

## Problèmes identifiés

1. ❌ Page `/demandes-animation` → colonne `is_private` manquante
2. ❌ Exports et autres pages → colonnes `email` et `created_at` manquantes dans table `users`
3. ❌ Limitation des villes/catégories → colonnes `location` et `category` trop petites

## Solution rapide (PostgreSQL - Production)

### Via psql ou Render Shell

Connectez-vous à votre base de données et exécutez :

```sql
-- 1. Colonne is_private pour demande_animation
ALTER TABLE demande_animation ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE;

-- 2. Colonnes users (email et created_at)
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 3. Extension colonnes shows (location et category à 500 caractères)
ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500);
ALTER TABLE shows ALTER COLUMN category TYPE VARCHAR(500);
```

### Via Render Dashboard (Alternative)

1. Aller sur https://dashboard.render.com
2. Sélectionner votre service
3. Cliquer sur **Shell**
4. Exécuter :
   ```bash
   python migrate_sql_brut.py
   ```
5. Copier-coller les commandes PostgreSQL affichées
6. Redémarrer : **Manual Deploy** > **Deploy latest commit**

## Vérification

1. ✅ `/demandes-animation` se charge sans erreur
2. ✅ `/admin/export-users-xlsx` fonctionne
3. ✅ Possibilité d'ajouter 10 villes/catégories

## Fichiers à déployer

```bash
git add models/models.py migrate_sql_brut.py FIX_ERREUR_500.md templates/show_form_edit.html
git commit -m "fix: ajouter colonnes manquantes (email, created_at, is_private) et étendre location/category"
git push origin main
```

## Notes

- ⚠️ Ces migrations sont **safe** et ne suppriment aucune donnée
- ⚠️ Compatible **PostgreSQL** en production
- ⏱️ Temps d'exécution : < 10 secondes
