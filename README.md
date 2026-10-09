
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
```

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

### Matching du public ciblé
- Les fiches et les demandes permettent de cocher plusieurs âges.
- Une catégorie commune et une case d'âge commune suffisent (logique OU).
- Aucun élargissement automatique : une demande « Dès 10 ans » ne reçoit pas
  un spectacle coché seulement « Dès 12 ans » ou « Dès 16 ans ».
- Le comportement sans âge précisé est conservé : la catégorie commune suffit
  si l'un des deux n'a aucune sous-option dans les catégories communes.
- Les règles de compatibilité entre catégories et de petite enfance restent
  inchangées. Le matching historique est conservé pour les demandes sans
  catégories de public.
- Aucune migration ni modification automatique des fiches existantes :
  l'admin peut compléter progressivement les âges réellement adaptés.

## 🌍 URLs Production

- **Site** : https://spectacleanimation.fr
- **Admin** : https://spectacleanimation.fr/admin
- **Health Check** : https://spectacleanimation.fr/health

## 📞 Support

Pour toute question :
- Consulter [GUIDE_DEPLOIEMENT_RENDER.md](GUIDE_DEPLOIEMENT_RENDER.md)
- Voir les logs : Render Dashboard → Logs
- Vérifier santé : `/health`, `/health/full`, `/health/s3`
