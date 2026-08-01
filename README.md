
# Flask Spectacles — spectacleanimation.fr

Plateforme de mise en relation entre organisateurs d'événements (mairies, écoles, CSE) et artistes du spectacle vivant.

## 🚀 Installation Locale

```bash
# 1. Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Installer dépendances
pip install -r requirements.txt

# 3. Initialiser la base de données
python init_db.py
```

## ⚙️ Configuration (optionnel)

Créer un fichier `.env` à la racine :

```bash
SECRET_KEY="votre-cle-secrete-aleatoire"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="motdepasse-solide"

# S3 (optionnel, pour stockage images)
S3_BUCKET="votre-bucket"
S3_KEY="AKIA..."
S3_SECRET="votre-secret"
S3_REGION="eu-west-1"

# Option perf image (CloudFront recommandé)
S3_CUSTOM_DOMAIN="dxxxxxxxxxxxx.cloudfront.net"
S3_USE_PRESIGNED_URLS="False"
IMAGE_CACHE_CONTROL="public, max-age=31536000, immutable"
```

## ⚡ Chargement photo instantané (AWS)

Pour obtenir un affichage quasi immédiat des photos, utiliser des URLs stables (CloudFront/S3) + cache long.

Variables Render à définir sur le service web :

- `S3_CUSTOM_DOMAIN` : domaine CloudFront (ex: `dxxxxxxxxxxxx.cloudfront.net`)
- `S3_USE_PRESIGNED_URLS` : `False`
- `IMAGE_CACHE_CONTROL` : `public, max-age=31536000, immutable`

Comportement applicatif déjà en place :

- URLs publiques stables via `S3_CUSTOM_DOMAIN` (ou fallback S3 public)
- Cache-Control appliqué à l'upload des originaux et des thumbnails
- Fallback automatique en URL signée si le mode public n'est pas activé

Checklist AWS minimale :

1. Créer une distribution CloudFront avec le bucket S3 en origin.
2. Configurer l'accès privé du bucket via OAC/OAI (recommandé) ou policy publique contrôlée.
3. Vérifier que `https://<S3_CUSTOM_DOMAIN>/thumb_<fichier>.webp` répond en 200.
4. Déployer sur Render avec les variables ci-dessus.
5. Purger le cache CloudFront si nécessaire après migration.

## 🏃 Lancer en Développement

```bash
python app.py
# Ouvrir http://127.0.0.1:5000
```

## 🌐 Déploiement Production (Render)

Voir le guide complet : **[GUIDE_DEPLOIEMENT_RENDER.md](GUIDE_DEPLOIEMENT_RENDER.md)**

**Quick Start Production :**

1. Créer PostgreSQL sur Render
2. Créer Web Service (Python)
3. Configurer variables d'environnement
4. Déployer : `git push`
5. Initialiser DB : `python init_db.py`

## 🛠️ Scripts Utiles

```bash
# Vérifier environnement production
python check_production.py

# Initialiser base de données
python init_db.py

# Lister les tables
python list_tables.py

# Migrations
python migrate_add_photos.py
python migrate_all.py
```

## 📁 Structure Projet

```
flask-spectacles/
├── app.py                    # Application Flask principale
├── config.py                 # Configuration
├── requirements.txt          # Dépendances Python
├── gunicorn_config.py       # Config serveur production
├── render.yaml              # Config déploiement Render
├── models/
│   └── models.py            # Modèles SQLAlchemy (User, Show, etc.)
├── templates/               # Templates Jinja2
├── static/                  # CSS, JS, images statiques
└── GUIDE_DEPLOIEMENT_RENDER.md  # Guide déploiement complet
```

## 🔐 Sécurité

- ✅ CSRF Protection (Flask-WTF)
- ✅ Rate Limiting (Flask-Limiter)
- ✅ Security Headers (Flask-Talisman)
- ✅ Password Hashing (Werkzeug)
- ✅ SQL Injection Protection (SQLAlchemy ORM)

## 📊 Fonctionnalités

### Public
- Catalogue spectacles avec recherche/filtres
- Pages thématiques (magiciens, clowns, marionnettes...)
- Formulaire demande d'animation (mairies/écoles)
- Abonnement compagnie (services administratifs)

### Artistes/Compagnies
- Inscription gratuite
- Publication spectacles (3 photos max)
- Dashboard gestion spectacles
- Visibilité base 60k contacts

### Admin
- Dashboard administration
- Validation spectacles
- Gestion demandes animations
- Statistiques

## 🌍 URLs Production

- **Site** : https://spectacleanimation.fr
- **Admin** : https://spectacleanimation.fr/admin
- **Health Check** : https://spectacleanimation.fr/health

## 📞 Support

Pour toute question :
- Consulter [GUIDE_DEPLOIEMENT_RENDER.md](GUIDE_DEPLOIEMENT_RENDER.md)
- Voir les logs : Render Dashboard → Logs
- Vérifier santé : `/health`, `/health/full`, `/health/s3`

