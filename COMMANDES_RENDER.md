# 🚀 COMMANDES POUR EXÉCUTER LA MIGRATION SUR RENDER

## Méthode 1 : Avec psql (RECOMMANDÉ)

Copiez-collez cette SEULE commande dans le shell SSH de Render :

```bash
psql $DATABASE_URL -c "ALTER TABLE demande_animation ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT FALSE; UPDATE demande_animation SET approved = TRUE WHERE is_private = FALSE; SELECT COUNT(*) FILTER (WHERE approved = TRUE) as approuvees, COUNT(*) FILTER (WHERE approved = FALSE) as en_attente FROM demande_animation;"
```

## Méthode 2 : Avec le script Python

```bash
python migrate_add_approved_production.py
```

## Méthode 3 : Via le fichier SQL

```bash
psql $DATABASE_URL < migrate_add_approved_postgres.sql
```

---

## ⚠️ ERREUR COMMUNE

❌ **NE PAS** exécuter le SQL directement dans bash :
```bash
ALTER TABLE ...  # ❌ Cela ne marche pas
```

✅ **TOUJOURS** utiliser psql :
```bash
psql $DATABASE_URL -c "ALTER TABLE ..."  # ✅ Correct
```

---

## 🔍 Vérification après migration

Pour vérifier que la colonne a bien été ajoutée :

```bash
psql $DATABASE_URL -c "\d demande_animation"
```

Vous devriez voir la colonne `approved` dans la liste.
