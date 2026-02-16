# Guide de Déploiement Render - spectacleanimation.fr

## 📋 Prérequis

- Compte Render (gratuit ou payant)
- Compte GitHub avec le repo flask-spectacles
- Compte AWS S3 configuré (bucket `spectacle-ment-votre`)
- Variables d'environnement sensibles préparées

---

## 🚀 Étape 1 : Créer la Base de Données PostgreSQL

### Dans le Dashboard Render :

1. **New → PostgreSQL**
2. Remplir :
   - **Name** : `flask-spectacles-db`
   - **Database** : `flask_spectacles`
   - **User** : `flask_user`
   - **Region** : `Frankfurt (EU Central)` (pour la France)
   - **Plan** : `Free` (90 jours) ou `Starter` ($7/mois, persistant)

3. Cliquer **Create Database**
4. ⚠️ **ATTENDRE** que le status passe à **Available** (2-3 minutes)
5. Noter l'**Internal Database URL** (format `postgresql://...`)

---

## 🌐 Étape 2 : Créer le Service Web

### Dans le Dashboard Render :

1. **New → Web Service**
2. Connecter votre repo GitHub `flask-spectacles`
3. Remplir :
   - **Name** : `flask-spectacles` (ou `spectacleanimation`)
   - **Region** : `Frankfurt (EU Central)`
   - **Branch** : `main` (ou votre branche principale)
   - **Root Directory** : *(laisser vide)*
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn -c gunicorn_config.py app:app`
   - **Plan** : `Free` (pour commencer) ou `Starter` ($7/mois)

---

## 🔐 Étape 3 : Configurer les Variables d'Environnement

Dans **Environment → Environment Variables**, ajouter :

### ✅ Variables Critiques (OBLIGATOIRES)

```bash
# Flask
SECRET_KEY=<générer une valeur aléatoire longue 50+ caractères>
FLASK_ENV=production

# Base de données (lier à la DB créée à l'étape 1)
DATABASE_URL=<sélectionner "flask-spectacles-db" dans le menu déroulant>

# Admin (créer vos identifiants sécurisés)
ADMIN_USERNAME=votreAdminUsername
ADMIN_PASSWORD=votreMotDePasseSécurisé123!

# AWS S3 (vos credentials AWS)
S3_BUCKET=spectacle-ment-votre
S3_KEY=AKIA...votreCléAWS
S3_SECRET=votre+Secret+AWS+Base64
S3_REGION=eu-west-1
```

### 📝 Comment générer SECRET_KEY

```python
# Dans un terminal Python
import secrets
print(secrets.token_urlsafe(50))
# Copier la sortie dans SECRET_KEY
```

### ⚠️ Important DATABASE_URL

- **NE PAS copier/coller manuellement** l'URL de la DB
- Utiliser le **menu déroulant** pour sélectionner `flask-spectacles-db`
- Cela crée un lien automatique qui fonctionne avec l'Internal URL

---

## 📦 Étape 4 : Déploiement Initial

1. Cliquer **Create Web Service**
2. Render va :
   - Cloner votre repo
   - Installer les dépendances (`pip install -r requirements.txt`)
   - Démarrer avec Gunicorn
3. Surveiller les **Logs** en temps réel

### ✅ Logs de Succès Attendus

```
==> Build successful 🎉
==> Deploying...
==> Running 'gunicorn -c gunicorn_config.py app:app'
[INFO] Starting gunicorn 25.1.0
[INFO] Listening at: http://0.0.0.0:10000
[INFO] Booting worker with pid: 58
[INFO] Booting worker with pid: 59
==> Your service is live 🎉
```

### ❌ Erreurs Possibles

**"Port scan timeout"** → Vérifier :
- `DATABASE_URL` est bien configurée
- Variables `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` sont définies
- La DB est en status **Available**

**"Application failed to respond"** → Vérifier logs :
- Erreurs Python au démarrage
- Connexion DB impossible
- Variables manquantes

---

## 🗄️ Étape 5 : Initialiser la Base de Données

### Via le Shell Render

1. Dans le dashboard du service web, aller dans **Shell** (onglet en haut)
2. Exécuter les commandes suivantes :

```bash
# Vérifier que Python fonctionne
python --version

# Initialiser la base de données (créer les tables)
python init_db.py

# Vérifier que les tables existent
python - <<EOF
from app import app, db
with app.app_context():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables créées:", tables)
EOF
```

### ✅ Sortie Attendue

```
Tables créées: ['users', 'shows', 'demandes_animation', 'demandes_ecole']
```

### Alternative : Script SQL Direct

Si `init_db.py` échoue, utiliser PostgreSQL direct :

```bash
# Se connecter à la DB
psql $DATABASE_URL

# Créer manuellement les tables
\i migrations_production.sql
\q
```

---

## 🔍 Étape 6 : Vérifications Post-Déploiement

### 1. Health Check

Visiter : `https://votre-service.onrender.com/health`

**Réponse attendue :**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-16T...",
  "version": "1.0.0"
}
```

### 2. Health Check Complet (avec DB)

Visiter : `https://votre-service.onrender.com/health/full`

**Réponse attendue :**
```json
{
  "status": "healthy",
  "database": "ok",
  "timestamp": "2026-02-16T...",
  "version": "1.0.0"
}
```

### 3. Health Check S3

Visiter : `https://votre-service.onrender.com/health/s3`

**Réponse attendue :**
```json
{
  "status": "ok",
  "bucket": "spectacle-ment-votre",
  "region": "eu-west-1",
  "test_object": "health-check/test.txt",
  "message": "S3 connection successful"
}
```

### 4. Page d'Accueil

Visiter : `https://votre-service.onrender.com/`

- Doit charger la page d'accueil avec le catalogue
- Vérifier que les images S3 se chargent
- Tester la recherche

### 5. Connexion Admin

1. Aller sur `/login`
2. Utiliser `ADMIN_USERNAME` et `ADMIN_PASSWORD` configurés
3. Accéder à `/admin`
4. Vérifier que le dashboard fonctionne

---

## 🌍 Étape 7 : Configurer le Domaine Personnalisé

### Dans Render (onglet Settings → Custom Domains)

1. Cliquer **Add Custom Domain**
2. Entrer : `spectacleanimation.fr`
3. Render vous donne des enregistrements DNS à configurer

### Chez votre Registrar DNS (OVH, Cloudflare, etc.)

Ajouter les enregistrements fournis par Render :

**Type A** :
```
@ → 216.24.57.1  (exemple, utiliser l'IP Render)
```

**Type CNAME** :
```
www → votre-service.onrender.com
```

### Attendre la Propagation DNS (15 min - 48h)

Vérifier avec :
```bash
nslookup spectacleanimation.fr
dig spectacleanimation.fr
```

### Une fois propagé

- Render détecte automatiquement le domaine
- Génère un certificat SSL Let's Encrypt (gratuit)
- Redirige HTTP → HTTPS automatiquement

---

## 📊 Étape 8 : Monitoring et Logs

### Logs en Temps Réel

Dans le dashboard Render :
- **Logs** (onglet) → Voir les requêtes HTTP, erreurs Python, etc.
- Filtre par niveau : `INFO`, `WARNING`, `ERROR`

### Métriques

Dans **Metrics** :
- CPU Usage
- Memory Usage
- Request Count
- Response Time

### Alertes (Plan Payant)

Configurer des notifications Slack/Email si :
- Service down
- CPU > 80%
- Erreurs 5xx > seuil

---

## 🔄 Étape 9 : Déploiements Futurs

### Déploiement Automatique (recommandé)

**Settings → Build & Deploy**
- Activer **Auto-Deploy** : `Yes`
- Branche : `main`

Chaque `git push` vers `main` déclenche automatiquement :
1. Build
2. Test
3. Déploiement

### Déploiement Manuel

Dans le dashboard :
- **Manual Deploy** → `Deploy latest commit`
- Surveiller les logs

### Rollback

Si un déploiement échoue :
- **Deployments** (historique)
- Cliquer sur un déploiement précédent
- **Redeploy**

---

## 🛡️ Sécurité et Bonnes Pratiques

### ✅ Checklist Sécurité

- [ ] `SECRET_KEY` généré aléatoirement (50+ caractères)
- [ ] `ADMIN_PASSWORD` fort (12+ caractères, symboles)
- [ ] `S3_KEY` et `S3_SECRET` jamais dans le code
- [ ] `DATABASE_URL` jamais dans le code
- [ ] HTTPS activé (automatique avec Render)
- [ ] CSRF protection activée (Flask-WTF)
- [ ] Rate limiting activé (Flask-Limiter)
- [ ] Talisman activé (en-têtes sécurité)

### 🔐 Sauvegardes Base de Données

**Plan Free** :
- Base éphémère (90 jours max)
- Sauvegardes manuelles recommandées

**Plan Starter** :
- Sauvegardes automatiques daily
- Rétention 7 jours

### Sauvegarde Manuelle

```bash
# Depuis votre machine locale
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restauration
psql $DATABASE_URL < backup_20260216.sql
```

---

## 🐛 Dépannage

### Service ne démarre pas

**Symptôme** : "Port scan timeout"

**Solutions** :
1. Vérifier `DATABASE_URL` configurée
2. Vérifier variables `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`
3. Consulter les logs Build et Deploy
4. Vérifier `requirements.txt` à jour

### Erreur 500 sur toutes les pages

**Cause probable** : Base de données non initialisée

**Solution** :
```bash
# Via Shell Render
python init_db.py
```

### Images ne se chargent pas

**Cause** : S3 mal configuré ou credentials invalides

**Vérifier** :
1. `/health/s3` → doit retourner `"status": "ok"`
2. Variables `S3_BUCKET`, `S3_KEY`, `S3_SECRET`, `S3_REGION` définies
3. Credentials AWS valides et ayant les permissions S3

**Permissions S3 Requises** :
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ],
    "Resource": [
      "arn:aws:s3:::spectacle-ment-votre",
      "arn:aws:s3:::spectacle-ment-votre/*"
    ]
  }]
}
```

### Performance lente

**Plan Free** :
- Service s'endort après 15 min d'inactivité
- Première requête prend 30-60s (cold start)

**Solution** :
- Passer au plan **Starter** ($7/mois)
- Ou utiliser uptime monitor externe (UptimeRobot, Pingdom)

### Dépassement mémoire

**Symptôme** : Service crash régulièrement

**Solutions** :
1. Réduire `workers` dans `gunicorn_config.py` (actuellement max 4)
2. Optimiser les requêtes DB (indexes, pagination)
3. Passer à un plan avec plus de RAM

---

## 📞 Support

### Documentation Render

- [Render Docs](https://render.com/docs)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [Python on Render](https://render.com/docs/deploy-flask)

### Support Render

- Community Forum : https://community.render.com
- Email : support@render.com

### Logs Détaillés

Pour debug approfondi, activer logs verbose :

**Ajouter variable** :
```bash
LOG_LEVEL=debug
```

Redéployer et consulter les logs.

---

## ✅ Checklist Finale

- [ ] Base PostgreSQL créée et Available
- [ ] Service Web créé et déployé
- [ ] Toutes les variables d'environnement configurées
- [ ] `python init_db.py` exécuté avec succès
- [ ] `/health` retourne 200 OK
- [ ] `/health/full` retourne `"database": "ok"`
- [ ] `/health/s3` retourne `"status": "ok"`
- [ ] Page d'accueil accessible
- [ ] Login admin fonctionne
- [ ] Domaine personnalisé configuré (optionnel)
- [ ] SSL/HTTPS activé
- [ ] Auto-deploy configuré

---

## 🎉 Félicitations !

Votre application **spectacleanimation.fr** est maintenant en production sur Render !

**URLs importantes** :
- Production : `https://spectacleanimation.fr`
- Admin : `https://spectacleanimation.fr/admin`
- Health : `https://spectacleanimation.fr/health`
- Dashboard Render : `https://dashboard.render.com`

**Prochaines étapes** :
1. Tester toutes les fonctionnalités
2. Importer les données spectacles existantes
3. Configurer Google Analytics / Search Console
4. Mettre en place monitoring externe
5. Communiquer la nouvelle URL aux utilisateurs
