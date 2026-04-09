# 🚀 MIGRATION PRODUCTION - Ajout de la colonne approved

## ⚠️ PROBLÈME ACTUEL

La colonne `approved` existe dans le code mais **pas dans la base PostgreSQL de production**.
Cela provoque des erreurs 500 sur le site en production :
```
column "approved" of relation "demande_animation" does not exist
```

## ✅ SOLUTION : Exécuter la migration sur PostgreSQL

### MÉTHODE 1 : Via le Dashboard Render (RECOMMANDÉ)

1. **Se connecter au dashboard Render** : https://dashboard.render.com/

2. **Aller dans votre service PostgreSQL** :
   - Cliquez sur votre base de données PostgreSQL
   - Cliquez sur l'onglet **"Shell"** ou **"Connect"**

3. **Copier et exécuter le SQL suivant** :

```sql
-- Ajouter la colonne approved
ALTER TABLE demande_animation 
ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT FALSE;

-- Mettre à jour les cartes existantes (publiques = approuvées)
UPDATE demande_animation 
SET approved = TRUE 
WHERE is_private = FALSE;

-- Vérifier le résultat
SELECT 
    COUNT(*) FILTER (WHERE approved = TRUE) as cartes_approuvees,
    COUNT(*) FILTER (WHERE approved = FALSE) as cartes_en_attente,
    COUNT(*) as total
FROM demande_animation;
```

4. **Vérifier** : Le script devrait afficher le nombre de cartes approuvées/en attente

### MÉTHODE 2 : Via SSH sur Render

1. **Se connecter en SSH** à votre service web Render

2. **Exécuter le script de migration** :
```bash
cd /opt/render/project/src
python migrate_add_approved_production.py
```

### MÉTHODE 3 : Via psql en local (si vous avez les credentials)

```bash
psql $DATABASE_URL -f migrate_add_approved_postgres.sql
```

## 🔍 VÉRIFICATION POST-MIGRATION

Une fois la migration exécutée :

1. **Tester la création d'un appel d'offre** via le formulaire public
2. **Vérifier dans l'admin** que la carte apparaît avec le badge "⏳ EN ATTENTE"
3. **Cliquer sur "Approuver et publier"**
4. **Vérifier l'email de confirmation** envoyé au créateur
5. **Vérifier sur le site public** que la carte est maintenant visible

## 📋 FICHIERS CRÉÉS

- `migrate_add_approved_postgres.sql` : Script SQL pur pour PostgreSQL
- `migrate_add_approved_production.py` : Script Python pour exécuter la migration
- `migrate_add_approved.py` : Script SQLite (déjà exécuté en local)

## 🎯 RÉSULTAT ATTENDU

Après la migration :
- ✅ Les appels d'offre publics existants seront marqués `approved = TRUE`
- ✅ Les nouvelles demandes seront créées avec `approved = FALSE`
- ✅ Vous devrez les approuver manuellement avant publication
- ✅ Un email sera envoyé au créateur lors de l'approbation
