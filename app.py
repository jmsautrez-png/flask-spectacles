# Import optionnel de Flask-Mail
try:
    from flask_mail import Mail, Message
except ImportError:
    Mail = None
    Message = None
# Import optionnel de Flask-Talisman
try:
    from flask_talisman import Talisman
except ImportError:
    Talisman = None
import sys

print("PYTHON EXE:", sys.executable)
from sqlalchemy import or_
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import random
import os
import logging
from logging.handlers import RotatingFileHandler

import uuid

# Import global de boto3 pour éviter NameError
try:
    import boto3
except ImportError:
    boto3 = None

# Import optionnel de Flask-Compress
try:
    from flask_compress import Compress
except ImportError:
    Compress = None

# Charger les variables d'environnement du fichier .env
from dotenv import load_dotenv
load_dotenv()


from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    current_app
)

from config import Config
from models import db
from models.models import User, Show

# -----------------------------------------------------
# Logging
# -----------------------------------------------------
def configure_logging(app: Flask) -> None:
    """Configure le système de logging pour l'application"""
    # Créer le dossier logs s'il n'existe pas
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Niveau de log selon l'environnement
    if os.environ.get("FLASK_ENV") == "production":
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    
    app.logger.setLevel(log_level)
    
    # Handler pour fichier (rotation automatique)
    file_handler = RotatingFileHandler(
        log_dir / "flask-spectacles.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    
    # Format des logs
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Handler pour console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Ajouter les handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    app.logger.info("Système de logging initialisé")

# -----------------------------------------------------
# Factory
# -----------------------------------------------------
def _validate_production_config(app: Flask) -> None:
    """Validate critical environment variables in production."""
    import os
    is_production = os.environ.get("FLASK_ENV") == "production"
    
    warnings = []
    errors = []
    
    # Critical: SECRET_KEY must not be the default (TOUJOURS)
    secret_key = app.config.get("SECRET_KEY")
    if not secret_key or secret_key == "dev-secret-key":
        if is_production:
            errors.append("SECRET_KEY is not set or using default value. Set it in environment variables!")
        else:
            warnings.append("SECRET_KEY using default value. Set SECRET_KEY in .env for security.")
    
    # Critical: ADMIN_PASSWORD must be set
    admin_pwd = app.config.get("ADMIN_PASSWORD")
    if not admin_pwd:
        if is_production:
            errors.append("ADMIN_PASSWORD is not set. Set it in environment variables!")
        else:
            warnings.append("ADMIN_PASSWORD not set. Define ADMIN_PASSWORD in .env file.")
    
    # Critical: Database should be PostgreSQL in production
    if is_production:
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "sqlite" in db_uri.lower():
            errors.append("DATABASE_URL not set. Using ephemeral SQLite! Set DATABASE_URL in Render.")
    
    # Warning: Admin credentials using defaults
    if app.config.get("ADMIN_USERNAME") == "admin":
        warnings.append("ADMIN_USERNAME using default 'admin'. Consider setting a custom value.")
    
    # Warning: S3 not fully configured
    s3_vars = ["S3_BUCKET", "S3_KEY", "S3_SECRET", "S3_REGION"]
    missing_s3 = [v for v in s3_vars if not app.config.get(v)]
    if missing_s3:
        warnings.append(f"S3 not fully configured (missing: {', '.join(missing_s3)}). Uploads will use local disk (ephemeral!).")
    
    # Log warnings
    for w in warnings:
        app.logger.warning(f"[CONFIG] ⚠️  {w}")
    
    # Log errors and optionally fail
    for e in errors:
        app.logger.error(f"[CONFIG] ❌ {e}")
    
    if errors:
        app.logger.error("[CONFIG] ❌ CRITICAL CONFIGURATION ERRORS DETECTED. App may not work correctly!")


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(Config)
    import os
    
    # Validate production configuration
    _validate_production_config(app)
    
    app.logger.info("ENV UPLOAD_DIR=%s", os.environ.get("UPLOAD_DIR"))
    app.logger.info("ENV UPLOAD_FOLDER=%s", os.environ.get("UPLOAD_FOLDER"))
    app.logger.info("CONFIG UPLOAD_FOLDER=%s", app.config.get("UPLOAD_FOLDER"))
    app.logger.info("UPLOAD_FOLDER exists? %s", os.path.isdir(app.config.get("UPLOAD_FOLDER", "")))

    # Dossiers nécessaires
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    
    # === LOGGING ===
    configure_logging(app)
    
    # === COMPRESSION ===
    if Compress:
        Compress(app)
        app.logger.info("Compression Gzip activée")

    # DB
    db.init_app(app)

    # === MIGRATION AUTOMATIQUE DES COLONNES MANQUANTES ===
    with app.app_context():
        try:
            # Vérifier et ajouter les colonnes manquantes pour les photos multiples
            columns_to_add = [
                ("file_name2", "VARCHAR(255)"),
                ("file_mimetype2", "VARCHAR(100)"),
                ("file_name3", "VARCHAR(255)"),
                ("file_mimetype3", "VARCHAR(100)"),
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    # Vérifier si la colonne existe
                    db.session.execute(db.text(f"SELECT {col_name} FROM shows LIMIT 1"))
                except Exception:
                    # La colonne n'existe pas, l'ajouter
                    try:
                        db.session.rollback()
                        db.session.execute(db.text(f"ALTER TABLE shows ADD COLUMN {col_name} {col_type}"))
                        db.session.commit()
                        app.logger.info(f"Colonne {col_name} ajoutée à la table shows")
                    except Exception as e:
                        db.session.rollback()
                        app.logger.warning(f"Impossible d'ajouter la colonne {col_name}: {e}")
        except Exception as e:
            app.logger.warning(f"Migration automatique échouée: {e}")

    # === SÉCURITÉ ===
    
    # 1. Protection CSRF (Flask-WTF)
    try:
        from flask_wtf.csrf import CSRFProtect
        csrf = CSRFProtect(app)
        app.csrf = csrf  # type: ignore
        app.logger.info("Protection CSRF activée")
    except Exception as e:
        app.logger.warning(f"Protection CSRF non activée: {e}")
        app.csrf = None  # type: ignore
    
    # 2. Rate Limiting (protection contre attaques brute force)
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        # Limites plus raisonnables et différentes selon l'environnement
        is_production = os.environ.get("FLASK_ENV") == "production"
        
        if is_production:
            # En production : limites strictes
            default_limits = ["10000 per day", "500 per hour", "100 per minute"]
        else:
            # En développement : limites très souples
            default_limits = ["100000 per day", "10000 per hour", "1000 per minute"]
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=default_limits,
            storage_uri="memory://",
            strategy="moving-window"  # Plus précis que fixed-window
        )
        app.limiter = limiter  # type: ignore
        app.logger.info(f"Rate limiting activé: {', '.join(default_limits)}")
    except Exception as e:
        app.logger.warning(f"Rate limiting non activé: {e}")
        app.limiter = None  # type: ignore
    
    # 3. Headers de sécurité (HTTPS, XSS, etc.)
    if Talisman and os.environ.get("FLASK_ENV") == "production":
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            content_security_policy={
                'default-src': "'self'",
                'img-src': ["'self'", "data:"],
                'style-src': ["'self'", "'unsafe-inline'"],
                'script-src': ["'self'", "'unsafe-inline'"],
            },
        )
    
    # 4. Configuration cookies de session (sécurité)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if os.environ.get("FLASK_ENV") == "production":
        app.config["SESSION_COOKIE_SECURE"] = True  # HTTPS uniquement
    
    # 5. Headers de sécurité additionnels
    @app.after_request
    def set_security_headers(response):
        """Ajoute des headers de sécurité à toutes les réponses"""
        # Protection contre le clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Protection contre le sniffing MIME
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Protection XSS pour les anciens navigateurs
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Politique de référent
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy (anciennement Feature-Policy)
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

    # Mail (optionnel)
    if Mail:
        try:
            app.mail = Mail(app)  # type: ignore[attr-defined]
            # NOTE: éviter toute connexion réseau au démarrage (fragilise le déploiement/CI).
            # Si vous voulez tester SMTP, activer explicitement:
            # MAIL_SMTP_TEST_ON_STARTUP=1 (idéalement uniquement en production)
            if os.environ.get("MAIL_SMTP_TEST_ON_STARTUP") == "1":
                if app.config.get("MAIL_USERNAME") and app.config.get("MAIL_PASSWORD"):
                    try:
                        import smtplib
                        server = smtplib.SMTP(app.config.get("MAIL_SERVER"), app.config.get("MAIL_PORT"))
                        if app.config.get("MAIL_USE_TLS"):
                            server.starttls()
                        server.login(app.config.get("MAIL_USERNAME"), app.config.get("MAIL_PASSWORD"))
                        server.quit()
                        print("[MAIL] Connexion SMTP réussie.")
                    except Exception as smtp_error:
                        print(f"[MAIL] Erreur de connexion SMTP: {smtp_error}")
                else:
                    print("[MAIL] Configuration email incomplète : MAIL_USERNAME ou MAIL_PASSWORD manquant.")
        except Exception as e:  # pragma: no cover
            app.mail = None  # type: ignore[attr-defined]
            print("[MAIL] non initialisé:", e)
    else:
        app.mail = None  # type: ignore[attr-defined]

    with app.app_context():
        db.create_all()
        _bootstrap_admin(app)

    # Filtre Jinja2 pour formater les âges
    @app.template_filter('format_age')
    def format_age(value):
        """Formate les valeurs d'âge : enfant_2_10 → enfant 2/10ans"""
        if not value:
            return value
        import re
        # Remplacer enfant_X_Y(ans optionnel) par enfant X/Y
        value = re.sub(r'_(\d+)_(\d+)(ans)?', r' \1/\2', value)
        # Remplacer enfants_X_Y(ans optionnel) par enfants X/Y  
        value = re.sub(r's_(\d+)_(\d+)(ans)?', r's \1/\2', value)
        # Supprimer les underscores restants
        value = value.replace('_', ' ')
        # Ajouter "ans" à la fin si la valeur contient des chiffres et ne se termine pas déjà par "ans"
        if re.search(r'\d', value) and not value.endswith('ans'):
            value += 'ans'
        return value

    # Context processor pour les spectacles à la une (diaporama header)
    @app.context_processor
    def inject_featured_shows():
        """Injecte les spectacles à la une avec images pour le diaporama header"""
        try:
            # Uniquement les spectacles de la catégorie "à la une"
            featured = Show.query.filter(
                Show.approved.is_(True),
                Show.file_mimetype.ilike("image/%"),
                or_(
                    Show.category.ilike('%à la une%'),
                    Show.category.ilike('%a la une%')
                )
            ).order_by(Show.created_at.desc()).all()
            
            return {'header_featured_shows': featured}
        except Exception:
            db.session.rollback()
            return {'header_featured_shows': []}

    register_routes(app)
    register_error_handlers(app)
    return app

# -----------------------------------------------------
# Utilitaires
# -----------------------------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}

def allowed_file(filename: str) -> bool:
    """Vérifie si l'extension du fichier est autorisée"""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def secure_upload_filename(file) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valide et sécurise un fichier uploadé.
    Retourne: (success: bool, error_message: Optional[str], secure_filename: Optional[str])
    """
    from werkzeug.utils import secure_filename as werkzeug_secure_filename
    
    if not file or not file.filename:
        return False, "Aucun fichier fourni", None
    
    # 1. Vérifier l'extension
    if not allowed_file(file.filename):
        return False, f"Type de fichier non autorisé. Extensions acceptées : {', '.join(ALLOWED_EXTENSIONS)}", None
    
    # 2. Sécuriser le nom de fichier (éviter path traversal)
    safe_name = werkzeug_secure_filename(file.filename)
    if not safe_name or safe_name == '':
        return False, "Nom de fichier invalide", None
    
    # 3. Vérifier le MIME type (optionnel, nécessite python-magic)
    # Pour l'instant, on fait confiance à l'extension après werkzeug
    
    return True, None, safe_name

def validate_file_size(file) -> Tuple[bool, Optional[str]]:
    """Valide la taille d'un fichier. Retourne (True, None) si valide, (False, message d'erreur) sinon."""
    if not file:
        return True, None

    # Lire le fichier en mémoire pour vérifier sa taille
    file.seek(0, 2)  # Aller à la fin du fichier
    file_size = file.tell()  # Obtenir la taille
    file.seek(0)  # Revenir au début pour pouvoir le sauvegarder après

    max_size = current_app.config.get("MAX_FILE_SIZE", 5 * 1024 * 1024)  # Par défaut 5 MB

    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        return False, f"Le fichier est trop volumineux ({size_mb:.2f} MB). Taille maximale autorisée : {max_mb:.0f} MB."

    return True, None


# Utilitaire : upload d'un fichier sur S3
def _s3_client():
    """Crée un client S3 si configuré, sinon retourne None."""
    s3_bucket = current_app.config.get("S3_BUCKET")
    s3_key = current_app.config.get("S3_KEY")
    s3_secret = current_app.config.get("S3_SECRET")
    s3_region = current_app.config.get("S3_REGION")
    if not (s3_bucket and s3_key and s3_secret and boto3):
        return None
    return boto3.client(
        "s3",
        region_name=s3_region,
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret,
    )


def delete_file_s3(key: str) -> None:
    """Supprime un objet S3 (best-effort)."""
    s3_bucket = current_app.config.get("S3_BUCKET")
    client = _s3_client()
    if not (client and s3_bucket and key):
        return
    try:
        client.delete_object(Bucket=s3_bucket, Key=key)
        current_app.logger.info("[S3] Fichier supprimé: %s", key)
    except Exception as e:
        current_app.logger.warning("[S3] Suppression impossible (%s): %s", key, e)


def upload_file_to_s3(file) -> str:
    """
    Upload le fichier sur S3 et retourne le nom unique.
    Fallback sur stockage local si S3 n'est pas configuré.
    """
    from pathlib import Path as _Path
    ext = _Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    
    # Vérifier si S3 est configuré
    s3_bucket = current_app.config.get("S3_BUCKET")
    s3_client = _s3_client()

    if s3_client and s3_bucket:
        try:
            # Upload to S3
            s3_client.upload_fileobj(
                file,
                s3_bucket,
                unique_name,
                ExtraArgs={
                    "ContentType": file.content_type or "application/octet-stream"
                }
            )
            current_app.logger.info(f"[S3] Fichier uploadé avec succès: {unique_name}")
            return unique_name
            
        except Exception as e:
            current_app.logger.error(f"[S3] Erreur upload S3, fallback local: {e}")
            # Fallback to local storage
    
    # Fallback: sauvegarde locale
    save_path = _Path(current_app.config["UPLOAD_FOLDER"]) / unique_name
    file.save(save_path.as_posix())
    current_app.logger.info(f"[LOCAL] Fichier sauvegardé localement: {unique_name}")
    return unique_name


# Alias pour rétrocompatibilité
def upload_file_local(file) -> str:
    """Alias vers upload_file_to_s3 pour rétrocompatibilité."""
    return upload_file_to_s3(file)

def current_user() -> Optional[User]:
    username = session.get("username")
    if not username:
        return None
    return User.query.filter_by(username=username).first()

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("username"):
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("Accès réservé à l’administrateur.", "danger")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapper

def _generate_password(n: int = 10) -> str:
    import string, secrets
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def _is_suspicious_request() -> bool:
    """Détecte les requêtes suspectes (bots, scrapers, etc.)"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Liste de bots malveillants connus
    suspicious_agents = [
        'sqlmap', 'nikto', 'nmap', 'masscan', 'netsparker',
        'acunetix', 'burp', 'havij', 'scrapy', 'curl/7',
    ]
    
    for agent in suspicious_agents:
        if agent in user_agent:
            return True
    
    # Pas de User-Agent = suspect
    if not user_agent or user_agent == 'none':
        return True
        
    return False

def _bootstrap_admin(app: Flask) -> None:
    """
    Creates an admin user on first startup if the users table is empty.
    Credentials come from ADMIN_USERNAME and ADMIN_PASSWORD environment variables.
    """
    if User.query.count() == 0:
        username = app.config["ADMIN_USERNAME"]
        password = app.config["ADMIN_PASSWORD"]
        
        admin = User(username=username, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        
        # Clear log message so operator knows what credentials to use
        app.logger.info("=" * 60)
        app.logger.info("[BOOTSTRAP] Admin user created!")
        app.logger.info(f"[BOOTSTRAP]   Username: {username}")
        if password == "admin":
            app.logger.warning("[BOOTSTRAP]   Password: admin (DEFAULT - CHANGE IN RENDER!)")
        else:
            app.logger.info("[BOOTSTRAP]   Password: (set via ADMIN_PASSWORD env var)")
        app.logger.info("=" * 60)

def register_error_handlers(app: Flask) -> None:
    """Enregistre les gestionnaires d'erreurs personnalisés pour l'application"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", user=current_user()), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        # Rollback en cas d'erreur pour libérer la transaction PostgreSQL
        try:
            db.session.rollback()
        except Exception:
            pass
        return render_template("500.html", user=current_user()), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Rollback global pour toute exception non gérée
        try:
            db.session.rollback()
        except Exception:
            pass
        app.logger.exception("Erreur non gérée: %s", e)
        return render_template("500.html", user=current_user()), 500

# -----------------------------------------------------
# Routes
# -----------------------------------------------------
def register_routes(app: Flask) -> None:
    # ---------------------------
    # Route de test d'envoi de mail (à la fin pour éviter les erreurs)
    # ---------------------------
    @app.route("/test-mail")
    def test_mail():
        if not hasattr(app, "mail") or not app.mail:
            return "Mail non configuré.", 500
        try:
            msg = Message(
                subject="Test d'envoi de mail",
                recipients=[app.config.get("MAIL_DEFAULT_SENDER")],
                body="Ceci est un test d'envoi de mail depuis Flask-Spectacles."
            )
            app.mail.send(msg)
            print("[MAIL] Test d'envoi réussi vers :", app.config.get("MAIL_DEFAULT_SENDER"))
            return f"Mail de test envoyé à {app.config.get('MAIL_DEFAULT_SENDER')} !", 200
        except Exception as e:
            print("[MAIL] Test d'envoi échoué :", e)
            return f"Erreur lors de l'envoi du mail : {e}", 500
    # ---------------------------
    # Auth
    # ---------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        # Protection anti-bot
        if _is_suspicious_request():
            flash("Requête suspecte détectée.", "danger")
            return redirect(url_for("home"))
            
        if request.method == "POST":
            # Rate limiting manuel (max 5 tentatives d'inscription par heure depuis la même IP)
            if hasattr(app, 'limiter') and app.limiter:
                try:
                    # Vérifier le rate limit
                    pass  # Géré automatiquement par le décorateur global
                except Exception:
                    flash("Trop de tentatives. Réessayez plus tard.", "warning")
                    return redirect(url_for("register"))
            
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            email = request.form.get("email", "").strip()
            telephone = request.form.get("telephone", "").strip()
            raison_sociale = request.form.get("raison_sociale", "").strip()
            region = request.form.get("region", "").strip()
            site_internet = request.form.get("site_internet", "").strip()

            if not username or not password or not email:
                flash("Veuillez remplir tous les champs obligatoires.", "danger")
                return render_template("register.html")

            # Validation du mot de passe (minimum 6 caractères)
            if len(password) < 6:
                flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
                return render_template("register.html")

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Ce nom d'utilisateur existe déjà.", "warning")
                return render_template("register.html")

            try:
                user = User(
                    username=username,
                    email=email or None,
                    raison_sociale=raison_sociale or None,
                    region=region or None,
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

                # Envoi d'un email à l'admin avec le pédigrée du nouvel utilisateur
                if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                    try:
                        to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                        body = (
                            f"Nouvelle inscription utilisateur :\n\n"
                            f"Nom d'utilisateur : {username}\n"
                            f"Email : {email}\n"
                            f"Téléphone : {telephone}\n"
                            f"Raison sociale : {raison_sociale}\n"
                            f"Région : {region}\n"
                            f"Site internet : {site_internet}\n"
                        )
                        msg = Message(subject="Nouvelle inscription utilisateur", recipients=[to_addr])  # type: ignore[arg-type]
                        msg.body = body  # type: ignore[assignment]
                        current_app.mail.send(msg)  # type: ignore[attr-defined]
                    except Exception as e:
                        print("[MAIL] envoi impossible (inscription):", e)

                flash("Compte créé ! Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for("login"))
            except Exception:
                db.session.rollback()
                flash("Erreur lors de la création du compte.", "danger")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "username" in session:
            u = current_user()
            return redirect(url_for("admin_dashboard" if (u and u.is_admin) else "company_dashboard"))
        
        # Protection anti-bot
        if _is_suspicious_request():
            flash("Requête suspecte détectée.", "danger")
            return redirect(url_for("home"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            
            # Protection contre les injections SQL (SQLAlchemy protège déjà, mais vérifions)
            if any(char in username for char in ["'", '"', ';', '--', '/*']):
                flash("Caractères invalides détectés.", "danger")
                return render_template("login.html", user=current_user())

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["username"] = user.username
                flash("Connecté.", "success")
                
                # Sécuriser la redirection (open redirect fix)
                next_url = request.args.get("next")
                if next_url:
                    # Valider que l'URL est relative (même domaine)
                    from urllib.parse import urlparse
                    parsed = urlparse(next_url)
                    # Accepter uniquement les URLs relatives sans domaine
                    if not parsed.netloc and next_url.startswith('/') and '//' not in next_url:
                        return redirect(next_url)
                
                return redirect(url_for("admin_dashboard" if user.is_admin else "company_dashboard"))

            flash("Identifiants invalides.", "danger")

        return render_template("login.html", user=current_user())

    @app.route("/logout")
    def logout():
        if session.get("username"):
            session.pop("username", None)
            flash("Déconnecté.", "success")
        return redirect(url_for("home"))

    @app.route("/forgot", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            if not username:
                flash("Merci d’entrer votre nom d’utilisateur.", "warning")
                return redirect(url_for("forgot_password"))

            user = User.query.filter_by(username=username).first()
            if not user:
                flash("Si l’utilisateur existe, un nouveau mot de passe a été généré.", "info")
                return redirect(url_for("login"))

            new_pwd = _generate_password(12)
            user.set_password(new_pwd)
            db.session.commit()
            
            # Essayer d'envoyer par email
            email_sent = False
            if getattr(current_app, "mail", None):
                to_email = None
                if hasattr(user, 'shows') and user.shows:
                    for show in user.shows:
                        if show.contact_email:
                            to_email = show.contact_email
                            break
                
                if to_email:
                    try:
                        msg = Message(
                            "Réinitialisation de votre mot de passe",
                            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
                            recipients=[to_email]
                        )
                        msg.body = f"Bonjour {user.username},\\n\\nVotre nouveau mot de passe : {new_pwd}\\n\\nCordialement"
                        current_app.mail.send(msg)
                        current_app.logger.info(f"Email envoyé à {to_email}")
                        email_sent = True
                        flash(f"Un email a été envoyé à {to_email}", "success")
                    except Exception as e:
                        current_app.logger.error(f"Erreur email: {e}")
                else:
                    current_app.logger.warning(f"Pas d'email - MDP {username}: {new_pwd}")
            
            # Afficher le mot de passe sur la page si pas d'email envoyé
            # (ou toujours l'afficher en développement)
            if not email_sent or current_app.config.get("FLASK_ENV") != "production":
                return render_template(
                    "forgot_password.html", 
                    user=current_user(),
                    new_password=new_pwd,
                    reset_user=username
                )
            
            return redirect(url_for("login"))

        return render_template("forgot_password.html", user=current_user())

    # ---------------------------
    # Page des événements annoncés
    # ---------------------------
    @app.route("/evenements", endpoint="evenements")
    def evenements():
        """Affiche les événements annoncés (is_event=True)"""
        try:
            # Tester si la colonne existe
            db.session.execute(db.text("SELECT is_event FROM shows LIMIT 1"))
            shows = Show.query.filter(
                Show.approved.is_(True),
                Show.is_event.is_(True)
            ).order_by(Show.created_at.desc()).all()
        except Exception:
            db.session.rollback()  # Libérer la transaction en échec
            shows = []  # Colonne is_event pas encore créée
        
        return render_template(
            "evenements.html",
            shows=shows,
            user=current_user()
        )

    # ---------------------------
    # Accueil & listing (recherche)
    # ---------------------------
    @app.route("/", endpoint="home")
    def home():
        """Page d'accueil avec les deux blocs hero et le compteur"""
        # Récupérer les spectacles "à la une" pour les afficher
        spectacles_une = Show.query.filter(
            Show.approved == True,
            Show.category.ilike('%Spectacle à la une%'),
        ).order_by(Show.display_order.asc()).limit(8).all()
        
        return render_template(
            "home.html",
            user=current_user(),
            spectacles_une=spectacles_une,
        )

    @app.route("/catalogue", endpoint="catalogue")
    def catalogue():
        """Page catalogue avec les cartes des spectacles"""
        q = request.args.get("q", "", type=str).strip()
        category = request.args.get("category", "", type=str).strip()
        location = request.args.get("location", "", type=str).strip()
        type_filter = request.args.get("type", "all", type=str)
        sort = request.args.get("sort", "asc", type=str)
        date_from = request.args.get("date_from", "", type=str)
        date_to = request.args.get("date_to", "", type=str)
        page = request.args.get("page", 1, type=int)

        shows = Show.query

        # Visibilité publique : non-admin -> seulement approuvés
        u = current_user()
        if not u or not u.is_admin:
            shows = shows.filter(Show.approved.is_(True))

        # Note: Le filtre is_event a été temporairement désactivé
        # Les événements apparaîtront aussi sur la page d'accueil

        # Recherche texte + âges (6, 6 ans, 6-10, 6/10, 6 à 10, etc.)
        if q:
            like = f"%{q}%"

            variants = {q}
            if any(c.isdigit() for c in q):
                cleaned = q.lower().replace("ans", "").strip()
                seps = [" - ", "-", "—", "–", "à", "a", "/", " "]
                norm = cleaned
                for sep in seps:
                    norm = norm.replace(sep, "/")

                variants.update({
                    cleaned,
                    cleaned.replace(" ", ""),
                    cleaned.replace("-", "/"),
                    cleaned.replace("/", "-"),
                    cleaned.replace(" ", "-"),
                    cleaned.replace(" ", "/"),
                    norm,
                    norm.replace("/", "-"),
                    norm.replace("/", ""),
                })

            conditions = [
                Show.title.ilike(like),
                Show.description.ilike(like),
                Show.location.ilike(like),
                Show.category.ilike(like),
            ]

            # Facultatif si le champ existe
            try:
                Show.contact_email  # type: ignore[attr-defined]
                conditions.append(Show.contact_email.ilike(like))  # type: ignore[attr-defined]
            except Exception:
                pass

            for v in {v for v in variants if v}:
                v_like = f"%{v}%"
                try:
                    conditions.append(Show.age_range.ilike(v_like))
                except Exception:
                    pass
                conditions.append(Show.description.ilike(v_like))

            shows = shows.filter(or_(*conditions))

        # Filtres simples
        if category:
            from sqlalchemy import func
            shows = shows.filter(func.lower(Show.category).like(f"%{category.lower()}%"))
        if location:
            like = f"%{location}%"
            shows = shows.filter(or_(Show.location.ilike(like), Show.region.ilike(like)))

        # Type de fichier
        if type_filter == "image":
            shows = shows.filter(Show.file_mimetype.ilike("image/%"))
        elif type_filter == "pdf":
            shows = shows.filter(Show.file_mimetype.ilike("application/pdf"))

        # Filtres de dates
        def parse_date(s: str):
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except Exception:
                return None

        if date_from:
            d1 = parse_date(date_from)
            if d1:
                shows = shows.filter(Show.date >= d1)
        if date_to:
            d2 = parse_date(date_to)
            if d2:
                shows = shows.filter(Show.date <= d2)

        # Tri : par display_order d'abord (plus petit = plus haut), puis par date de création
        shows = shows.order_by(Show.display_order.asc(), Show.created_at.desc())

        # Pagination : 16 résultats par page
        try:
            pagination = shows.paginate(page=page, per_page=16, error_out=False)
            shows_list = pagination.items
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Erreur lors de la requête /home: %s", e)
            flash("Une erreur est survenue lors de la recherche.", "danger")
            pagination = None
            shows_list = []

        try:
            categories = [c[0] for c in db.session.query(Show.category).distinct().all() if c[0]]
            locations = [l[0] for l in db.session.query(Show.location).distinct().all() if l[0]]
        except Exception:
            db.session.rollback()
            categories = []
            locations = []

        # Générer un H1 SEO dynamique selon les filtres
        h1_title = "Spectacles et animations pour mairies, écoles et CSE partout en France"
        if category and location:
            h1_title = f"Spectacles {category} à {location} - Artistes professionnels"
        elif category:
            h1_title = f"Spectacles {category} pour enfants, mairies et entreprises en France"
        elif location:
            h1_title = f"Spectacles et animations à {location} - Artistes professionnels"

        # Tri personnalisé : Spectacle enfant d'abord, Atelier en dernier, autres entre les deux

        def genre_order(show):
            cat = (show.category or '').strip().lower()
            if 'à la une' in cat or 'a la une' in cat or 'une' in cat:
                return 0
            elif 'enfant' in cat:
                return 1
            elif 'atelier' in cat:
                return 3
            else:
                return 2
        shows_list_sorted = sorted(shows_list, key=genre_order)

        return render_template(
            "catalogue.html",
            shows=shows_list_sorted,
            pagination=pagination,
            q=q,
            category=category,
            location=location,
            categories=sorted(categories),
            locations=sorted(locations),
            type_filter=type_filter,
            sort=sort,
            date_from=date_from,
            date_to=date_to,
            h1_title=h1_title,
            user=current_user(),
        )

    # ---------------------------
    # SEO: robots.txt et sitemap.xml
    # ---------------------------
    @app.route("/robots.txt")
    def robots_txt():
        return send_from_directory(current_app.static_folder, "robots.txt", mimetype="text/plain")

    @app.route("/favicon.ico")
    def favicon_ico():
        # Certains navigateurs requêtent /favicon.ico par défaut.
        return redirect(url_for("static", filename="img/favicon.svg"))

    @app.route("/sitemap.xml")
    def sitemap_xml():
        """Génère dynamiquement un sitemap XML"""
        from flask import make_response
        
        pages = []
        # Page d'accueil
        pages.append({
            'loc': url_for('home', _external=True),
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '1.0'
        })
        
        # Page demande d'animation
        pages.append({
            'loc': url_for('demande_animation', _external=True),
            'changefreq': 'monthly',
            'priority': '0.8'
        })
        
        # Pages thématiques SEO (haute priorité)
        seo_pages = [
            ('spectacles_enfants', '0.9'),
            ('animations_enfants', '0.9'),
            ('spectacles_noel', '0.85'),
            ('animations_entreprises', '0.9'),
            ('marionnettes', '0.85'),
            ('magiciens', '0.85'),
            ('clowns', '0.85'),
            ('animations_anniversaire', '0.85'),
            ('booker_artiste', '0.8'),
            ('demandes_animation', '0.8'),
        ]
        
        for endpoint, priority in seo_pages:
            try:
                pages.append({
                    'loc': url_for(endpoint, _external=True),
                    'changefreq': 'weekly',
                    'priority': priority
                })
            except Exception:
                pass  # Si la route n'existe pas, on ignore
        
        # Tous les spectacles approuvés
        shows = Show.query.filter(Show.approved.is_(True)).all()
        for show in shows:
            pages.append({
                'loc': url_for('show_detail', show_id=show.id, _external=True),
                'lastmod': show.created_at.strftime('%Y-%m-%d') if show.created_at else datetime.utcnow().strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '0.7'
            })
        
        # Générer le XML
        sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for page in pages:
            sitemap_xml += '  <url>\n'
            sitemap_xml += f'    <loc>{page["loc"]}</loc>\n'
            if 'lastmod' in page:
                sitemap_xml += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
            if 'changefreq' in page:
                sitemap_xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
            if 'priority' in page:
                sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
            sitemap_xml += '  </url>\n'
        
        sitemap_xml += '</urlset>'
        
        response = make_response(sitemap_xml)
        response.headers["Content-Type"] = "application/xml"
        return response

    # ---------------------------
    # Monitoring et Health Check
    # ---------------------------
    @app.route("/health")
    def health_check():
        """Endpoint de santé pour le monitoring"""
        from flask import jsonify
        
        try:
            # Vérifier la connexion à la base de données
            db.session.execute(db.text("SELECT 1"))
            db_status = "ok"
        except Exception as e:
            current_app.logger.error(f"Health check - Erreur BDD: {e}")
            db_status = "error"
        
        status = {
            "status": "healthy" if db_status == "ok" else "unhealthy",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        status_code = 200 if db_status == "ok" else 503
        return jsonify(status), status_code

    @app.route("/health/s3")
    def s3_health_check():
        """Endpoint pour vérifier la connectivité S3"""
        from flask import jsonify
        
        s3_bucket = current_app.config.get("S3_BUCKET")
        s3_key = current_app.config.get("S3_KEY")
        s3_secret = current_app.config.get("S3_SECRET")
        s3_region = current_app.config.get("S3_REGION")
        
        if not (s3_bucket and s3_key and s3_secret):
            return jsonify({
                "status": "not_configured",
                "message": "S3 credentials not set",
                "bucket": s3_bucket or "not set",
                "region": s3_region or "not set"
            }), 200
        
        if not boto3:
            return jsonify({
                "status": "error",
                "message": "boto3 not installed"
            }, 500)
        
        try:
            import botocore
            s3_client = boto3.client(
                "s3",
                region_name=s3_region,
                aws_access_key_id=s3_key,
                aws_secret_access_key=s3_secret
            )
            # Test: list bucket (requires s3:ListBucket permission)
            s3_client.head_bucket(Bucket=s3_bucket)
            
            return jsonify({
                "status": "ok",
                "bucket": s3_bucket,
                "region": s3_region,
                "message": "S3 connection successful"
            }), 200
            
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            return jsonify({
                "status": "error",
                "bucket": s3_bucket,
                "error_code": error_code,
                "message": str(e)
            }), 500
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # ---------------------------
    # Publication & fichiers
    # ---------------------------
    @app.route("/publish")
    @login_required
    def publish():
        # Rediriger vers le vrai formulaire de publication
        return redirect(url_for("submit_show"))

    @app.route("/submit", methods=["GET", "POST"])
    @login_required
    def submit_show():
        if request.method == "POST":
            # Forcer la raison sociale = username de l'utilisateur connecté
            u = current_user()
            raison_sociale = u.username if u else None
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            region = request.form.get("region", "").strip()
            location = request.form.get("location", "").strip()
            category = request.form.get("category", "").strip()
            date_str = request.form.get("date", "").strip()
            age_range = request.form.get("age_range", "").strip()
            contact_email = request.form.get("contact_email", "").strip()
            contact_phone = request.form.get("contact_phone", "").strip()
            site_internet = request.form.get("site_internet", "").strip()
            is_event = request.form.get("is_event", "0") == "1"

            date_val = None
            if date_str:
                try:
                    date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")

            file = request.files.get("file")
            file_name = None
            file_mimetype = None

            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (png/jpg/jpeg/gif/webp/pdf).", "danger")
                    return redirect(request.url)

                # Vérifier la taille du fichier
                is_valid, error_msg = validate_file_size(file)
                if not is_valid:
                    flash(error_msg, "danger")
                    return redirect(request.url)

                # Sauvegarde locale du fichier
                file_name = upload_file_local(file)
                file_mimetype = file.mimetype

            # Gestion de la photo 2 pour le diaporama
            file2 = request.files.get("file2")
            file_name2 = None
            if file2 and file2.filename:
                if not allowed_file(file2.filename):
                    flash("Photo 2 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid2, error_msg2 = validate_file_size(file2)
                if not is_valid2:
                    flash(f"Photo 2 : {error_msg2}", "danger")
                    return redirect(request.url)
                file_name2 = upload_file_local(file2)

            # Gestion de la photo 3 pour le diaporama
            file3 = request.files.get("file3")
            file_name3 = None
            if file3 and file3.filename:
                if not allowed_file(file3.filename):
                    flash("Photo 3 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid3, error_msg3 = validate_file_size(file3)
                if not is_valid3:
                    flash(f"Photo 3 : {error_msg3}", "danger")
                    return redirect(request.url)
                file_name3 = upload_file_local(file3)

            show = Show(
                raison_sociale=raison_sociale or None,
                title=title,
                description=description,
                region=region or None,
                location=location,
                category=category,
                age_range=age_range or None,
                date=date_val,
                file_name=file_name,
                file_mimetype=file_mimetype,
                file_name2=file_name2,
                file_name3=file_name3,
                contact_email=contact_email or None,
                contact_phone=contact_phone or None,
                site_internet=site_internet or None,
                is_event=is_event,
                approved=False,
                user_id=current_user().id if current_user() else None,   # associer l'auteur
            )
            db.session.add(show)
            db.session.commit()

            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                try:
                    to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                    type_annonce = "📅 ÉVÉNEMENT" if is_event else "🎭 CATALOGUE"
                    body = (
                        f"🎭 Nouvelle annonce à valider [{type_annonce}]\n\n"
                        f"👤 Compagnie: {raison_sociale}\n"
                        f"📌 Titre: {title}\n"
                        f"📍 Lieu: {location}\n"
                        f"🎪 Catégorie: {category}\n"
                        f"📋 Type: {type_annonce}\n"
                        + (f"📅 Date: {date_val}\n\n" if date_val else "")
                        + f"Date de création de la fiche : {show.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
                        + f"📧 Email: {contact_email}\n"
                        + f"📱 Téléphone: {contact_phone}\n"
                        + "\n\nAussi, vous bénéficiez dès aujourd'hui d'un abonnement gratuit de six mois (voir onglet Abonnement).\n"
                        + "L'abonnement est optionnel. La plateforme Spectacle'ment Vôtre est avant tout un annuaire du spectacle vivant français.\n\n"
                        + "N'hésitez pas à vous inscrire \"gratuitement\" et ajouter vos spectacles.\n"
                        + "\nCordialement,\nL'équipe Spectacle'ment VØtre"
                    )
                    msg = Message(subject="🎭 Nouvelle annonce à valider", recipients=[to_addr])  # type: ignore[arg-type]
                    msg.body = body  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                except Exception as e:  # pragma: no cover
                    print("[MAIL] envoi impossible:", e)

            flash("Annonce envoyée ! Elle sera visible après validation.", "success")
            # Afficher uniquement le message flash après création
            return render_template("flash_only_child.html", user=u)

        return render_template("submit_form.html", user=current_user())

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        from flask import abort, Response
        import mimetypes
        
        # Tente d'abord de servir le fichier localement (pour compatibilité)
        local_path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
        if local_path.exists():
            return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)
        
        # Sinon, tente de servir depuis S3
        s3_bucket = current_app.config.get("S3_BUCKET")
        s3_key = current_app.config.get("S3_KEY")
        s3_secret = current_app.config.get("S3_SECRET")
        s3_region = current_app.config.get("S3_REGION")
        
        if not (s3_bucket and s3_key and s3_secret and boto3):
            current_app.logger.warning(f"[UPLOADS] Fichier non trouvé localement et S3 non configuré: {filename}")
            abort(404)
        
        try:
            import botocore
            s3_client = boto3.client(
                "s3",
                region_name=s3_region,
                aws_access_key_id=s3_key,
                aws_secret_access_key=s3_secret
            )
            s3_response = s3_client.get_object(Bucket=s3_bucket, Key=filename)
            file_data = s3_response["Body"].read()
            content_type = s3_response.get("ContentType") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
            
            # Add cache headers for better performance
            response = Response(file_data, mimetype=content_type)
            response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 year cache
            return response
            
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"[S3] Erreur lecture fichier {filename}: {e}")
            abort(404)
        except Exception as e:
            current_app.logger.error(f"[S3] Erreur inattendue pour {filename}: {e}")
            abort(404)

    @app.route("/show/<int:show_id>")
    def show_detail(show_id: int):
        show = Show.query.get_or_404(show_id)
        # Seuls les spectacles approuvés sont visibles (sauf pour les admins)
        u = current_user()
        if not show.approved and not (u and u.is_admin):
            flash("Ce spectacle n'est pas encore approuvé.", "warning")
            return redirect(url_for("home"))
        # On ne transmet l'email de contact que si l'admin l'a renseigné (contact_email non vide)
        admin_email = show.contact_email.strip() if show.contact_email and show.contact_email.strip() else None
        
        # Récupérer les spectacles "à la une" pour les afficher en dessous
        spectacles_une = Show.query.filter(
            Show.approved.is_(True),
            Show.category.ilike('%Spectacle à la une%'),
            Show.id != show_id  # Exclure le spectacle actuel
        ).order_by(Show.created_at.desc()).limit(8).all()
        
        return render_template("show_detail.html", show=show, user=u, admin_email=admin_email, spectacles_une=spectacles_une)

    # ---------------------------
    # Espace Compagnie
    # ---------------------------
    @app.route("/dashboard", endpoint="company_dashboard")
    @login_required
    def company_dashboard():
        u = current_user()
        if u and u.is_admin:
            return redirect(url_for("admin_dashboard"))
        my_shows = Show.query.filter_by(user_id=u.id).order_by(Show.created_at.desc()).all() if u else []
        return render_template("company_dashboard.html", user=u, shows=my_shows)

    @app.route("/my/shows/<int:show_id>/edit", methods=["GET","POST"], endpoint="show_edit_self")
    @login_required
    def show_edit_self(show_id: int):
        s = Show.query.get_or_404(show_id)
        u = current_user()
        if not u or not (u.is_admin or s.user_id == u.id):
            flash("Accès refusé.", "danger")
            return redirect(url_for("company_dashboard"))

        if request.method == "POST":
            s.raison_sociale = request.form.get("raison_sociale","").strip() or None
            s.title = request.form.get("title","").strip()
            s.description = request.form.get("description","").strip()
            s.region = request.form.get("region","").strip() or None
            s.location = request.form.get("location","").strip()
            s.category = request.form.get("category","").strip()
            s.age_range = (request.form.get("age_range","") or None)
            s.site_internet = request.form.get("site_internet","").strip() or None
            s.contact_email = request.form.get("contact_email","").strip() or None
            s.contact_phone = request.form.get("contact_phone","").strip() or None

            date_str = request.form.get("date","").strip()
            if date_str:
                try:
                    s.date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")
            else:
                s.date = None

            file = request.files.get("file")
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (png/jpg/jpeg/gif/webp/pdf).", "danger")
                    return redirect(request.url)
                
                # Vérifier la taille du fichier
                is_valid, error_msg = validate_file_size(file)
                if not is_valid:
                    flash(error_msg, "danger")
                    return redirect(request.url)

                # Supprimer l'ancien fichier (best-effort)
                if s.file_name:
                    delete_file_s3(s.file_name)
                    try:
                        old_local = Path(current_app.config["UPLOAD_FOLDER"]) / s.file_name
                        if old_local.exists():
                            old_local.unlink()
                    except Exception:
                        pass

                # Upload S3 (fallback local si S3 non configuré)
                new_name = upload_file_local(file)
                s.file_name = new_name
                s.file_mimetype = file.mimetype

            # Gestion de la photo 2 pour le diaporama
            file2 = request.files.get("file2")
            if file2 and file2.filename:
                if not allowed_file(file2.filename):
                    flash("Photo 2 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid, error_msg = validate_file_size(file2)
                if not is_valid:
                    flash(f"Photo 2 : {error_msg}", "danger")
                    return redirect(request.url)
                if s.file_name2:
                    delete_file_s3(s.file_name2)
                    try:
                        old_local = Path(current_app.config["UPLOAD_FOLDER"]) / s.file_name2
                        if old_local.exists():
                            old_local.unlink()
                    except Exception:
                        pass
                s.file_name2 = upload_file_local(file2)
                s.file_mimetype2 = file2.mimetype

            # Gestion de la photo 3 pour le diaporama
            file3 = request.files.get("file3")
            if file3 and file3.filename:
                if not allowed_file(file3.filename):
                    flash("Photo 3 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid, error_msg = validate_file_size(file3)
                if not is_valid:
                    flash(f"Photo 3 : {error_msg}", "danger")
                    return redirect(request.url)
                if s.file_name3:
                    delete_file_s3(s.file_name3)
                    try:
                        old_local = Path(current_app.config["UPLOAD_FOLDER"]) / s.file_name3
                        if old_local.exists():
                            old_local.unlink()
                    except Exception:
                        pass
                s.file_name3 = upload_file_local(file3)
                s.file_mimetype3 = file3.mimetype

            db.session.commit()
            flash("Spectacle mis à jour.", "success")
            return render_template("flash_only_child.html", user=u)

        return render_template("show_form_edit.html", show=s, user=u)

    @app.route("/my/shows/<int:show_id>/delete", methods=["POST"], endpoint="show_delete_self")
    @login_required
    def show_delete_self(show_id: int):
        s = Show.query.get_or_404(show_id)
        u = current_user()

        if not u or not (u.is_admin or s.user_id == u.id):
            flash("Accès refusé.", "danger")
            return redirect(url_for("company_dashboard"))

        # Supprimer tous les fichiers (photo 1, 2 et 3)
        for fname in [s.file_name, s.file_name2, s.file_name3]:
            if fname:
                delete_file_s3(fname)
                p = Path(current_app.config["UPLOAD_FOLDER"]) / fname
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

        db.session.delete(s)
        db.session.commit()
        flash("Spectacle supprimé.", "success")
        return render_template("flash_only_child.html", user=u)

    # ---------------------------
    # Espace Admin
    # ---------------------------
    @app.route("/admin", endpoint="admin_dashboard")
    @login_required
    @admin_required
    def admin_dashboard():
        page = request.args.get("page", 1, type=int)
        
        # Pagination pour tous les spectacles
        pagination = Show.query.order_by(Show.created_at.desc()).paginate(
            page=page, per_page=30, error_out=False
        )
        shows = pagination.items
        
        # Liste des spectacles en attente (non paginée pour le badge)
        pending = Show.query.filter_by(approved=False).all()
        
        return render_template(
            "admin_dashboard.html", 
            user=current_user(), 
            shows=shows, 
            pending=pending,
            pagination=pagination
        )

    @app.route("/admin/shows/new", methods=["GET", "POST"])
    @login_required
    @admin_required
    def show_new():

        if request.method == "POST":

            raison_sociale = request.form.get("raison_sociale", "").strip()
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            region = request.form.get("region", "").strip()
            location = request.form.get("location", "").strip()
            category = request.form.get("category", "").strip()
            age_range = request.form.get("age_range", "").strip()
            date_str = request.form.get("date", "").strip()
            site_internet = request.form.get("site_internet", "").strip()
            contact_email = request.form.get("contact_email", "").strip()

            date_val = None
            if date_str:
                try:
                    date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")

            file = request.files.get("file")
            file_name = None
            file_mimetype = None

            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (png/jpg/jpeg/gif/webp/pdf).", "danger")
                    return redirect(request.url)

                # Vérifier la taille du fichier
                is_valid, error_msg = validate_file_size(file)
                if not is_valid:
                    flash(error_msg, "danger")
                    return redirect(request.url)

                # 🔥 Envoi sur S3 au lieu du disque local
                file_name = upload_file_local(file)
                file_mimetype = file.mimetype

            # Gestion des photos 2 et 3 pour le diaporama
            file2 = request.files.get("file2")
            file_name2 = None
            file_mimetype2 = None

            if file2 and file2.filename:
                if not allowed_file(file2.filename):
                    flash("Photo 2 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid, error_msg = validate_file_size(file2)
                if not is_valid:
                    flash(f"Photo 2 : {error_msg}", "danger")
                    return redirect(request.url)
                file_name2 = upload_file_local(file2)
                file_mimetype2 = file2.mimetype

            file3 = request.files.get("file3")
            file_name3 = None
            file_mimetype3 = None

            if file3 and file3.filename:
                if not allowed_file(file3.filename):
                    flash("Photo 3 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid, error_msg = validate_file_size(file3)
                if not is_valid:
                    flash(f"Photo 3 : {error_msg}", "danger")
                    return redirect(request.url)
                file_name3 = upload_file_local(file3)
                file_mimetype3 = file3.mimetype

            show = Show(
                raison_sociale=raison_sociale or None,
                title=title,
                description=description,
                region=region or None,
                location=location,
                category=category,
                age_range=age_range or None,
                date=date_val,
                file_name=file_name,
                file_mimetype=file_mimetype,
                file_name2=file_name2,
                file_mimetype2=file_mimetype2,
                file_name3=file_name3,
                file_mimetype3=file_mimetype3,
                site_internet=site_internet or None,
                contact_email=contact_email or None,
                approved=False,
            )
            db.session.add(show)
            db.session.commit()

            # L'email de notification sera envoyé lors de la validation par l'admin

            flash("Annonce créée (en attente de validation).", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("show_form_new.html", user=current_user())

    @app.route("/admin/shows/<int:show_id>/edit", methods=["GET", "POST"])
    @login_required
    @admin_required
    def show_edit(show_id: int):
        show = Show.query.get_or_404(show_id)
        if request.method == "POST":
            show.raison_sociale = request.form.get("raison_sociale", "").strip() or None
            show.title = request.form.get("title", "").strip()
            show.description = request.form.get("description", "").strip()
            show.region = request.form.get("region", "").strip() or None
            show.location = request.form.get("location", "").strip()
            show.category = request.form.get("category", "").strip()
            show.age_range = request.form.get("age_range", "").strip() or None
            show.contact_email = request.form.get("contact_email", "").strip() or None
            show.contact_phone = request.form.get("contact_phone", "").strip() or None
            date_str = request.form.get("date", "").strip()
            show.site_internet = request.form.get("site_internet", "").strip() or None
            # Gérer le champ is_event (admin seulement)
            show.is_event = request.form.get("is_event", "0") == "1"
            if date_str:
                try:
                    show.date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")
            else:
                show.date = None

            file = request.files.get("file")
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (pdf/jpg/jpeg/png/webp/gif).", "danger")
                    return redirect(request.url)

                # Vérifier la taille du fichier
                is_valid, error_msg = validate_file_size(file)
                if not is_valid:
                    flash(error_msg, "danger")
                    return redirect(request.url)

                # Supprimer l'ancien fichier (best-effort)
                if show.file_name:
                    delete_file_s3(show.file_name)
                    try:
                        old_local = Path(current_app.config["UPLOAD_FOLDER"]) / show.file_name
                        if old_local.exists():
                            old_local.unlink()
                    except Exception:
                        pass

                # Upload S3 (fallback local si S3 non configuré)
                new_name = upload_file_local(file)
                show.file_name = new_name
                show.file_mimetype = file.mimetype

            # Gestion de la photo 2 pour le diaporama
            file2 = request.files.get("file2")
            if file2 and file2.filename:
                if not allowed_file(file2.filename):
                    flash("Photo 2 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid, error_msg = validate_file_size(file2)
                if not is_valid:
                    flash(f"Photo 2 : {error_msg}", "danger")
                    return redirect(request.url)
                # Supprimer l'ancienne photo 2
                if show.file_name2:
                    delete_file_s3(show.file_name2)
                    try:
                        old_local = Path(current_app.config["UPLOAD_FOLDER"]) / show.file_name2
                        if old_local.exists():
                            old_local.unlink()
                    except Exception:
                        pass
                show.file_name2 = upload_file_local(file2)
                show.file_mimetype2 = file2.mimetype

            # Gestion de la photo 3 pour le diaporama
            file3 = request.files.get("file3")
            if file3 and file3.filename:
                if not allowed_file(file3.filename):
                    flash("Photo 3 : Type de fichier non autorisé.", "danger")
                    return redirect(request.url)
                is_valid, error_msg = validate_file_size(file3)
                if not is_valid:
                    flash(f"Photo 3 : {error_msg}", "danger")
                    return redirect(request.url)
                # Supprimer l'ancienne photo 3
                if show.file_name3:
                    delete_file_s3(show.file_name3)
                    try:
                        old_local = Path(current_app.config["UPLOAD_FOLDER"]) / show.file_name3
                        if old_local.exists():
                            old_local.unlink()
                    except Exception:
                        pass
                show.file_name3 = upload_file_local(file3)
                show.file_mimetype3 = file3.mimetype

            db.session.commit()
            flash("Annonce mise à jour.", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("show_form_edit.html", show=show, user=current_user())

    @app.route("/admin/shows/<int:show_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def show_delete(show_id: int):
        show = Show.query.get_or_404(show_id)

        # Supprimer tous les fichiers (photo 1, 2 et 3)
        for fname in [show.file_name, show.file_name2, show.file_name3]:
            if fname:
                delete_file_s3(fname)
                p = Path(current_app.config["UPLOAD_FOLDER"]) / fname
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

        db.session.delete(show)
        db.session.commit()
        flash("Annonce supprimée.", "success")
        return redirect(request.referrer or url_for("admin_dashboard"))

    @app.route("/admin/shows/<int:show_id>/approve", methods=["POST"])
    @login_required
    @admin_required
    def show_approve(show_id: int):
        show = Show.query.get_or_404(show_id)
        show.approved = True
        db.session.commit()
        
        # Envoi automatique d'un email avec le lien du spectacle à la compagnie après validation
        if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
            try:
                # On privilégie l'email de la compagnie si présent, sinon fallback admin
                to_addr = show.contact_email if show.contact_email else (current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME"))
                show_url = url_for("show_detail", show_id=show.id, _external=True)
                
                # Déterminer si c'est une carte créée par l'admin (pas de user_id) ou par l'utilisateur
                if show.user_id:
                    # Carte créée par l'utilisateur lui-même → Email de validation classique
                    subject = "Votre spectacle est validé sur Spectacle'ment VØtre !"
                    body = (
                        "Bonjour,\n\n"
                        "Votre spectacle vient d'être validé et publié sur Spectacle'ment VØtre.\n\n"
                        f"Compagnie : {show.raison_sociale or 'Non renseignée'}\n"
                        f"Titre : {show.title}\n"
                        f"Lieu : {show.location}\n"
                        f"Catégorie : {show.category}\n"
                        + (f"Date : {show.date}\n" if show.date else "")
                        + f"Date de publication : {show.created_at.strftime('%d/%m/%Y %H:%M') if show.created_at else 'N/A'}\n\n"
                        + f"Lien direct vers l'annonce (public) : {show_url}\n\n"
                        + "Si vous souhaitez la retirer ou la modifier, merci de nous contacter par simple retour de ce mail.\n\n"
                        + "Aussi, vous bénéficiez dès aujourd'hui d'un abonnement gratuit de six mois (voir onglet Abonnement).\n"
                        + "L'abonnement est totalement optionnel : Spectacle'ment VØtre reste avant tout un annuaire gratuit d'artistes.\n\n"
                        + "N'hésitez pas à vous inscrire \"gratuitement\" et ajouter vos spectacles sur la plateforme (Inscription/Connexion > Ajouter votre spectacle).\n\n"
                        + "Spectaclement vôtre,\nL'équipe Spectacle'ment VØtre"
                    )
                else:
                    # Carte créée par l'admin → Email de découverte
                    subject = "Nous serions honorés de votre apparition gratuite sur notre annuaire Spectacle'ment VØtre !"
                    body = (
                        "Bonjour,\n\n"
                        "Spectacle'ment VØtre diffuse, crée et produit auprès des acteurs culturels français (Centres Culturels, C.Com, Mairies, CSE, Écoles, MJC, etc.), depuis plus de trente ans, des spectacles de qualité. "
                        "Notre créneau : proposer des spectacles haut de gamme avec des artistes expérimentés, évitant l'écueil de l'amateurisme aux acheteurs en quête de professionnalisme. "
                        "_Nous aimerions alors leur garantir ainsi la qualité car ils n'ont pas facilement la possibilité de se déplacer._\n\n"
                        "Votre spectacle a été repéré et nous avons créé une fiche pour vous :\n\n"
                        f"Compagnie : {show.raison_sociale or 'Non renseignée'}\n"
                        f"Titre : {show.title}\n"
                        f"Lieu : {show.location}\n"
                        f"Catégorie : {show.category}\n"
                        + (f"Date : {show.date}\n" if show.date else "")
                        + f"Date de publication : {show.created_at.strftime('%d/%m/%Y %H:%M') if show.created_at else 'N/A'}\n\n"
                        + f"Lien direct vers l'annonce (public) : {show_url}\n\n"
                        + "Si vous souhaitez la retirer ou la modifier, merci de nous contacter par simple retour de ce mail.\n\n"
                        + "Aussi, vous bénéficiez dès aujourd'hui d'un abonnement gratuit de six mois (voir onglet Abonnement).\n"
                        + "L'abonnement est totalement optionnel : Spectacle'ment VØtre reste avant tout un annuaire gratuit d'artistes.\n\n"
                        + "N'hésitez pas à vous inscrire \"gratuitement\" et ajouter vos spectacles sur la plateforme (Inscription/Connexion > Ajouter votre spectacle).\n\n"
                        + "Spectaclement vôtre,\nL'équipe Spectacle'ment VØtre"
                    )
                
                msg = Message(subject=subject, recipients=[to_addr])  # type: ignore[arg-type]
                msg.body = body  # type: ignore[assignment]
                current_app.mail.send(msg)  # type: ignore[attr-defined]
            except Exception as e:
                print("[MAIL] envoi automatique impossible:", e)
        
        flash("Annonce validée ✅", "success")
        return redirect(url_for("admin_dashboard"))

    # ---------------------------
    # Gestion de l'ordre d'affichage des cartes
    # ---------------------------
    @app.route("/admin/ordre-affichage", methods=["GET"])
    @login_required
    @admin_required
    def admin_ordre_affichage():
        """Page admin pour réorganiser l'ordre d'affichage des cartes."""
        page = request.args.get("page", 1, type=int)
        per_page = 50  # Plus de cartes par page pour faciliter la gestion
        
        pagination = Show.query.filter_by(approved=True).order_by(
            Show.display_order.asc(), Show.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        shows = pagination.items
        
        return render_template(
            "admin_ordre_affichage.html",
            user=current_user(),
            shows=shows,
            pagination=pagination
        )

    @app.route("/admin/shows/<int:show_id>/update-order", methods=["POST"])
    @login_required
    @admin_required
    def update_show_order(show_id: int):
        """Met à jour l'ordre d'affichage d'un spectacle."""
        show = Show.query.get_or_404(show_id)
        new_order = request.form.get("display_order", type=int)
        
        if new_order is not None:
            show.display_order = new_order
            db.session.commit()
            flash(f"Position de « {show.title} » mise à jour : {new_order}", "success")
        else:
            flash("Erreur : ordre non valide", "danger")
        
        return redirect(request.referrer or url_for("admin_ordre_affichage"))

    @app.route("/admin/shows/update-orders", methods=["POST"])
    @login_required
    @admin_required
    def update_shows_orders():
        """Met à jour l'ordre de plusieurs spectacles en une fois (via AJAX ou formulaire)."""
        try:
            # Format attendu : orders = {"show_id": new_order, ...}
            orders = request.get_json()
            if orders:
                for show_id, new_order in orders.items():
                    show = Show.query.get(int(show_id))
                    if show:
                        show.display_order = int(new_order)
                db.session.commit()
                return {"success": True, "message": "Ordres mis à jour"}
            return {"success": False, "message": "Aucune donnée reçue"}, 400
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}, 500

    # ---------------------------
    # Pages diverses
    # ---------------------------
    @app.route("/demande_animation", methods=["GET", "POST"])
    def demande_animation():
        if request.method == "POST":
            # Récupérer la date et l'heure d'envoi automatique
            auto_datetime = request.form.get("auto_datetime", "")
            # Récupération des données du formulaire
            structure = request.form.get("structure", "").strip()
            telephone = request.form.get("telephone", "").strip()
            lieu_ville = request.form.get("lieu_ville", "").strip()
            code_postal = request.form.get("code_postal", "").strip()
            region = request.form.get("region", "").strip()
            nom = request.form.get("nom", "").strip()
            dates_horaires = request.form.get("dates_horaires", "").strip()
            type_espace = request.form.get("type_espace", "").strip()
            genre_recherche = request.form.get("genre_recherche", "").strip()
            age_range = request.form.get("age_range", "").strip()
            jauge = request.form.get("jauge", "").strip()
            budget = request.form.get("budget", "").strip()
            contraintes = request.form.get("contraintes", "").strip()
            accessibilite = request.form.get("accessibilite", "").strip()
            contact_email = request.form.get("contact_email", "").strip()
            intitule = request.form.get("intitule", "").strip()

            # Validation basique
            if not all([structure, telephone, lieu_ville, code_postal, nom, dates_horaires, 
                       type_espace, genre_recherche, age_range, jauge, budget, contact_email, intitule]):
                flash("Veuillez remplir tous les champs obligatoires.", "danger")
                # UX: keep user on page and preserve entered values (no redirect)
                return render_template("demande_animation.html", user=current_user()), 400

            # Envoi d'email si configuré
            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                try:
                    to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                    body = f"""
Nouvelle demande d'animation

Date et heure de la demande (automatique) : {auto_datetime}
Structure: {structure}
Contact: {nom}
Téléphone: {telephone}
Email: {contact_email}
Intitulé de la demande: {intitule}
Lieu/Ville: {lieu_ville}
Code postal: {code_postal}
Région: {region}
Date(s) et horaires: {dates_horaires}
Type d'espace: {type_espace}
Genre recherché: {genre_recherche}
Tranche d'âge: {age_range}
Jauge: {jauge}
Budget: {budget}
Contraintes techniques: {contraintes}
Accessibilité: {accessibilite}
"""
                    msg = Message(subject="Nouvelle demande d'animation", recipients=[to_addr])  # type: ignore[arg-type]
                    msg.body = body  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                except Exception as e:  # pragma: no cover
                    print("[MAIL] envoi impossible:", e)

            # Enregistrement de la demande en base
            from models.models import DemandeAnimation
            demande = DemandeAnimation(
                auto_datetime=auto_datetime,
                structure=structure,
                telephone=telephone,
                lieu_ville=lieu_ville,
                code_postal=code_postal,
                region=region,
                nom=nom,
                dates_horaires=dates_horaires,
                type_espace=type_espace,
                genre_recherche=genre_recherche,
                age_range=age_range,
                jauge=jauge,
                budget=budget,
                contraintes=contraintes,
                accessibilite=accessibilite,
                contact_email=contact_email,
                intitule=intitule
            )
            db.session.add(demande)
            db.session.commit()

            flash("Votre demande d'animation a bien été envoyée ! Nous vous répondrons rapidement.", "success")
            return redirect(url_for("home"))

        # Récupérer les spectacles "à la une" pour affichage
        spectacles_une = Show.query.filter(
            Show.approved.is_(True),
            Show.category.ilike('%Spectacle à la une%')
        ).order_by(Show.created_at.desc()).limit(8).all()

        return render_template("demande_animation.html", user=current_user(), spectacles_une=spectacles_une)

    @app.route("/informations-legales")
    def legal():
        return render_template("legal.html", user=current_user())

    # ---------------------------
    # Pages thématiques SEO
    # ---------------------------
    @app.route("/spectacles-enfants")
    def spectacles_enfants():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.category.ilike('%enfant%'),
                Show.category.ilike('%jeune public%'),
                Show.category.ilike('%famille%'),
                Show.age_range.ilike('%ans%')
            )
        ).all()
        return render_template("spectacles_enfants.html", shows=shows, user=current_user())

    @app.route("/animations-enfants")
    def animations_enfants():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.category.ilike('%animation%'),
                Show.category.ilike('%atelier%'),
                Show.category.ilike('%jeu%'),
                Show.title.ilike('%animation%')
            )
        ).all()
        return render_template("animations_enfants.html", shows=shows, user=current_user())

    @app.route("/spectacles-noel")
    def spectacles_noel():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.title.ilike('%noël%'),
                Show.title.ilike('%noel%'),
                Show.description.ilike('%noël%'),
                Show.description.ilike('%noel%'),
                Show.category.ilike('%noël%'),
                Show.category.ilike('%noel%')
            )
        ).all()
        return render_template("spectacles_noel.html", shows=shows, user=current_user())

    @app.route("/animations-entreprises")
    def animations_entreprises():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.category.ilike('%entreprise%'),
                Show.category.ilike('%corporate%'),
                Show.category.ilike('%CSE%'),
                Show.description.ilike('%entreprise%'),
                Show.description.ilike('%corporate%')
            )
        ).all()
        return render_template("animations_entreprises.html", shows=shows, user=current_user())

    @app.route("/marionnettes")
    def marionnettes():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.category.ilike('%marionnette%'),
                Show.title.ilike('%marionnette%'),
                Show.description.ilike('%marionnette%')
            )
        ).all()
        return render_template("marionnettes.html", shows=shows, user=current_user())

    @app.route("/booker-artiste")
    def booker_artiste():
        # Afficher tous les spectacles pour la réservation d'artistes
        shows = Show.query.filter(Show.approved.is_(True)).all()
        return render_template("booker_artiste.html", shows=shows, user=current_user())

    @app.route("/magiciens")
    def magiciens():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.category.ilike('%magie%'),
                Show.category.ilike('%magicien%'),
                Show.title.ilike('%magie%'),
                Show.title.ilike('%magicien%')
            )
        ).all()
        return render_template("magiciens.html", shows=shows, user=current_user())

    @app.route("/clowns")
    def clowns():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.category.ilike('%clown%'),
                Show.title.ilike('%clown%'),
                Show.description.ilike('%clown%')
            )
        ).all()
        return render_template("clowns.html", shows=shows, user=current_user())

    @app.route("/animations-anniversaire")
    def animations_anniversaire():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.category.ilike('%anniversaire%'),
                Show.title.ilike('%anniversaire%'),
                Show.description.ilike('%anniversaire%'),
                Show.category.ilike('%enfant%'),
                Show.category.ilike('%animation%')
            )
        ).all()
        return render_template("animations_anniversaire.html", shows=shows, user=current_user())

    # ---------------------------
    # Recherche géolocalisée (optionnelle)
    # ---------------------------
    from math import radians, sin, cos, asin

    def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 2 * R * asin(a ** 0.5)

    try:
        from geopy.geocoders import Nominatim  # type: ignore
    except Exception:  # pragma: no cover
        Nominatim = None  # type: ignore

    def geocode(addr: str) -> Tuple[Optional[float], Optional[float]]:
        if not Nominatim:
            return None, None
        geo = Nominatim(user_agent="artemisia")
        try:
            loc = geo.geocode(addr)
            if loc:
                return float(loc.latitude), float(loc.longitude)
        except Exception:
            pass
        return None, None

    @app.route("/search", methods=["GET"])
    def search():
        q = request.args.get("q", "").strip()
        addr = request.args.get("address", "").strip()
        rad = request.args.get("radius", "20").strip()
        try:
            radius = float(rad)
        except Exception:
            radius = 20.0

        lat = request.args.get("lat")
        lng = request.args.get("lng")

        # 1) centre GPS
        if lat and lng:
            try:
                center = (float(lat), float(lng))
            except Exception:
                center = (None, None)
        else:
            center = geocode(addr)

        # 2) recherche textuelle
        base = Show.query
        if q:
            like = f"%{q}%"
            base = base.filter(Show.title.ilike(like) | Show.description.ilike(like))

        shows = base.all()
        results = []

        # 3) filtrage par distance
        if center and center[0] and center[1]:
            c_lat, c_lng = center
            for s in shows:
                if getattr(s, "latitude", None) and getattr(s, "longitude", None):
                    d = distance_km(c_lat, c_lng, float(s.latitude), float(s.longitude))
                    if d <= radius:
                        results.append((s, round(d, 1)))
            results.sort(key=lambda x: x[1])
        else:
            results = [(s, None) for s in shows]

        return render_template("search.html", results=results, q=q, address=addr, radius=radius)

    @app.route("/abonnement-compagnie")
    def abonnement_compagnie():
        return render_template("abonnement_compagnie.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            nom = request.form.get("nom", "").strip()
            email = request.form.get("email", "").strip()
            message = request.form.get("message", "").strip()
            try:
                if hasattr(current_app, "mail") and current_app.mail:
                    from flask_mail import Message
                    msg = Message(
                        subject="Nouveau message de contact",
                        recipients=["audition_2020@yahoo.fr"],
                        body=f"Nom: {nom}\nEmail: {email}\nMessage: {message}"
                    )
                    current_app.mail.send(msg)
                    flash("Votre message a été envoyé à audition_2020@yahoo.fr !", "success")
                else:
                    flash("Erreur: le service mail n'est pas configuré.", "danger")
            except Exception as e:
                print("[MAIL] Erreur envoi contact:", e)
                flash(f"Erreur lors de l'envoi du message: {e}", "danger")
            return render_template("contact.html")
        return render_template("contact.html")

    @app.route("/demandes-animation")
    def demandes_animation():
        from models.models import DemandeAnimation
        page = request.args.get('page', 1, type=int)
        per_page = 9
        categorie = request.args.get('categorie', '').strip()
        region = request.args.get('region', '').strip()
        
        # Base de la requête - TOUJOURS filtrer les demandes privées sur la page publique
        demandes_query = DemandeAnimation.query.filter(DemandeAnimation.is_private == False).order_by(DemandeAnimation.created_at.desc())
        
        if categorie:
            demandes_query = demandes_query.filter(DemandeAnimation.genre_recherche.ilike(f"%{categorie}%"))
        if region:
            demandes_query = demandes_query.filter(DemandeAnimation.lieu_ville.ilike(f"%{region}%"))
        
        total = demandes_query.count()
        demandes = demandes_query.offset((page-1)*per_page).limit(per_page).all()
        nb_pages = (total // per_page) + (1 if total % per_page > 0 else 0)
        
        # Pour le moteur de recherche : liste unique des catégories et régions existantes
        categories = [c[0] for c in db.session.query(DemandeAnimation.genre_recherche).distinct().all() if c[0]]
        regions = [r[0] for r in db.session.query(DemandeAnimation.lieu_ville).distinct().all() if r[0]]
        
        # Récupérer les spectacles "à la une" pour affichage
        spectacles_une = Show.query.filter(
            Show.approved.is_(True),
            Show.category.ilike('%Spectacle à la une%')
        ).order_by(Show.created_at.desc()).limit(8).all()
        
        return render_template("demandes_animation.html", demandes=demandes, page=page, nb_pages=nb_pages, total=total, per_page=per_page, user=current_user(), categories=categories, regions=regions, categorie=categorie, region=region, spectacles_une=spectacles_une)

    @app.route("/test-demandes")
    def test_demandes():
        return render_template("test_demandes.html")

    @app.route("/demandes-animation/delete/<int:demande_id>", methods=["POST"])
    @login_required
    @admin_required
    def delete_demande_animation(demande_id):
        from models.models import DemandeAnimation
        demande = DemandeAnimation.query.get_or_404(demande_id)
        db.session.delete(demande)
        db.session.commit()
        flash("Appel d'offre supprimé.", "success")
        return redirect(url_for("demandes_animation"))

    @app.route("/demandes-animation/edit/<int:demande_id>", methods=["GET", "POST"])
    @login_required
    @admin_required
    def edit_demande_animation(demande_id):
        from models.models import DemandeAnimation
        demande = DemandeAnimation.query.get_or_404(demande_id)
        if request.method == "POST":
            demande.structure = request.form.get("structure", demande.structure)
            demande.telephone = request.form.get("telephone", demande.telephone)
            demande.lieu_ville = request.form.get("lieu_ville", demande.lieu_ville)
            demande.nom = request.form.get("nom", demande.nom)
            demande.dates_horaires = request.form.get("dates_horaires", demande.dates_horaires)
            demande.type_espace = request.form.get("type_espace", demande.type_espace)
            demande.genre_recherche = request.form.get("genre_recherche", demande.genre_recherche)
            demande.age_range = request.form.get("age_range", demande.age_range)
            demande.jauge = request.form.get("jauge", demande.jauge)
            demande.budget = request.form.get("budget", demande.budget)
            demande.contraintes = request.form.get("contraintes", demande.contraintes)
            demande.accessibilite = request.form.get("accessibilite", demande.accessibilite)
            demande.contact_email = request.form.get("contact_email", demande.contact_email)
            demande.is_private = request.form.get("is_private") == "on"
            db.session.commit()
            flash("✅ Demande modifiée avec succès !", "success")
            # Rediriger vers la page admin pour voir toutes les demandes et avoir accès au bouton d'envoi
            return redirect(url_for("admin_demandes_animation"))
        return render_template("edit_demande_animation.html", demande=demande, user=current_user())

    @app.route("/admin/demandes-animation")
    @login_required
    @admin_required
    def admin_demandes_animation():
        """Page admin pour gérer toutes les demandes d'animation (publiques et privées)"""
        from models.models import DemandeAnimation
        page = request.args.get('page', 1, type=int)
        per_page = 15
        categorie = request.args.get('categorie', '').strip()
        region = request.args.get('region', '').strip()
        filtre = request.args.get('filtre', '').strip()  # 'privees', 'publiques', ou '' (toutes)
        
        # Base de la requête - l'admin voit TOUTES les demandes
        demandes_query = DemandeAnimation.query.order_by(DemandeAnimation.created_at.desc())
        
        # Filtrer par type (privé/public)
        if filtre == 'privees':
            demandes_query = demandes_query.filter(DemandeAnimation.is_private.is_(True))
        elif filtre == 'publiques':
            demandes_query = demandes_query.filter(DemandeAnimation.is_private.is_(False))
        
        if categorie:
            demandes_query = demandes_query.filter(DemandeAnimation.genre_recherche.ilike(f"%{categorie}%"))
        if region:
            demandes_query = demandes_query.filter(DemandeAnimation.lieu_ville.ilike(f"%{region}%"))
        
        total = demandes_query.count()
        demandes = demandes_query.offset((page-1)*per_page).limit(per_page).all()
        nb_pages = (total // per_page) + (1 if total % per_page > 0 else 0)
        
        # Compter les demandes privées et publiques
        nb_privees = DemandeAnimation.query.filter(DemandeAnimation.is_private.is_(True)).count()
        nb_publiques = DemandeAnimation.query.filter(DemandeAnimation.is_private.is_(False)).count()
        
        return render_template(
            "admin_demandes_animation.html", 
            demandes=demandes, 
            page=page, 
            nb_pages=nb_pages, 
            total=total, 
            per_page=per_page,
            nb_privees=nb_privees,
            nb_publiques=nb_publiques,
            filtre=filtre,
            categorie=categorie,
            region=region,
            user=current_user()
        )

    @app.route("/admin/demande-animation/new", methods=["GET", "POST"])
    @login_required
    @admin_required
    def admin_create_demande_animation():
        """Créer une demande d'animation privée (admin uniquement)"""
        from models.models import DemandeAnimation
        from datetime import datetime
        
        if request.method == "POST":
            structure = request.form.get("structure", "").strip()
            telephone = request.form.get("telephone", "").strip()
            lieu_ville = request.form.get("lieu_ville", "").strip()
            nom = request.form.get("nom", "").strip()
            dates_horaires = request.form.get("dates_horaires", "").strip()
            type_espace = request.form.get("type_espace", "").strip()
            genre_recherche = request.form.get("genre_recherche", "").strip()
            age_range = request.form.get("age_range", "").strip()
            jauge = request.form.get("jauge", "").strip()
            budget = request.form.get("budget", "").strip()
            contraintes = request.form.get("contraintes", "").strip()
            accessibilite = request.form.get("accessibilite", "").strip()
            contact_email = request.form.get("contact_email", "").strip()
            is_private = request.form.get("is_private") == "on"

            # Validation basique
            if not all([structure, telephone, lieu_ville, nom, dates_horaires, 
                       type_espace, genre_recherche, age_range, jauge, budget, contact_email]):
                flash("Veuillez remplir tous les champs obligatoires.", "danger")
                return render_template("admin_create_demande.html", user=current_user()), 400

            # Créer la demande
            demande = DemandeAnimation(
                auto_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                structure=structure,
                telephone=telephone,
                lieu_ville=lieu_ville,
                nom=nom,
                dates_horaires=dates_horaires,
                type_espace=type_espace,
                genre_recherche=genre_recherche,
                age_range=age_range,
                jauge=jauge,
                budget=budget,
                contraintes=contraintes,
                accessibilite=accessibilite,
                contact_email=contact_email,
                is_private=is_private
            )
            db.session.add(demande)
            db.session.commit()

            if is_private:
                flash("🔒 Demande privée créée ! Sélectionnez maintenant les catégories pour l'envoi.", "success")
            else:
                flash("✅ Demande publique créée ! Sélectionnez maintenant les catégories pour l'envoi.", "success")
            
            # Rediriger directement vers la page d'envoi
            return redirect(url_for("envoyer_demande_animation", demande_id=demande.id))

        return render_template("admin_create_demande.html", user=current_user())

    @app.route("/admin/envoyer-demande/<int:demande_id>", methods=["GET", "POST"])
    @login_required
    @admin_required
    def envoyer_demande_animation(demande_id):
        """Interface pour envoyer une demande d'animation aux utilisateurs par catégorie"""
        from models.models import DemandeAnimation
        demande = DemandeAnimation.query.get_or_404(demande_id)
        
        if request.method == "POST":
            print(f"[DEBUG] POST reçu pour demande_id={demande_id}")
            categories = request.form.getlist("categories")
            regions = request.form.getlist("regions")
            print(f"[DEBUG] Catégories sélectionnées: {categories}")
            print(f"[DEBUG] Régions sélectionnées: {regions}")
            
            if not categories:
                print("[DEBUG] Aucune catégorie sélectionnée")
                flash("Veuillez sélectionner au moins une catégorie.", "warning")
                return redirect(request.url)
            
            print(f"[DEBUG] Recherche des spectacles pour {len(categories)} catégories et {len(regions)} régions")
            # Récupérer tous les spectacles correspondants
            query = Show.query.filter(Show.approved.is_(True))
            
            if categories:
                category_filters = [Show.category.ilike(f"%{cat}%") for cat in categories]
                query = query.filter(or_(*category_filters))
            
            # Filtrer par région si des régions sont sélectionnées
            if regions:
                # Filtrer sur la région du spectacle OU la région de l'utilisateur propriétaire
                region_filters = []
                for reg in regions:
                    region_filters.append(Show.region.ilike(f"%{reg}%"))
                query = query.filter(or_(*region_filters))
            
            shows = query.all()
            
            print(f"[DEBUG] {len(shows)} spectacles trouvés")
            # Récupérer les emails uniques des utilisateurs
            emails_sent = set()
            success_count = 0
            error_count = 0
            
            # Vérifier si mail est configuré
            if not getattr(current_app, "mail", None):
                print("[DEBUG ERREUR] Flask-Mail n'est pas configuré !")
                flash("❌ Erreur : le service email n'est pas configuré.", "danger")
                return redirect(url_for("admin_demandes_animation"))
            
            # Si des régions sont sélectionnées, ajouter aussi les utilisateurs directement
            # (ceux qui ont une région correspondante mais dont le spectacle n'a pas de région définie)
            additional_users = []
            if regions:
                from models.models import User as UserModel
                user_region_filters = []
                for reg in regions:
                    user_region_filters.append(UserModel.region.ilike(f"%{reg}%"))
                additional_users = UserModel.query.filter(
                    UserModel.email.isnot(None),
                    or_(*user_region_filters)
                ).all()
                print(f"[DEBUG] {len(additional_users)} utilisateurs supplémentaires avec région correspondante")
            
            print(f"[DEBUG] Flask-Mail configuré, début de l'envoi...")
            for show in shows:
                # Vérifier si l'utilisateur correspond aux régions sélectionnées (si applicable)
                if regions and show.user and show.user.region:
                    user_region_match = any(reg.lower() in show.user.region.lower() for reg in regions)
                    show_region_match = show.region and any(reg.lower() in show.region.lower() for reg in regions)
                    if not user_region_match and not show_region_match:
                        continue  # Skip si ni le spectacle ni l'utilisateur ne correspondent à une région sélectionnée
                
                # Utiliser l'email du spectacle en priorité, sinon l'email de l'utilisateur
                email = show.contact_email
                if not email and show.user:
                    email = show.user.email if hasattr(show.user, 'email') else None
                
                if email and email not in emails_sent:
                    emails_sent.add(email)
                    
                    # Envoyer l'email à l'adresse réelle
                    if getattr(current_app, "mail", None):
                        try:
                            body = f"""Bonjour,

Nous avons une nouvelle demande d'animation qui pourrait vous intéresser :

📍 Lieu : {demande.lieu_ville}
📅 Date(s) : {demande.dates_horaires}
🎭 Type recherché : {demande.genre_recherche}
👥 Jauge : {demande.jauge}
💰 Budget : {demande.budget}
👶 Âge : {demande.age_range}
🏢 Type d'espace : {demande.type_espace}

Structure : {demande.structure}
Contact : {demande.nom}
Email : {demande.contact_email}
Téléphone : {demande.telephone}

Contraintes techniques : {demande.contraintes or 'Aucune'}
Accessibilité : {demande.accessibilite or 'Non précisée'}

Si vous êtes intéressé(e), vous pouvez contacter directement le demandeur.

Cordialement,
L'équipe Spectacle'ment VØtre

---
Votre spectacle concerné: {show.title}
Catégorie: {show.category}
"""
                            msg = Message(
                                subject=f"Nouvelle opportunité : {demande.genre_recherche} à {demande.lieu_ville}",
                                recipients=[email]
                            )
                            msg.body = body
                            current_app.mail.send(msg)
                            print(f"[DEBUG] ✅ Email envoyé à {email}")
                            success_count += 1
                        except Exception as e:
                            print(f"[MAIL] ❌ Erreur envoi à {email}: {e}")
                            error_count += 1
            
            # Envoyer aussi aux utilisateurs additionnels par région (qui n'ont pas de spectacle correspondant aux catégories mais sont dans la région)
            for user in additional_users:
                if user.email and user.email not in emails_sent:
                    emails_sent.add(user.email)
                    try:
                        body = f"""Bonjour,

Nous avons une nouvelle demande d'animation dans votre région qui pourrait vous intéresser :

📍 Lieu : {demande.lieu_ville}
📅 Date(s) : {demande.dates_horaires}
🎭 Type recherché : {demande.genre_recherche}
👥 Jauge : {demande.jauge}
💰 Budget : {demande.budget}
👶 Âge : {demande.age_range}
🏢 Type d'espace : {demande.type_espace}

Structure : {demande.structure}
Contact : {demande.nom}
Email : {demande.contact_email}
Téléphone : {demande.telephone}

Contraintes techniques : {demande.contraintes or 'Aucune'}
Accessibilité : {demande.accessibilite or 'Non précisée'}

Si vous êtes intéressé(e), vous pouvez contacter directement le demandeur.

Cordialement,
L'équipe Spectacle'ment VØtre
"""
                        msg = Message(
                            subject=f"Nouvelle opportunité dans votre région : {demande.genre_recherche} à {demande.lieu_ville}",
                            recipients=[user.email]
                        )
                        msg.body = body
                        current_app.mail.send(msg)
                        print(f"[DEBUG] ✅ Email envoyé à {user.email} (utilisateur région)")
                        success_count += 1
                    except Exception as e:
                        print(f"[MAIL] ❌ Erreur envoi à {user.email}: {e}")
                        error_count += 1
            
            print(f"[DEBUG] Envoi terminé - Succès: {success_count}, Erreurs: {error_count}")
            if success_count > 0:
                flash(f"✅ Demande envoyée à {success_count} utilisateur(s) !", "success")
            if error_count > 0:
                flash(f"⚠️ {error_count} email(s) n'ont pas pu être envoyé(s).", "warning")
            
            if success_count == 0 and error_count == 0:
                flash("⚠️ Aucun email n'a été envoyé. Aucun spectacle correspondant trouvé.", "warning")
            
            # Retourner à la page admin des demandes
            return redirect(url_for("admin_demandes_animation"))
        
        # GET : afficher le formulaire de sélection
        # Liste des catégories prédéfinies du site
        predefined_categories = [
            "Magie",
            "Marionnette", 
            "Clown",
            "Théâtre",
            "Danse",
            "Spectacle de danse",
            "Spectacle enfant",
            "Spectacle maternelle",
            "Spectacle primaire",
            "Spectacle collège",
            "Spectacle lycée",
            "Jeune public",
            "Atelier",
            "Atelier sculpteur ballon",
            "Concert",
            "Cirque",
            "Spectacle de rue",
            "Orchestre",
            "Fanfare",
            "Banda",
            "Cinéma plein air",
            "Arbre de Noël",
            "Père Noël",
            "Animation école",
            "Animation entreprise",
            "Comité d'entreprise",
            "CSE",
            "Fête de village",
            "Spectacle à la une",
            "Animation anniversaire",
            "Anniversaire",
            "Animation familiale",
            "Conte",
            "Musique",
            "Chanson",
            "Flamenco",
            "Tango",
            "Bal",
            "DJ",
            "Boum pour enfant"
        ]
        
        # Récupérer les catégories des spectacles existants
        try:
            existing_categories = db.session.query(Show.category).filter(Show.approved.is_(True)).distinct().all()
            existing_categories_list = [c[0] for c in existing_categories if c[0]]
        except Exception:
            db.session.rollback()
            existing_categories_list = []
        
        # Combiner et trier (prédéfinies + existantes, sans doublons)
        all_categories_set = set(predefined_categories + existing_categories_list)
        categories_list = sorted(all_categories_set, key=lambda x: x.lower())
        
        return render_template(
            "admin_envoyer_demande.html", 
            demande=demande, 
            categories=categories_list,
            user=current_user()
        )


# -----------------------------------------------------
# Entrée
# -----------------------------------------------------

app = create_app()

# === ROUTE EXPORT UTILISATEURS EXCEL ===
import pandas as pd
from flask import send_file
@app.route("/admin/export-users-xlsx")
@login_required
@admin_required
def export_users_xlsx():
    users = User.query.all()
    data = []
    for u in users:
        # Prendre le premier spectacle associé (si existant)
        show = u.shows[0] if hasattr(u, 'shows') and u.shows else None
        data.append({
            "ID": u.id,
            "Nom d'utilisateur": u.username,
            "Email utilisateur": u.email if hasattr(u, 'email') else "",
            "Date création utilisateur": u.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(u, 'created_at') and u.created_at else "",
            "Admin": "VRAI" if getattr(u, "is_admin", False) else "FAUX",
            "Raison sociale": show.raison_sociale if show and show.raison_sociale else "",
            "Nom du spectacle": show.title if show else "",
            "Catégorie": show.category if show else "",
            "Âge": show.age_range if show and show.age_range else "",
            "Région": show.region if show and show.region else "",
            "Ville": show.location if show else "",
            "Email spectacle": show.contact_email if show and show.contact_email else "",
            "Téléphone": show.contact_phone if show and show.contact_phone else "",
            "Site Internet": show.site_internet if show and show.site_internet else "",
            "Date spectacle": show.date.strftime("%Y-%m-%d") if show and show.date else "",
            "Date création spectacle": show.created_at.strftime("%Y-%m-%d %H:%M") if show and show.created_at else "",
            "Spectacle approuvé": "OUI" if show and show.approved else "NON" if show else "",
            "Nombre de spectacles": len(u.shows) if hasattr(u, 'shows') and u.shows else 0
        })
    print(f"[EXPORT XLSX] {len(data)} utilisateurs exportés")
    df = pd.DataFrame(data)
    file_path = "instance/utilisateurs_export.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True, download_name="utilisateurs_export.xlsx")

# === ROUTE EXPORT SPECTACLES EXCEL ===
@app.route("/admin/export-shows-xlsx")
@login_required
@admin_required
def export_shows_xlsx():
    shows = Show.query.order_by(Show.created_at.desc()).all()
    data = []
    for show in shows:
        data.append({
            "ID": show.id,
            "Raison sociale": show.raison_sociale or "",
            "Titre": show.title,
            "Description": show.description,
            "Catégorie": show.category,
            "Âge": show.age_range or "",
            "Région": show.region or "",
            "Ville": show.location,
            "Email": show.contact_email or "",
            "Site Internet": show.site_internet or "",
            "Téléphone": show.contact_phone or "",
            "Date": show.date.strftime("%Y-%m-%d") if show.date else "",
            "Approuvé": "OUI" if show.approved else "NON",
            "Date création": show.created_at.strftime("%Y-%m-%d %H:%M") if show.created_at else "",
            "Fichier": show.file_name or ""
        })
    print(f"[EXPORT SPECTACLES XLSX] {len(data)} spectacles exportés")
    df = pd.DataFrame(data)
    file_path = "instance/spectacles_export.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True, download_name="spectacles_export.xlsx")

# ---------------------------
# SECTION ÉCOLES - Demandes thématiques pédagogiques
# ---------------------------

# Dictionnaire des thèmes avec leurs labels et emojis
THEMES_ECOLES = {
    'noel': {'label': 'Noël & Fêtes', 'emoji': '🎄'},
    'ecologie': {'label': 'Écologie & Développement durable', 'emoji': '🌍'},
    'vivre-ensemble': {'label': 'Vivre ensemble & Citoyenneté', 'emoji': '🤝'},
    'musique': {'label': 'Musique & Chant', 'emoji': '🎵'},
    'litterature': {'label': 'Langage & Littérature', 'emoji': '📚'},
    'marionnettes': {'label': 'Marionnettes', 'emoji': '🎭'},
    'inclusion': {'label': 'Différences & Inclusion', 'emoji': '🌈'},
    'theatre': {'label': 'Théâtre', 'emoji': '🎪'},
    'cultures-monde': {'label': 'Cultures du monde', 'emoji': '🌐'},
    'prevention': {'label': 'Prévention & Bien-être', 'emoji': '❤️'},
    'cirque': {'label': 'Cirque', 'emoji': '🎪'},
    'carnaval': {'label': 'Carnaval', 'emoji': '🎭'},
    'atelier-divers': {'label': 'Ateliers Créatifs', 'emoji': '🎨'},
    'autre': {'label': 'Autre thème', 'emoji': '📝'},
}

@app.route("/ecoles")
def ecoles_themes():
    """Page présentant les thèmes pédagogiques pour les écoles"""
    return render_template("ecoles_themes.html", user=current_user())

@app.route("/ecoles/demande", methods=["GET", "POST"])
def demande_ecole():
    """Formulaire de demande pour les écoles"""
    from models.models import DemandeEcole
    
    if request.method == "POST":
        # Récupération des données
        auto_datetime = request.form.get("auto_datetime", "")
        theme_principal = request.form.get("theme_principal", "").strip()
        
        # Infos école
        nom_ecole = request.form.get("nom_ecole", "").strip()
        type_etablissement = request.form.get("type_etablissement", "").strip()
        adresse = request.form.get("adresse", "").strip()
        code_postal = request.form.get("code_postal", "").strip()
        ville = request.form.get("ville", "").strip()
        region = request.form.get("region", "").strip()
        
        # Contact
        nom_contact = request.form.get("nom_contact", "").strip()
        fonction_contact = request.form.get("fonction_contact", "").strip()
        email = request.form.get("email", "").strip()
        telephone = request.form.get("telephone", "").strip()
        
        # Classes
        nombre_classes = request.form.get("nombre_classes", "").strip()
        nombre_eleves = request.form.get("nombre_eleves", "").strip()
        niveaux = request.form.getlist("niveaux")
        niveaux_concernes = ", ".join(niveaux) if niveaux else ""
        
        # Thème et objectifs
        sous_themes = request.form.getlist("sous_themes")
        sous_themes_str = ", ".join(sous_themes) if sous_themes else ""
        objectifs_pedagogiques = request.form.get("objectifs_pedagogiques", "").strip()
        
        # Animation
        types_animation = request.form.getlist("types_animation")
        types_animation_str = ", ".join(types_animation) if types_animation else ""
        
        # Contraintes
        salles = request.form.getlist("salle_disponible")
        salle_disponible = ", ".join(salles) if salles else ""
        surface_approximative = request.form.get("surface_approximative", "").strip()
        acces_electricite = request.form.get("acces_electricite", "1") == "1"
        
        # Période et budget
        periode_souhaitee = request.form.get("periode_souhaitee", "").strip()
        date_precise = request.form.get("date_precise", "").strip()
        budget = request.form.get("budget", "").strip()
        
        # Infos complémentaires
        informations_complementaires = request.form.get("informations_complementaires", "").strip()
        
        # Validation
        if not all([nom_ecole, type_etablissement, code_postal, ville, nom_contact, email, telephone, objectifs_pedagogiques]):
            flash("Veuillez remplir tous les champs obligatoires.", "danger")
            return render_template("demande_ecole.html", 
                                   user=current_user(),
                                   theme=theme_principal,
                                   theme_label=THEMES_ECOLES.get(theme_principal, {}).get('label', 'Autre'),
                                   theme_emoji=THEMES_ECOLES.get(theme_principal, {}).get('emoji', '📝')), 400
        
        # Convertir le slug du thème en label
        theme_label = THEMES_ECOLES.get(theme_principal, {}).get('label', theme_principal)
        
        # Créer la demande
        demande = DemandeEcole(
            auto_datetime=auto_datetime,
            nom_ecole=nom_ecole,
            type_etablissement=type_etablissement,
            adresse=adresse,
            code_postal=code_postal,
            ville=ville,
            region=region,
            nom_contact=nom_contact,
            fonction_contact=fonction_contact,
            email=email,
            telephone=telephone,
            nombre_classes=nombre_classes,
            nombre_eleves=nombre_eleves,
            niveaux_concernes=niveaux_concernes,
            theme_principal=theme_label,
            sous_themes=sous_themes_str,
            objectifs_pedagogiques=objectifs_pedagogiques,
            types_animation=types_animation_str,
            salle_disponible=salle_disponible,
            surface_approximative=surface_approximative,
            acces_electricite=acces_electricite,
            periode_souhaitee=periode_souhaitee,
            date_precise=date_precise,
            budget=budget,
            informations_complementaires=informations_complementaires
        )
        db.session.add(demande)
        db.session.commit()
        
        # Envoi email à l'admin si configuré
        if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
            try:
                to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                body = f"""
Nouvelle demande école - Thème pédagogique

Date de la demande : {auto_datetime}
École : {nom_ecole} ({type_etablissement})
Ville : {ville} ({code_postal})
Région : {region}

Contact : {nom_contact} ({fonction_contact})
Email : {email}
Téléphone : {telephone}

Thème : {theme_label}
Sous-thèmes : {sous_themes_str}
Objectifs pédagogiques : {objectifs_pedagogiques}

Classes : {nombre_classes} classes, {nombre_eleves} élèves
Niveaux : {niveaux_concernes}

Types d'animation souhaités : {types_animation_str}
Budget : {budget}
Période : {periode_souhaitee} ({date_precise})

Contraintes techniques :
- Salle : {salle_disponible}
- Surface : {surface_approximative}
- Électricité : {'Oui' if acces_electricite else 'Non'}

Informations complémentaires :
{informations_complementaires}
"""
                msg = Message(subject=f"Nouvelle demande école - {theme_label}", recipients=[to_addr])
                msg.body = body
                current_app.mail.send(msg)
            except Exception as e:
                print("[MAIL] envoi impossible:", e)
        
        flash("Votre demande a bien été envoyée ! Nous vous recontacterons dans les 48h avec une proposition personnalisée.", "success")
        return redirect(url_for("ecoles_themes"))
    
    # GET - Afficher le formulaire
    theme = request.args.get("theme", "autre")
    theme_data = THEMES_ECOLES.get(theme, {'label': 'Autre thème', 'emoji': '📝'})
    
    return render_template("demande_ecole.html",
                           user=current_user(),
                           theme=theme,
                           theme_label=theme_data['label'],
                           theme_emoji=theme_data['emoji'])

# Routes Admin pour les demandes d'écoles
@app.route("/admin/demandes-ecoles")
@login_required
@admin_required
def admin_demandes_ecole():
    """Liste des demandes des écoles (admin uniquement)"""
    from models.models import DemandeEcole
    
    # Filtres
    statut_filter = request.args.get("statut", "")
    theme_filter = request.args.get("theme", "")
    
    query = DemandeEcole.query
    
    if statut_filter:
        query = query.filter(DemandeEcole.statut == statut_filter)
    if theme_filter:
        theme_label = THEMES_ECOLES.get(theme_filter, {}).get('label', '')
        if theme_label:
            query = query.filter(DemandeEcole.theme_principal.ilike(f'%{theme_label}%'))
    
    demandes = query.order_by(DemandeEcole.created_at.desc()).all()
    
    # Stats
    all_demandes = DemandeEcole.query.all()
    stats = {
        'total': len(all_demandes),
        'nouvelles': len([d for d in all_demandes if d.statut == 'nouvelle']),
        'en_cours': len([d for d in all_demandes if d.statut == 'en_cours']),
        'traitees': len([d for d in all_demandes if d.statut == 'traitee']),
    }
    
    return render_template("admin_demandes_ecole.html", 
                           user=current_user(), 
                           demandes=demandes,
                           stats=stats)

@app.route("/admin/demandes-ecoles/<int:demande_id>")
@login_required
@admin_required
def admin_demande_ecole_detail(demande_id):
    """Détail d'une demande d'école"""
    from models.models import DemandeEcole
    demande = DemandeEcole.query.get_or_404(demande_id)
    return render_template("admin_demande_ecole_detail.html", 
                           user=current_user(), 
                           demande=demande)

@app.route("/admin/demandes-ecoles/<int:demande_id>/statut", methods=["POST"])
@login_required
@admin_required
def admin_demande_ecole_statut(demande_id):
    """Modifier le statut d'une demande d'école"""
    from models.models import DemandeEcole
    demande = DemandeEcole.query.get_or_404(demande_id)
    nouveau_statut = request.form.get("statut", "nouvelle")
    demande.statut = nouveau_statut
    db.session.commit()
    flash(f"Statut mis à jour : {nouveau_statut}", "success")
    return redirect(request.referrer or url_for("admin_demandes_ecole"))

@app.route("/admin/demandes-ecoles/<int:demande_id>/notes", methods=["POST"])
@login_required
@admin_required
def admin_demande_ecole_notes(demande_id):
    """Enregistrer les notes admin d'une demande d'école"""
    from models.models import DemandeEcole
    demande = DemandeEcole.query.get_or_404(demande_id)
    demande.notes_admin = request.form.get("notes_admin", "")
    db.session.commit()
    flash("Notes enregistrées.", "success")
    return redirect(url_for("admin_demande_ecole_detail", demande_id=demande_id))

# ---------------------------
# Routes SEO
# ---------------------------
from flask import redirect, url_for, abort

SEO_CATEGORIES = {
    "marionnette": "marionnette",
    "magie": "magie",
    "clown": "clown",
    "theatre": "théâtre",
    "danse": "danse",
    "spectacle-enfant": "enfant",
    "enfant": "enfant",
    "atelier": "atelier",
    "concert": "concert",
    "cirque": "cirque",
    "spectacle-de-rue": "rue",
    "rue": "rue",
    "orchestre": "orchestre",
    "arbre-de-noel": "arbre de noël",
    "animation-ecole": "animation école",
    "fete-de-village": "fête de village",
    "une": "Spectacle à la une",
}

@app.get("/<category_slug>/")
def seo_category(category_slug):
    if category_slug not in SEO_CATEGORIES:
        abort(404)
    return redirect(url_for("catalogue", category=SEO_CATEGORIES[category_slug]), code=301)

@app.get("/<category_slug>/<city_slug>/")
def seo_category_city(category_slug, city_slug):
    if category_slug not in SEO_CATEGORIES:
        abort(404)
    return redirect(
        url_for("catalogue", category=SEO_CATEGORIES[category_slug], location=city_slug),
        code=301
    )

if __name__ == "__main__":
    import os
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
