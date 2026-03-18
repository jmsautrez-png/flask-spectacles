# 🔧 CORRECTION ERREUR DE DÉPLOIEMENT - Colonne site_internet manquante

## ❌ Problème
```
sqlalchemy.exc.ProgrammingError: column users.site_internet does not exist
```

La colonne `site_internet` a été ajoutée au modèle User mais n'existe pas dans la base de données PostgreSQL en production.

## ✅ Solution

### Option 1 : Via le Shell Render (Recommandé)

1. **Accéder au Shell Render**
   - Aller sur le dashboard Render : https://dashboard.render.com
   - Sélectionner votre service web
   - Cliquer sur "Shell" dans le menu de gauche

2. **Se connecter à PostgreSQL**
   ```bash
   psql $DATABASE_URL
   ```

3. **Exécuter la migration**
   ```sql
   ALTER TABLE users ADD COLUMN IF NOT EXISTS site_internet VARCHAR(255);
   ```

4. **Vérifier que la colonne a été ajoutée**
   ```sql
   SELECT column_name, data_type, character_maximum_length 
   FROM information_schema.columns 
   WHERE table_name = 'users' AND column_name = 'site_internet';
   ```

5. **Quitter psql**
   ```sql
   \q
   ```

6. **Redémarrer le service**
   - Dans le dashboard Render, cliquer sur "Manual Deploy" > "Deploy latest commit"

### Option 2 : Via un script Python au démarrage

Si vous voulez automatiser la migration au démarrage de l'application, vous pouvez utiliser le script `migrate_all.py` qui contient déjà une logique similaire.

### Option 3 : Exécuter toutes les migrations

Si vous voulez être sûr que toutes les migrations sont appliquées :

```bash
# Dans le shell Render, après psql $DATABASE_URL
\i migrations_production.sql
```

## 📝 Fichiers de migration créés

- `migrate_add_user_site_internet_postgres.sql` - Migration SQL standalone
- `migrations_production.sql` - Mis à jour avec la nouvelle migration (#14)

## ⚠️ Important

Après avoir exécuté la migration en production :
- Le déploiement devrait réussir
- Les utilisateurs pourront s'inscrire avec leur site internet
- L'email de bienvenue sera envoyé aux nouveaux inscrits

## 🔍 Vérification

Pour vérifier que tout fonctionne après la migration :

1. Tester une inscription sur : https://votre-site.onrender.com/register
2. Vérifier dans les logs Render qu'il n'y a plus d'erreur
3. Vérifier que l'utilisateur peut se connecter

## 📌 Note

Cette erreur se produit car :
1. La migration a été exécutée en local (SQLite) ✓
2. Le modèle a été mis à jour ✓
3. **Mais la migration n'a pas été exécutée en production (PostgreSQL)** ❌

C'est une situation courante lors du développement. La solution est d'exécuter manuellement la migration SQL en production.
