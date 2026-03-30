# 🚀 Guide de déploiement - Corrections urgentes

## ⚠️ Problème identifié

Erreur 500 sur `/demandes-animation` : la colonne `is_private` n'existe pas en production.

## ✅ Solution : Exécuter les migrations

### Étape 1 : Se connecter au serveur de production

```bash
# Via Render, GitHub Codespaces, ou votre hébergeur
ssh votre-serveur
# OU
render shell votre-service
```

### Étape 2 : Naviguer vers le dossier de l'application

```bash
cd /opt/render/project/src  # Render
# OU
cd /chemin/vers/votre/app    # Autre hébergeur
```

### Étape 3 : Exécuter le script de migration complet

```bash
python migrate_all.py
```

Ce script :
- ✅ Ajoute la colonne `is_private` à `demande_animation`
- ✅ Étend `location` à 500 caractères (pour supporter 10 villes)
- ✅ Étend `category` à 500 caractères (pour supporter 10 catégories)
- ✅ Est sécurisé : peut être exécuté plusieurs fois sans problème
- ✅ Compatible SQLite, PostgreSQL, MySQL/MariaDB

### Étape 4 : Redémarrer l'application

```bash
# Render
render deploy

# Autre hébergeur avec systemd
sudo systemctl restart votre-app

# Autre hébergeur avec PM2
pm2 restart votre-app
```

## 📋 Vérification post-déploiement

1. Accéder à `https://spectacleanimation.fr/demandes-animation`
2. Vérifier qu'il n'y a plus d'erreur 500
3. Tester l'ajout de plusieurs villes dans un spectacle (panneau admin)

## 🔧 Scripts de migration individuels (si nécessaire)

Si vous préférez exécuter les migrations séparément :

```bash
# 1. Ajouter is_private
python add_is_private_column.py

# 2. Étendre location
python migrate_increase_location_size.py

# 3. Étendre category
python migrate_increase_category_size.py
```

## 📝 Modifications apportées

### Base de données
- `demande_animation.is_private` : nouvelle colonne BOOLEAN (défaut: FALSE)
- `shows.location` : VARCHAR(200) → VARCHAR(500)
- `shows.category` : VARCHAR(80) → VARCHAR(500)

### Interface utilisateur
- Limite de 6 → 10 villes/régions/catégories
- Validation JavaScript pour alerter l'utilisateur
- Messages d'aide mis à jour

## 🆘 En cas de problème

Si l'erreur persiste après la migration :

1. Vérifier les logs du serveur :
   ```bash
   render logs --tail
   # OU
   tail -f /var/log/votre-app/error.log
   ```

2. Vérifier que la migration s'est bien exécutée :
   ```bash
   python -c "from app import app, db; from sqlalchemy import inspect; \
   with app.app_context(): \
       inspector = inspect(db.engine); \
       cols = [c['name'] for c in inspector.get_columns('demande_animation')]; \
       print('is_private' in cols)"
   ```
   Résultat attendu : `True`

3. Si la base de données est PostgreSQL et que la migration échoue, essayez :
   ```bash
   python -c "from app import app, db; from sqlalchemy import text; \
   with app.app_context(): \
       db.session.execute(text('ALTER TABLE demande_animation ADD COLUMN is_private BOOLEAN DEFAULT FALSE')); \
       db.session.commit(); \
       print('✅ Migration manuelle réussie')"
   ```

## 📞 Support

En cas de problème persistant, vérifiez :
- Les permissions de la base de données
- La version de SQLAlchemy (doit être >= 2.0)
- Les logs d'erreur détaillés
