# Guide de déploiement - Flask Spectacles

## ✅ Checklist pré-déploiement

### 1. Sécurité (CRITIQUE)
- [x] SECRET_KEY en variable d'environnement
- [x] Identifiants email en variables d'environnement
- [x] Mode DEBUG désactivé en production
- [x] .gitignore configuré (instance/, .env, uploads/)
- [x] Validation de taille des fichiers (5 MB max)
- [x] Pagination (30 résultats/page)

### 2. Base de données
- [ ] Migrer vers PostgreSQL en production (recommandé)
- [ ] Sauvegardes automatiques configurées
- [ ] Variables d'environnement DATABASE_URL configurée

### 3. Fichiers statiques
- [x] AWS S3 configuré pour les uploads (persistance garantie)
- [x] Fallback local disponible pour développement
- [x] Variables S3_BUCKET, S3_KEY, S3_SECRET, S3_REGION requises en production

### 4. Performance
- [x] Pagination implémentée (30/page)
- [x] Limite upload 5 MB
- [ ] Cache HTTP configuré
- [ ] Compression gzip activée

## 🚀 Déploiement sur différentes plateformes

### Option 1: Heroku (Recommandé pour débuter)

```bash
# 1. Installer Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# 2. Se connecter
heroku login

# 3. Créer l'application
heroku create votre-app-spectacles

# 4. Ajouter PostgreSQL
heroku addons:create heroku-postgresql:mini

# 5. Configurer les variables d'environnement
heroku config:set SECRET_KEY="votre-cle-secrete-longue-et-aleatoire"
heroku config:set ADMIN_USERNAME="admin"
heroku config:set ADMIN_PASSWORD="mot-de-passe-securise"
heroku config:set FLASK_DEBUG="False"

# 6. Configurer email (optionnel)
heroku config:set MAIL_USERNAME="votre-email@gmail.com"
heroku config:set MAIL_PASSWORD="mot-de-passe-application"
heroku config:set MAIL_DEFAULT_SENDER="votre-email@gmail.com"

# 7. Déployer
git push heroku main

# 8. Initialiser la base de données
heroku run python -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all()"

# 9. Ouvrir l'application
heroku open
```

### Option 2: Railway

```bash
# 1. Aller sur railway.app
# 2. Créer nouveau projet depuis GitHub
# 3. Ajouter variables d'environnement dans Settings
# 4. Déploiement automatique à chaque push
```

### Option 3: Render (Configuration actuelle)

```bash
# 1. Aller sur render.com
# 2. New > Web Service
# 3. Connecter votre repo GitHub
# 4. Le fichier render.yaml configure automatiquement le build

# 5. Ajouter ces variables d'environnement dans le dashboard Render:
#    - SECRET_KEY (générer une clé aléatoire)
#    - ADMIN_USERNAME
#    - ADMIN_PASSWORD
#    - DATABASE_URL (si PostgreSQL)

# 6. OBLIGATOIRE - Variables S3 pour la persistance des images:
#    - S3_BUCKET=spectacle-ment-votre
#    - S3_KEY=votre-access-key-id
#    - S3_SECRET=votre-secret-access-key
#    - S3_REGION=eu-west-1

# 7. Vérifier après déploiement:
curl https://votre-app.onrender.com/health
curl https://votre-app.onrender.com/health/s3
```

> ⚠️ **Important**: Sans les variables S3, les images uploadées seront perdues à chaque redéploiement.

### Option 4: VPS (Digital Ocean, AWS, etc.)

```bash
# 1. Installer sur le serveur
sudo apt update
sudo apt install python3-pip python3-venv nginx

# 2. Cloner le projet
git clone votre-repo
cd flask-spectacles

# 3. Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 4. Installer dépendances
pip install -r requirements.txt

# 5. Créer fichier .env avec vos variables

# 6. Configurer Gunicorn + Nginx
# (voir documentation complète selon votre hébergeur)
```

## 🔧 Variables d'environnement OBLIGATOIRES

```bash
SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxx  # Générer avec: python -c "import secrets; print(secrets.token_hex(32))"
ADMIN_USERNAME=admin
ADMIN_PASSWORD=votre-mot-de-passe-fort
DATABASE_URL=postgresql://user:pass@host/db  # Pour PostgreSQL
FLASK_DEBUG=False
```

## 🔧 Variables d'environnement OPTIONNELLES

```bash
# Email
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=mot-de-passe-application
MAIL_DEFAULT_SENDER=votre-email@gmail.com

# Uploads locaux (fallback uniquement)
UPLOAD_FOLDER=instance/uploads

# Port (si nécessaire)
PORT=5000
```

## 🔧 Variables d'environnement AWS S3 (OBLIGATOIRES en production)

```bash
S3_BUCKET=votre-bucket-s3
S3_KEY=AKIA...votre-access-key
S3_SECRET=votre-secret-access-key
S3_REGION=eu-west-1
```

### Vérification de la connexion S3

Après déploiement, tester la connectivité S3 :

```bash
curl https://votre-app.onrender.com/health/s3
```

Réponse attendue :
```json
{"status": "ok", "bucket": "spectacle-ment-votre", "region": "eu-west-1", "message": "S3 connection successful"}
```

## 📝 Configuration Email Gmail

Pour utiliser Gmail:
1. Activer la validation en 2 étapes sur votre compte Google
2. Générer un "Mot de passe d'application":
   - Compte Google > Sécurité > Validation en 2 étapes
   - Mots de passe d'application
   - Sélectionner "Autre" et nommer "Flask Spectacles"
   - Utiliser ce mot de passe dans MAIL_PASSWORD

## 🔒 Sécurité post-déploiement

1. **Forcer HTTPS** (obligatoire en production)
2. **Configurer les CORS** si vous avez une API
3. **Rate limiting** pour éviter les abus
4. **Monitoring** : configurer des alertes
5. **Backups réguliers** de la base de données
6. **Rotation des secrets** tous les 6 mois

## 🧪 Tests avant déploiement

```bash
# Test local avec mode production
export FLASK_DEBUG=False
export SECRET_KEY="test-key-long"
python app.py

# Vérifier:
# - Pas d'erreurs au démarrage
# - Upload de fichiers fonctionne
# - Pagination fonctionne
# - Login/logout fonctionnent
# - Admin dashboard accessible
```

## 📊 Monitoring recommandé

- **Uptime**: UptimeRobot, Pingdom
- **Logs**: Logentries, Papertrail
- **Erreurs**: Sentry
- **Analytics**: Google Analytics

## 🆘 Troubleshooting

**Erreur "Application error":**
- Vérifier les logs: `heroku logs --tail`
- Vérifier DATABASE_URL est défini
- Vérifier SECRET_KEY est défini

**Uploads ne fonctionnent pas:**
- Vérifier les variables S3 sont configurées : `curl https://votre-app.com/health/s3`
- Vérifier que l'utilisateur IAM a les permissions `PutObject` et `GetObject`
- Vérifier que le bucket existe et est accessible

**Base de données vide:**
- Exécuter les migrations
- L'admin se crée automatiquement au premier démarrage

## 📈 Scalabilité future

1. **Cache Redis** pour les sessions
2. **CDN** pour les assets statiques
3. **Load balancer** si > 10000 utilisateurs
4. **Base de données répliquée**
5. **Queue Celery** pour tâches asynchrones (emails, etc.)

---

**L'application est prête pour le déploiement ! 🚀**
