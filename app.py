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
    if os.environ.get("FLASK_ENV") != "production":
        return  # Skip validation in development
    
    warnings = []
    errors = []
    
    # Critical: SECRET_KEY must not be the default
    if app.config.get("SECRET_KEY") == "dev-secret-key":
        errors.append("SECRET_KEY is using default value. Set it in Render environment variables!")
    
    # Critical: Database should be PostgreSQL in production
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if "sqlite" in db_uri.lower():
        errors.append("DATABASE_URL not set. Using ephemeral SQLite! Set DATABASE_URL in Render.")
    
    # Warning: Admin credentials using defaults
    if app.config.get("ADMIN_USERNAME") == "admin":
        warnings.append("ADMIN_USERNAME using default 'admin'. Consider setting a custom value.")
    if app.config.get("ADMIN_PASSWORD") == "admin":
        warnings.append("ADMIN_PASSWORD using default 'admin'. Set a strong password in Render!")
    
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

    # === SÉCURITÉ ===
    
    # 1. Rate Limiting (protection contre attaques brute force) -- DÉSACTIVÉ POUR TESTS
    app.limiter = None  # type: ignore
    
    # 2. Headers de sécurité (HTTPS, XSS, etc.)
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
    
    # 3. Protection CSRF via session
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if os.environ.get("FLASK_ENV") == "production":
        app.config["SESSION_COOKIE_SECURE"] = True  # HTTPS uniquement
    
    # 4. Headers de sécurité additionnels
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

    register_routes(app)
    register_error_handlers(app)
    return app

# -----------------------------------------------------
# Utilitaires
# -----------------------------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
                    raison_sociale=raison_sociale or None,
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
                next_url = request.args.get("next")
                if next_url:
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

            new_pwd = _generate_password(10)
            user.set_password(new_pwd)
            db.session.commit()

            return render_template(
                "forgot_password.html",
                user=current_user(),
                new_password=new_pwd,
                reset_user=user.username,
            )

        return render_template("forgot_password.html", user=current_user())

    # ---------------------------
    # Accueil & listing (recherche)
    # ---------------------------
    @app.route("/", endpoint="home")
    def home():
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

        # Tri : annonces validées d'abord, puis par date
        if sort == "desc":
            shows = shows.order_by(Show.approved.desc(), Show.date.desc().nullslast(), Show.created_at.desc())
        else:
            shows = shows.order_by(Show.approved.desc(), Show.date.asc().nullsfirst(), Show.created_at.asc())

        # Pagination : 30 résultats par page
        try:
            pagination = shows.paginate(page=page, per_page=24, error_out=False)
            shows_list = pagination.items
        except Exception as e:
            current_app.logger.exception("Erreur lors de la requête /home: %s", e)
            flash("Une erreur est survenue lors de la recherche.", "danger")
            pagination = None
            shows_list = []

        categories = [c[0] for c in db.session.query(Show.category).distinct().all() if c[0]]
        locations = [l[0] for l in db.session.query(Show.location).distinct().all() if l[0]]

        return render_template(
            "home.html",
            shows=shows_list,
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
            }), 500
        
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
                contact_email=contact_email or None,
                contact_phone=contact_phone or None,
                    site_internet=site_internet or None,
                approved=False,
                user_id=current_user().id if current_user() else None,   # associer l'auteur
            )
            db.session.add(show)
            db.session.commit()

            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                try:
                    to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                    body = (
                        "🎭 Nouvelle annonce à valider\n\n"
                        f"👤 Compagnie: {raison_sociale}\n"
                        f"📌 Titre: {title}\n"
                        f"📍 Lieu: {location}\n"
                        f"🎪 Catégorie: {category}\n"
                        f"📅 Date: {date_val}\n\n"
                        f"📧 Email: {contact_email}\n"
                        f"📱 Téléphone: {contact_phone}\n"
                    )
                    msg = Message(subject="🎭 Nouvelle annonce à valider", recipients=[to_addr])  # type: ignore[arg-type]
                    msg.body = body  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                except Exception as e:  # pragma: no cover
                    print("[MAIL] envoi impossible:", e)

            flash("Annonce envoyée ! Elle sera visible après validation.", "success")
            # Rediriger vers la page d'édition du spectacle nouvellement créé
            return redirect(url_for("show_edit_self", show_id=show.id))

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
        return render_template("show_detail.html", show=show, user=u)

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

            db.session.commit()
            flash("Spectacle mis à jour.", "success")
            return redirect(url_for("company_dashboard"))

        return render_template("show_form_edit.html", show=s, user=u)

    @app.route("/my/shows/<int:show_id>/delete", methods=["POST"], endpoint="show_delete_self")
    @login_required
    def show_delete_self(show_id: int):
        s = Show.query.get_or_404(show_id)
        u = current_user()

        if not u or not (u.is_admin or s.user_id == u.id):
            flash("Accès refusé.", "danger")
            return redirect(url_for("company_dashboard"))

        if s.file_name:
            delete_file_s3(s.file_name)
            p = Path(current_app.config["UPLOAD_FOLDER"]) / s.file_name
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        db.session.delete(s)
        db.session.commit()
        flash("Spectacle supprimé.", "success")
        return redirect(request.referrer or url_for("company_dashboard"))

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
                    site_internet=site_internet or None,
                approved=False,
            )
            db.session.add(show)
            db.session.commit()
            flash("Annonce créée (en attente).", "success")
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
            show.contact_email = request.form.get("contact_email", "").strip() or None
            show.contact_phone = request.form.get("contact_phone", "").strip() or None
            date_str = request.form.get("date", "").strip()
            show.site_internet = request.form.get("site_internet", "").strip() or None
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

            db.session.commit()
            flash("Annonce mise à jour.", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("show_form_edit.html", show=show, user=current_user())

    @app.route("/admin/shows/<int:show_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def show_delete(show_id: int):
        show = Show.query.get_or_404(show_id)

        if show.file_name:
            delete_file_s3(show.file_name)
            p = Path(current_app.config["UPLOAD_FOLDER"]) / show.file_name
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
        flash("Annonce validée ✅", "success")
        return redirect(url_for("admin_dashboard"))

    # ---------------------------
    # Pages diverses
    # ---------------------------
    @app.route("/demande_animation", methods=["GET", "POST"])
    def demande_animation():
        if request.method == "POST":
            # Récupération des données du formulaire
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

            # Validation basique
            if not all([structure, telephone, lieu_ville, nom, dates_horaires, 
                       type_espace, genre_recherche, age_range, jauge, budget, contact_email]):
                flash("Veuillez remplir tous les champs obligatoires.", "danger")
                # UX: keep user on page and preserve entered values (no redirect)
                return render_template("demande_animation.html", user=current_user()), 400

            # Envoi d'email si configuré
            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                try:
                    to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                    body = f"""
Nouvelle demande d'animation

Structure: {structure}
Contact: {nom}
Téléphone: {telephone}
Email: {contact_email}
Lieu/Ville: {lieu_ville}
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

            flash("Votre demande d'animation a bien été envoyée ! Nous vous répondrons rapidement.", "success")
            return redirect(url_for("home"))

        return render_template("demande_animation.html", user=current_user())

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

# -----------------------------------------------------
# Entrée
# -----------------------------------------------------
app = create_app()

if __name__ == "__main__":
    import os
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
