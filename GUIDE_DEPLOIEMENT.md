# 🚀 Guide de Déploiement - Spectacle'ment Votre

Ce guide vous accompagne pour déployer l'application en production.

## 📋 Prérequis

- Python 3.10+ installé
- Git installé
- Un compte sur une plateforme de déploiement (Heroku, Railway, Render, etc.)
- Fichiers d'images pour le SEO (voir section Images)

## 🔧 Configuration avant déploiement

### 1. Variables d'environnement

Créez un fichier `.env` basé sur `.env.example` avec VOS vraies valeurs :

```bash
# IMPORTANT: Générer une clé secrète forte
SECRET_KEY=votre-cle-super-longue-et-aleatoire-generee-avec-secrets

# Identifiants admin
ADMIN_USERNAME=votre_admin
ADMIN_PASSWORD=MotDePasseTresFort123!

# Base de données (PostgreSQL en production)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Configuration Flask
FLASK_ENV=production
PORT=5000

# Email (optionnel mais recommandé)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=mot-de-passe-application
```

**⚠️ IMPORTANT**: Ne JAMAIS commiter le fichier `.env` sur Git !

### 2. Générer une SECRET_KEY sécurisée

```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Images requises

Créez ces fichiers dans `static/img/` :

- `favicon.ico` (format ICO)
- `favicon-16x16.png` (16x16 pixels)
- `favicon-32x32.png` (32x32 pixels)
- `apple-touch-icon.png` (180x180 pixels)
- `default-og.jpg` (1200x630 pixels) - Image par défaut pour les réseaux sociaux

**Outils recommandés** :
- [Favicon.io](https://favicon.io/) - Générateur de favicon gratuit
- [Canva](https://canva.com) - Pour créer l'image Open Graph

## 🌐 Déploiement sur Heroku

### Installation Heroku CLI

```bash
# Windows (avec Chocolatey)
choco install heroku-cli

# macOS
brew install heroku/brew/heroku

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

### Déploiement

```bash
# 1. Connexion
heroku login

# 2. Créer l'application
heroku create nom-de-votre-app

# 3. Ajouter PostgreSQL (gratuit)
heroku addons:create heroku-postgresql:mini

# 4. Configurer les variables d'environnement
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY="votre-cle-secrete-generee"
heroku config:set ADMIN_USERNAME="votre_admin"
heroku config:set ADMIN_PASSWORD="MotDePasseSecurise123!"

# 5. Déployer
git push heroku main

# 6. Initialiser la base de données
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 7. Ouvrir l'application
heroku open
```

### Vérifier les logs

```bash
heroku logs --tail
```

## 🚂 Déploiement sur Railway

1. Connectez-vous sur [Railway.app](https://railway.app/)
2. Créez un nouveau projet depuis GitHub
3. Ajoutez une base PostgreSQL
4. Configurez les variables d'environnement dans l'interface
5. Railway déploiera automatiquement !

## 🎨 Déploiement sur Render

1. Connectez-vous sur [Render.com](https://render.com/)
2. New → Web Service
3. Connectez votre repository GitHub
4. Configuration :
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Ajoutez une base PostgreSQL
6. Configurez les variables d'environnement

## 📊 Monitoring et maintenance

### Vérifier la santé de l'application

```bash
curl https://votre-app.com/health
```

Retourne un JSON avec le status de l'application et de la base de données.

### Logs

Les logs sont automatiquement sauvegardés dans `logs/flask-spectacles.log` avec rotation automatique (10 fichiers de 10 MB max).

### Backup de la base de données

```bash
# Créer un backup
python backup_database.py

# Restaurer depuis un backup
python backup_database.py --restore backups/backup_app_20231118_143022.db
```

**💡 Recommandation** : Configurez une tâche automatique (cron job) pour faire des backups quotidiens.

## 🔐 Sécurité en production

L'application inclut automatiquement en production :

✅ HTTPS forcé (via Talisman)  
✅ Headers de sécurité (X-Frame-Options, CSP, etc.)  
✅ Rate limiting contre les attaques brute force  
✅ Protection CSRF  
✅ Cookies sécurisés (HttpOnly, Secure, SameSite)  
✅ Validation des fichiers uploadés  
✅ Détection de requêtes suspectes  

### Recommandations supplémentaires

1. **Firewall** : Activez le firewall de votre hébergeur
2. **SSL/TLS** : Utilisez Let's Encrypt (gratuit) ou le certificat de votre hébergeur
3. **Monitoring** : Configurez des alertes (Sentry, Datadog, etc.)
4. **Backups** : Planifiez des backups automatiques quotidiens
5. **Mises à jour** : Gardez les dépendances à jour

## 🔄 Mise à jour de l'application

```bash
# 1. Faire un backup de la BDD
python backup_database.py

# 2. Récupérer les dernières modifications
git pull origin main

# 3. Installer les nouvelles dépendances
pip install -r requirements.txt

# 4. Redémarrer l'application
# Sur Heroku:
heroku restart

# Sur un serveur:
sudo systemctl restart votre-app
```

## 📈 Optimisations de performance

L'application inclut :

- ✅ Compression Gzip automatique
- ✅ Pool de connexions PostgreSQL optimisé
- ✅ Pagination des résultats (30 par page)
- ✅ Validation de taille des fichiers (max 5 MB)

### CDN (optionnel)

Pour de meilleures performances, utilisez un CDN comme Cloudflare pour servir les fichiers statiques.

## 🆘 Dépannage

### L'application ne démarre pas

1. Vérifiez les logs : `heroku logs --tail`
2. Vérifiez que toutes les variables d'environnement sont définies
3. Vérifiez que PostgreSQL est bien configuré

### Erreur de base de données

```bash
# Réinitialiser la base (⚠️ efface toutes les données)
heroku pg:reset DATABASE_URL --confirm nom-de-votre-app
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Problèmes de performance

1. Vérifiez les logs pour identifier les requêtes lentes
2. Ajoutez des index sur les colonnes fréquemment requêtées
3. Augmentez les ressources de votre hébergeur si nécessaire

## 📞 Support

Pour toute question, consultez :
- Documentation Flask : https://flask.palletsprojects.com/
- Documentation SQLAlchemy : https://docs.sqlalchemy.org/
- Votre plateforme d'hébergement

## ✅ Checklist avant mise en production

- [ ] Variables d'environnement configurées
- [ ] SECRET_KEY générée de manière sécurisée
- [ ] PostgreSQL configuré (pas SQLite en production)
- [ ] Images favicon/OG créées
- [ ] FLASK_ENV=production défini
- [ ] Backups automatiques configurés
- [ ] Monitoring/alertes configurés
- [ ] SSL/HTTPS activé
- [ ] Domaine personnalisé configuré (optionnel)
- [ ] Tests effectués en environnement de staging
- [ ] Documentation mise à jour

🎉 **Félicitations ! Votre application est prête pour la production !**
