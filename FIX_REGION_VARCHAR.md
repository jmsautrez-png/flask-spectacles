# 🔧 Fix: Erreur "value too long for type character varying(100)"

## ❌ Problème

Lors de la modification d'un spectacle avec plusieurs régions, l'erreur suivante apparaît :

```
sqlalchemy.exc.DataError: (psycopg2.errors.StringDataRightTruncation) 
value too long for type character varying(100)
[SQL: UPDATE shows SET region=%(region)s WHERE shows.id = %(shows_id)s]
[parameters: {'region': 'auvergne-Rhône-Alpes / Bourgogne-Franche-Comté / ...', 'shows_id': 29}]
```

**Cause** : Le champ `region` en base de données PostgreSQL est limité à **100 caractères**, mais certaines valeurs (multi-régions) dépassent cette limite.

## ✅ Solution appliquée

### 1. Mise à jour des modèles Python

Tous les champs `region` dans `models/models.py` ont été étendus de `String(100)` à `String(200)` :

- ✅ `Show.region` : 100 → **200 caractères**
- ✅ `DemandeAnimation.region` : 100 → **200 caractères**  
- ✅ `DemandeEcole.region` : 100 → **200 caractères**
- ✅ `VisitorLog.region` : 100 → **200 caractères**

### 2. Migration SQL pour PostgreSQL

Fichier créé : `migrate_extend_region_column.sql`

```sql
ALTER TABLE shows ALTER COLUMN region TYPE VARCHAR(200);
ALTER TABLE demande_animation ALTER COLUMN region TYPE VARCHAR(200);
ALTER TABLE demande_ecole ALTER COLUMN region TYPE VARCHAR(200);
ALTER TABLE visitor_logs ALTER COLUMN region TYPE VARCHAR(200);
```

### 3. Script Python d'application

Fichier créé : `migrate_extend_region_postgres.py`

## 🚀 Application en production

### Option A: Via Render Shell (Recommandé)

1. Connectez-vous au dashboard Render
2. Allez dans votre service → **Shell**
3. Exécutez :

```bash
python migrate_extend_region_postgres.py
```

### Option B: Via déploiement Git

1. Committez les changements :

```bash
git add models/models.py migrate_extend_region_postgres.py
git commit -m "Fix: Extension du champ region à 200 caractères"
git push origin main
```

2. Une fois déployé, connectez-vous au Shell Render et exécutez :

```bash
python migrate_extend_region_postgres.py
```

### Option C: SQL direct (Avancé)

Si vous avez accès direct à PostgreSQL :

```bash
psql $DATABASE_URL < migrate_extend_region_column.sql
```

## 📊 Vérification

Après la migration, vérifiez que les colonnes ont bien été étendues :

```sql
SELECT table_name, column_name, character_maximum_length 
FROM information_schema.columns 
WHERE column_name = 'region' 
ORDER BY table_name;
```

Vous devriez voir **200** pour toutes les tables.

## 🔄 Test local

Pour tester la migration localement (SQLite) :

```bash
python migrate_extend_region_postgres.py
```

Note : SQLite n'a pas de limite stricte sur VARCHAR, donc cette migration n'a pas d'effet sur SQLite mais ne génère pas d'erreur.

## 📝 Impact

- ✅ **Pas de perte de données** : Extension de colonne seulement
- ✅ **Pas de downtime** : Opération rapide (< 1 seconde)
- ✅ **Rétrocompatible** : Les valeurs < 100 caractères restent inchangées
- ✅ **Prévention** : Évite les erreurs futures pour les multi-régions

## 🎯 Résultat attendu

Après cette migration, vous pourrez sauvegarder des spectacles avec plusieurs régions longues comme :

```
auvergne-Rhône-Alpes / Bourgogne-Franche-Comté / Bretagne / Centre-Val de Loire | Occitanie | Île-de-France
```

Sans erreur de troncature ! ✅
