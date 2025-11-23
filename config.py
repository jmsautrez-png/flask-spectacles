# ---------------------------------------------
# Adresse email admin utilisée pour l'envoi des mails
# Toutes les notifications administratives seront envoyées à :
# artemisiacompagnie@gmail.com
# ---------------------------------------------
import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    INSTANCE_PATH = os.environ.get("INSTANCE_PATH", None)
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "static/uploads")

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

    BASE_DIR = Path(__file__).resolve().parent
    
    # Configuration de la base de données
    # En production, utiliser PostgreSQL via DATABASE_URL
    # En développement, SQLite par défaut
    database_url = os.environ.get("DATABASE_URL")
    
    # Heroku utilise postgres:// mais SQLAlchemy nécessite postgresql://
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Vérifie la connexion avant utilisation
        "pool_recycle": 300,     # Recycle les connexions après 5 minutes
    }

    # Configuration Email (variables d'environnement recommandées en production)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "False") == "True"
    # Adresse email admin fixée
    MAIL_USERNAME = "artemisiacompagnie@gmail.com"
    MAIL_PASSWORD = "ouzd fafg akwu ulwd"  # Mot de passe d'application Gmail
    MAIL_DEFAULT_SENDER = "artemisiacompagnie@gmail.com"
    # Affichage de l'adresse email utilisée pour l'envoi des mails
    print(f"[CONFIG] MAIL_DEFAULT_SENDER utilisé : {MAIL_DEFAULT_SENDER}")

    # Limite de taille des fichiers (5 MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB en bytes
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB en bytes
    
    # Sécurité sessions
    PERMANENT_SESSION_LIFETIME = 3600  # 1 heure
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # En production, forcer HTTPS
    if os.environ.get("FLASK_ENV") == "production":
        SESSION_COOKIE_SECURE = True