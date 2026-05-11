# Import optionnel de Flask-Mail
try:
    from flask_mail import Mail, Message as MailMessage
except ImportError:
    Mail = None
    MailMessage = None
# Import optionnel de Flask-Talisman
try:
    from flask_talisman import Talisman
except ImportError:
    Talisman = None
import sys

print("=" * 70)
print("🚀 DÉMARRAGE APP.PY")
print("=" * 70)
print("PYTHON EXE:", sys.executable)
print("PYTHON VERSION:", sys.version)

from sqlalchemy import or_
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import random
import os
import logging
from logging.handlers import RotatingFileHandler
import unicodedata
import re
import socket

# Timeout global pour les connexions réseau (SMTP, etc.)
# Évite les crashs worker gunicorn quand le serveur mail ne répond pas
socket.setdefaulttimeout(15)

print("✓ Imports standards OK")

import uuid
import requests  # Pour l'API de géolocalisation

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

print("✓ Imports optionnels OK (boto3, Compress)")

# Charger les variables d'environnement du fichier .env
from dotenv import load_dotenv
load_dotenv()

print("✓ Dotenv chargé")

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    current_app,
    abort,
    jsonify
)

print("✓ Flask importé")

from config import Config
from models import db
from models.models import User, Show, PageVisit, VisitorLog, Review, Conversation, Message, ShowView, Notification
from seo_cities import FRENCH_CITIES, get_city_by_slug, get_all_city_slugs, get_neighbor_cities, get_city_seo_data, get_category_seo_data

# Imports refactorisés — utils/
from utils.files import (
    ALLOWED_EXTENSIONS, ALLOWED_MIMETYPES, allowed_file,
    secure_upload_filename, validate_file_size, optimize_image_to_webp,
    delete_file_s3, upload_file_to_s3, upload_file_local,
    generate_thumbnail,
)
from utils.security import (
    current_user, login_required, admin_required,
    generate_password as _generate_password,
    is_suspicious_request as _is_suspicious_request,
    is_bot_visitor as _is_bot_visitor_standalone,
    fix_mojibake,
)
from utils.search import normalize_search_text, generate_search_patterns
from utils.seo import SEO_CATEGORIES, optimize_title_seo
from constants import SPECIALITES, EVENEMENTS, LIEUX, REGIONS_FRANCE, REGIONS_VOISINES, PUBLICS, PUBLIC_CIBLE_CATEGORIES, PUBLIC_CIBLE_ORGANISATEUR, PUBLIC_CIBLE_ADMIN, PUBLIC_CIBLE_INCOMPATIBLES, PUBLIC_CIBLE_CODES_VALIDES

print("✓ Config, models et utils importés")

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
    print("\n📦 Entrée dans create_app()")
    
    app = Flask(__name__, instance_relative_config=True)
    
    print("✓ Instance Flask créée")

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
    # Note: Cette migration est désactivée au démarrage pour éviter de bloquer
    # le lancement si la DB n'est pas encore prête. À exécuter manuellement si nécessaire.
    # with app.app_context():
    #     try:
    #         # Vérifier et ajouter les colonnes manquantes pour les photos multiples
    #         columns_to_add = [
    #             ("file_name2", "VARCHAR(255)"),
    #             ("file_mimetype2", "VARCHAR(100)"),
    #             ("file_name3", "VARCHAR(255)"),
    #             ("file_mimetype3", "VARCHAR(100)"),
    #         ]
    #         
    #         for col_name, col_type in columns_to_add:
    #             try:
    #                 # Vérifier si la colonne existe
    #                 db.session.execute(db.text(f"SELECT {col_name} FROM shows LIMIT 1"))
    #             except Exception:
    #                 # La colonne n'existe pas, l'ajouter
    #                 try:
    #                     db.session.rollback()
    #                     db.session.execute(db.text(f"ALTER TABLE shows ADD COLUMN {col_name} {col_type}"))
    #                     db.session.commit()
    #                     app.logger.info(f"Colonne {col_name} ajoutée à la table shows")
    #                 except Exception as e:
    #                     db.session.rollback()
    #                     app.logger.warning(f"Impossible d'ajouter la colonne {col_name}: {e}")
    #     except Exception as e:
    #         app.logger.warning(f"Migration automatique échouée: {e}")

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
    
    # Fonction de détection des robots/crawlers
    def is_bot_visitor(user_agent: str, isp: str = None) -> bool:
        """Détecte si un visiteur est un robot/crawler basé sur le User-Agent et l'ISP
        
        Retourne True si c'est un robot, False sinon.
        
        Amélioration v3 : LISTE BLANCHE (whitelist) - Plus restrictif mais infaillible
        Seuls les FAI français résidentiels sont considérés humains
        """
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        
        # Liste des patterns de robots connus dans User-Agent
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'slurp', 'mediapartners',
            'googlebot', 'bingbot', 'yandexbot', 'baiduspider', 'facebookexternalhit',
            'twitterbot', 'linkedinbot', 'whatsapp', 'telegrambot', 'discordbot',
            'slackbot', 'pinterestbot', 'applebot', 'duckduckbot', 'ahrefsbot',
            'semrushbot', 'mj12bot', 'dotbot', 'rogerbot', 'exabot', 'sogou', 
            'archive.org', 'wget', 'curl', 'python-requests', 'java/', 'go-http',
            'phantom', 'headless', 'selenium', 'webdriver', 'prerender'
        ]
        
        # Vérifier si un pattern de bot est présent dans le User-Agent
        for pattern in bot_patterns:
            if pattern in user_agent_lower:
                return True
        
        # APPROCHE LISTE BLANCHE : Si pas d'ISP ou ISP inconnu = BOT
        if not isp or isp == 'N/A':
            return True  # Pas d'ISP identifié = suspect
        
        isp_lower = isp.lower()
        
        # Détection des IPs brutes (non résolues) → TOUJOURS des bots
        import re
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', isp.strip()):
            return True  # IP non résolue = bot/proxy/datacenter
        
        # LISTE BLANCHE : FAI français résidentiels UNIQUEMENT
        # Tout ce qui n'est PAS dans cette liste = BOT
        trusted_french_isps = [
            # Opérateurs principaux
            'orange',
            'proxad',  # Free
            'free sas',
            'free telecom',
            'sfr',
            'societe francaise du radiotelephone',
            'bouygues',
            'numericable',
            
            # Opérateurs secondaires français
            'la poste mobile',
            'transatel',
            'lycamobile',
            'nrj mobile',
            'coriolis',
            'completel',
            'neuf',
            'cegetel',
            'iliad',  # Maison-mère de Free
            'outremer telecom',
            
            # FAI régionaux français
            'alsatis',
            'auchan telecom',
            'adista',
            'netissime',
            'ielo',
            'k-net',
            
            # Internet satellite
            'space exploration technologies',  # Starlink
            'starlink'
        ]
        
        # Vérifier si l'ISP est dans la liste blanche
        for trusted_isp in trusted_french_isps:
            if trusted_isp in isp_lower:
                return False  # ISP français reconnu = HUMAIN
        
        # Si on arrive ici : ISP inconnu/étranger = BOT
        return True
    
    # Cache en mémoire pour la géolocalisation (évite les appels HTTP répétés)
    _geo_cache = {}  # {ip: {'data': {...}, 'timestamp': float}}
    _GEO_CACHE_TTL = 3600  # 1 heure de cache par IP
    _GEO_CACHE_MAX_SIZE = 5000  # Limite mémoire

    # Cache en mémoire pour les catégories/locations DISTINCT (catalogue)
    _catalogue_cache = {'categories': None, 'locations': None, 'timestamp': 0}
    _CATALOGUE_CACHE_TTL = 300  # 5 minutes

    # Fonction de géolocalisation IP (API gratuite ip-api.com) — AVEC CACHE
    def get_ip_geolocation(ip_address):
        """
        Récupère les informations géographiques d'une IP via l'API ip-api.com
        Retourne un dict avec city, region, country, isp
        Utilise un cache en mémoire pour éviter les appels répétés.
        """
        import time as _time

        # Vérifier le cache
        cached = _geo_cache.get(ip_address)
        if cached and (_time.time() - cached['timestamp']) < _GEO_CACHE_TTL:
            return cached['data']

        try:
            # API gratuite : 45 requêtes/minute sans clé
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                params={"fields": "city,regionName,country,isp,status"},
                timeout=2  # 2 secondes max
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result = {
                        'city': data.get('city', ''),
                        'region': data.get('regionName', ''),
                        'country': data.get('country', ''),
                        'isp': data.get('isp', '')
                    }
                    # Stocker en cache (avec nettoyage si trop gros)
                    if len(_geo_cache) >= _GEO_CACHE_MAX_SIZE:
                        _geo_cache.clear()
                    _geo_cache[ip_address] = {'data': result, 'timestamp': _time.time()}
                    return result
        except Exception as e:
            app.logger.warning(f"[GEO] Erreur géolocalisation pour {ip_address}: {e}")
        
        # En cas d'erreur, retourner des valeurs vides (et cacher pour éviter de re-tenter en boucle)
        fallback = {'city': None, 'region': None, 'country': None, 'isp': None}
        _geo_cache[ip_address] = {'data': fallback, 'timestamp': _time.time()}
        return fallback
    
    # 6. Tracking des visiteurs (anonymisé, conforme RGPD) — OPTIMISÉ
    @app.before_request
    def track_visitor():
        """Enregistre chaque visite de manière anonymisée (conforme RGPD)"""
        # Ne pas tracker les fichiers statiques, robots et pages admin
        if (request.path.startswith('/static/') or 
            request.path.startswith('/robots.txt') or 
            request.path.startswith('/admin') or
            request.path.startswith('/favicon')):
            return

        # Ne pas tracker les visites de l'admin connecte (evite de polluer les stats)
        try:
            uid = session.get('user_id')
            if uid:
                u = User.query.get(uid)
                if u and getattr(u, 'is_admin', False):
                    return
        except Exception:
            pass

        try:
            # Récupérer la vraie IP du visiteur (derrière proxy/load balancer)
            ip = None
            
            # 1. X-Forwarded-For (standard proxy/load balancer)
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                ip = forwarded_for.split(',')[0].strip()
            
            # 2. X-Real-IP (utilisé par Nginx et certains proxies)
            if not ip or ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                real_ip = request.headers.get('X-Real-IP')
                if real_ip:
                    ip = real_ip.strip()
            
            # 3. CF-Connecting-IP (Cloudflare)
            if not ip or ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                cf_ip = request.headers.get('CF-Connecting-IP')
                if cf_ip:
                    ip = cf_ip.strip()
            
            # 4. Fallback sur remote_addr
            if not ip or ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                ip = request.remote_addr or '0.0.0.0'
            
            # Anonymiser l'IP (garder seulement les 2 premiers octets) - RGPD compliant
            ip_parts = ip.split('.')
            if len(ip_parts) == 4:
                ip_anonymized = f"{ip_parts[0]}.{ip_parts[1]}.0.0"
            else:
                ip_anonymized = "0.0.0.0"
            
            # Créer ou récupérer un identifiant de session anonyme
            if 'visitor_id' not in session:
                session['visitor_id'] = str(uuid.uuid4())
                app.logger.info(f"[TRACKING] Nouveau visiteur - IP: {ip_anonymized}")
            
            # Récupérer l'utilisateur connecté (si applicable)
            user_id = session.get('user_id')
            
            # Géolocaliser l'IP (AVEC CACHE — pas d'appel HTTP si déjà connu)
            geo_data = get_ip_geolocation(ip)
            
            # Détecter si c'est un robot/crawler
            user_agent_str = request.headers.get('User-Agent', '')[:300]
            is_bot = is_bot_visitor(user_agent_str, geo_data['isp'])
            
            # Utiliser la session pour anti-refresh (évite une requête DB)
            session_id = session.get('visitor_id')
            last_track_page = session.get('_last_track_page')
            last_track_time = session.get('_last_track_time', 0)
            now_ts = datetime.utcnow().timestamp()
            
            # Si même page visitée il y a moins de 10 secondes : c'est un refresh
            if (last_track_page == request.path and 
                (now_ts - last_track_time) < 10):
                return
            
            # Détection par comportement : >10 pages visitées = bot (scraper)
            # Utiliser un compteur en session au lieu d'un COUNT(*) en DB
            page_count = session.get('_page_count', 0) + 1
            session['_page_count'] = page_count
            
            if session_id and not is_bot and page_count >= 10:
                is_bot = True
                app.logger.info(f"[TRACKING] Session {session_id[:20]}... marquée BOT - {page_count} pages")
            
            # Mettre à jour la session pour l'anti-refresh
            session['_last_track_page'] = request.path
            session['_last_track_time'] = now_ts
            
            # Enregistrer la visite
            visitor_log = VisitorLog(
                page_url=request.path[:300],
                referrer=request.referrer[:300] if request.referrer else None,
                user_agent=user_agent_str,
                ip_anonymized=ip_anonymized,
                session_id=session_id,
                user_id=user_id,
                city=geo_data['city'],
                region=geo_data['region'],
                country=geo_data['country'],
                isp=geo_data['isp'],
                is_bot=is_bot
            )
            db.session.add(visitor_log)
            db.session.commit()
        except Exception as e:
            # Ne pas bloquer le site si le tracking échoue
            app.logger.warning(f"[TRACKING] Erreur lors de l'enregistrement: {e}")
            db.session.rollback()
    
    # 7. Headers de sécurité additionnels
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
        
        # Cache HTTP pour les images uploadées (1 jour)
        if request.path.startswith('/uploads/'):
            response.headers['Cache-Control'] = 'public, max-age=86400'
        
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
        _run_critical_migrations(app)
        _bootstrap_admin(app)

    # Filtre Jinja2 pour formater les âges
    @app.template_filter('format_age')
    def format_age(value):
        """Affiche un libellé court et lisible pour la valeur age_range.

        Utilise d'abord PUBLICS (nouveaux codes) puis PUBLICS_LEGACY_LABELS,
        sinon fallback sur l'ancien comportement (regex)."""
        if not value:
            return value
        v = str(value).strip().lower()
        # Libellés courts pour l'affichage compact des cartes
        short_labels = {
            "jp_0_3":   "Jeune public 0/3 ans",
            "jp_4_8":   "Jeune public 4/8 ans",
            "jp_7_11":  "Jeune public 7/11 ans",
            "jp_8_11":  "Jeune public 5/11 ans",
            "jp_des_3": "Jeune public dès 3 ans",
            "anim_div": "Animations diverses",
            "ad_12":    "Adulte 12 ans+",
            "ad_16":    "Adulte 16 ans+",
            "fam_2":    "Famille dès 2 ans",
            "fam_3":    "Familial dès 3 ans",
            "fam_8":    "Familial dès 8 ans",
        }
        if v in short_labels:
            return short_labels[v]
        # Fallback ancien (enfant_2_10 → enfant 2/10ans)
        import re
        out = re.sub(r'_(\d+)_(\d+)(ans)?', r' \1/\2', value)
        out = re.sub(r's_(\d+)_(\d+)(ans)?', r's \1/\2', out)
        out = out.replace('_', ' ')
        if re.search(r'\d', out) and not out.endswith('ans'):
            out += 'ans'
        return out

    # Filtre Public Cible v2 : produit un texte court à partir des CSV
    # public_categories + public_sous_options. Fallback sur format_age si vide.
    _PC_CAT_LABELS = {cat["code"]: cat["label"] for cat in PUBLIC_CIBLE_CATEGORIES}
    _PC_SUB_LABELS = {}
    for _cat in PUBLIC_CIBLE_CATEGORIES:
        for _code, _label in _cat["sous_options"]:
            _PC_SUB_LABELS[_code] = _label

    # Libellés courts par code de catégorie (pour affichage compact sur les cartes)
    _PC_SHORT = {
        "enfants": "Enfants",
        "famille": "Famille",
        "adultes": "Adultes",
    }

    @app.template_filter('format_public_cible')
    def format_public_cible(show):
        """Retourne un libellé compact du public ciblé, ex.:
        'Famille (dès 3 ans)' ou 'Enfants (Maternelle, Élémentaire) · Famille (dès 3 ans)'.
        Si aucune donnée v2, retourne le format_age sur show.age_range.
        """
        cats_csv = getattr(show, 'public_categories', None)
        subs_csv = getattr(show, 'public_sous_options', None)
        if not cats_csv:
            return format_age(getattr(show, 'age_range', None))
        cats = [c.strip() for c in cats_csv.split(',') if c.strip()]
        subs = set(s.strip() for s in (subs_csv or '').split(',') if s.strip())
        parts = []
        for cat_code in cats:
            short = _PC_SHORT.get(cat_code, cat_code.capitalize())
            cat_subs = []
            for sub_code, sub_label in [(s, _PC_SUB_LABELS.get(s)) for s in subs]:
                if sub_label and sub_code in [c[0] for c in next((cat["sous_options"] for cat in PUBLIC_CIBLE_CATEGORIES if cat["code"] == cat_code), [])]:
                    # Sous-libellé court : enlever préfixes "Dès X ans" reste, mais "Spectacle adulte à partir de" → "Dès X ans"
                    short_sub = sub_label.replace("Spectacle adulte à partir de ", "Dès ").replace("Toute la famille à partir de ", "Famille dès ")
                    cat_subs.append(short_sub)
            if cat_subs:
                parts.append(f"{short} ({', '.join(cat_subs)})")
            else:
                parts.append(short)
        return " · ".join(parts)

    # Context processor pour les spectacles à la une (diaporama header)
    @app.context_processor
    def inject_featured_shows():
        """Injecte les spectacles à la une avec images pour le diaporama header"""
        try:
            # Uniquement les spectacles de la catégorie "à la une" OU avec is_featured=True
            featured = Show.query.filter(
                Show.approved.is_(True),
                Show.file_mimetype.ilike("image/%"),
                or_(
                    Show.category.ilike('%à la une%'),
                    Show.category.ilike('%a la une%'),
                    Show.is_featured.is_(True)
                )
            ).order_by(Show.created_at.desc()).all()
            
            return {'header_featured_shows': featured}
        except Exception:
            db.session.rollback()
            return {'header_featured_shows': []}

    @app.context_processor
    def inject_thumbnail_url():
        """Fournit thumbnail_url() et original_url() — URLs S3 directes dans le HTML."""
        _state = {}
        _cache = {}

        def _ensure_s3():
            if 'done' not in _state:
                s3_bucket = current_app.config.get("S3_BUCKET")
                if s3_bucket and current_app.config.get("S3_KEY") and boto3:
                    from utils.files import _s3_client
                    _state['client'] = _s3_client()
                    _state['bucket'] = s3_bucket
                _state['done'] = True

        def thumbnail_url(filename):
            if not filename:
                return ''
            if filename in _cache:
                return _cache[filename]
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
                r = url_for('uploaded_file', filename=filename)
                _cache[filename] = r
                return r
            _ensure_s3()
            client = _state.get('client')
            bucket = _state.get('bucket')
            if client and bucket:
                thumb_key = "thumb_" + filename.rsplit(".", 1)[0] + ".webp"
                try:
                    r = client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket, 'Key': thumb_key},
                        ExpiresIn=3600
                    )
                    _cache[filename] = r
                    return r
                except Exception:
                    pass
            r = url_for('thumbnail_file', filename=filename)
            _cache[filename] = r
            return r

        def original_url(filename):
            if not filename:
                return ''
            _ensure_s3()
            client = _state.get('client')
            bucket = _state.get('bucket')
            if client and bucket:
                try:
                    return client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket, 'Key': filename},
                        ExpiresIn=3600
                    )
                except Exception:
                    pass
            return url_for('uploaded_file', filename=filename)

        return {'thumbnail_url': thumbnail_url, 'original_url': original_url}

    @app.context_processor
    def inject_user_has_show():
        """Indique si l'utilisateur connecté a au moins un spectacle approuvé."""
        u = current_user()
        if not u:
            return {'user_has_show': False}
        if u.is_admin:
            return {'user_has_show': True}
        has = Show.query.filter(
            Show.user_id == u.id,
            Show.approved.is_(True)
        ).count() > 0
        return {'user_has_show': has}

    @app.context_processor
    def inject_public_cible():
        return {
            'PUBLIC_CIBLE_CATEGORIES': PUBLIC_CIBLE_CATEGORIES,
            'PUBLIC_CIBLE_ORGANISATEUR': PUBLIC_CIBLE_ORGANISATEUR,
            'PUBLIC_CIBLE_ADMIN': PUBLIC_CIBLE_ADMIN,
            'PUBLIC_CIBLE_INCOMPATIBLES': PUBLIC_CIBLE_INCOMPATIBLES,
        }

    register_routes(app)
    register_error_handlers(app)
    return app

# -----------------------------------------------------------------
# NOTE : Les utilitaires ci-dessous ont été extraits dans utils/.
# Les imports en haut du fichier (utils.files, utils.security,
# utils.search, utils.seo) rendent ces fonctions disponibles
# dans tout le code applicatif.
# -----------------------------------------------------------------
def _run_critical_migrations(app: Flask) -> None:
    """
    Exécute les migrations critiques nécessaires au démarrage.
    Utilise du SQL brut pour éviter les problèmes avec les modèles SQLAlchemy.
    db.create_all() ne crée PAS les colonnes manquantes sur des tables existantes,
    donc on le fait manuellement ici.
    """
    from sqlalchemy import text

    # Colonnes à garantir : (table, colonne, type_postgres, type_sqlite, default)
    REQUIRED_COLUMNS = [
        # ── users ──
        ("users", "site_internet", "VARCHAR(255)", "VARCHAR(255)", None),
        ("users", "code_postal", "VARCHAR(10)", "VARCHAR(10)", None),
        ("users", "ville", "VARCHAR(150)", "VARCHAR(150)", None),
        ("users", "departement", "VARCHAR(100)", "VARCHAR(100)", None),
        # ── shows ──
        ("shows", "file_name2", "VARCHAR(255)", "VARCHAR(255)", None),
        ("shows", "file_mimetype2", "VARCHAR(120)", "VARCHAR(120)", None),
        ("shows", "file_name3", "VARCHAR(255)", "VARCHAR(255)", None),
        ("shows", "file_mimetype3", "VARCHAR(120)", "VARCHAR(120)", None),
        ("shows", "is_featured", "BOOLEAN DEFAULT FALSE", "BOOLEAN DEFAULT 0", "FALSE"),
        ("shows", "is_event", "BOOLEAN DEFAULT FALSE", "BOOLEAN DEFAULT 0", "FALSE"),
        ("shows", "display_order", "INTEGER DEFAULT 0", "INTEGER DEFAULT 0", "0"),
        ("shows", "site_internet", "VARCHAR(255)", "VARCHAR(255)", None),
        ("shows", "specialites", "TEXT", "TEXT", None),
        ("shows", "evenements", "TEXT", "TEXT", None),
        ("shows", "lieux_intervention", "TEXT", "TEXT", None),
        ("shows", "regions_intervention", "TEXT", "TEXT", None),
        ("shows", "public_categories", "TEXT", "TEXT", None),
        ("shows", "public_sous_options", "TEXT", "TEXT", None),
        # ── demande_animation ──
        ("demande_animation", "is_private", "BOOLEAN DEFAULT FALSE", "BOOLEAN DEFAULT 0", "FALSE"),
        ("demande_animation", "approved", "BOOLEAN DEFAULT FALSE", "BOOLEAN DEFAULT 0", "FALSE"),
        ("demande_animation", "portee_nationale", "BOOLEAN DEFAULT TRUE", "BOOLEAN DEFAULT 1", "TRUE"),
        ("demande_animation", "specialites_recherchees", "TEXT", "TEXT", None),
        ("demande_animation", "evenements_contexte", "TEXT", "TEXT", None),
        ("demande_animation", "lieux_souhaites", "TEXT", "TEXT", None),
        ("demande_animation", "date_debut", "VARCHAR(20)", "VARCHAR(20)", None),
        ("demande_animation", "date_fin", "VARCHAR(20)", "VARCHAR(20)", None),
        ("demande_animation", "public_categories", "TEXT", "TEXT", None),
        ("demande_animation", "public_sous_options", "TEXT", "TEXT", None),
        # ── users ──
        ("users", "pending_deletion_at", "TIMESTAMP", "DATETIME", None),
    ]

    is_pg = 'postgresql' in str(db.engine.url)

    try:
        with db.engine.connect() as conn:
            for table, column, pg_type, sqlite_type, _default in REQUIRED_COLUMNS:
                try:
                    if is_pg:
                        result = conn.execute(text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = :t AND column_name = :c"
                        ), {"t": table, "c": column})
                        if not result.fetchone():
                            col_def = pg_type
                            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_def}'))
                            conn.commit()
                            app.logger.info(f"[MIGRATION] ✓ {table}.{column} ajoutée (PG)")
                    else:
                        result = conn.execute(text(f'PRAGMA table_info("{table}")'))
                        columns = [row[1] for row in result.fetchall()]
                        if column not in columns:
                            col_def = sqlite_type
                            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_def}'))
                            conn.commit()
                            app.logger.info(f"[MIGRATION] ✓ {table}.{column} ajoutée (SQLite)")
                except Exception as col_err:
                    app.logger.warning(f"[MIGRATION] {table}.{column}: {col_err}")

    except Exception as e:
        app.logger.warning(f"[MIGRATION] Erreur générale: {e}")

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

    @app.errorhandler(413)
    def request_entity_too_large(e):
        max_mb = (app.config.get("MAX_CONTENT_LENGTH") or 0) // (1024 * 1024)
        flash(
            f"📦 Fichier(s) trop volumineux : la taille totale de votre envoi dépasse {max_mb} Mo. "
            f"Compressez vos photos (par ex. via https://squoosh.app) puis réessayez.",
            "danger",
        )
        # Tenter de revenir à la page précédente, sinon dashboard
        try:
            ref = request.referrer
            if ref:
                return redirect(ref)
        except Exception:
            pass
        return redirect(url_for("home"))
    
    # Gestionnaire d'erreur CSRF
    try:
        from flask_wtf.csrf import CSRFError
        
        @app.errorhandler(CSRFError)
        def handle_csrf_error(e):
            """Gère les erreurs CSRF (token expiré ou invalide) de manière conviviale"""
            app.logger.warning(f"Erreur CSRF: {e.description}")
            # Redirection vers la page précédente avec un message flash
            flash("Votre session a expiré. Veuillez réessayer.", "warning")
            # Rediriger vers la page de provenance ou vers l'accueil
            referrer = request.referrer or url_for('home')
            return redirect(referrer)
    except ImportError:
        app.logger.warning("CSRFError non disponible - gestionnaire CSRF non enregistré")
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Rollback global pour toute exception non gérée
        try:
            db.session.rollback()
        except Exception:
            pass
        app.logger.exception("Erreur non gérée: %s", e)
        return render_template("500.html", user=current_user()), 500


def _build_appel_offre_email(demande, show):
    """Génère le HTML d'email pour un appel d'offre envoyé à un artiste."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
.content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
h2 {{ color: #1b2a4e; margin-top: 0; }}
.opportunity-box {{ background: #e8f5e9; border: 1px solid #a5d6a7; color: #1b5e20; padding: 20px; border-radius: 8px; margin: 20px 0; }}
.opportunity-box h3 {{ margin-top: 0; color: #1b5e20; }}
.info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
.info-item {{ background-color: rgba(255,255,255,0.6); padding: 10px; border-radius: 5px; }}
.info-label {{ font-weight: bold; font-size: 0.9em; }}
.contact-box {{ background-color: #fff; padding: 15px; border-left: 4px solid #2e7d32; margin: 15px 0; }}
.footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
.btn {{ display: inline-block; padding: 12px 24px; background-color: #1b5e20; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
</style>
</head>
<body>
<div style="text-align:center;margin:20px 0;">
    <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre" style="max-width:200px;">
</div>
<div class="content">
    <h2>Nouvelle Opportunité à {demande.lieu_ville}</h2>
    <p>Bonjour,</p>
    <p>Bonne nouvelle ! Nous avons reçu une demande d'animation pour <strong>{demande.genre_recherche}</strong> qui correspond à votre profil :</p>
    <div class="opportunity-box">
        <h3>📋 {demande.genre_recherche} à {demande.lieu_ville}</h3>
        <div class="info-grid">
            <div class="info-item"><div class="info-label">📍 Lieu</div>{demande.lieu_ville}</div>
            <div class="info-item"><div class="info-label">📅 Date(s)</div>{demande.dates_horaires}</div>
            <div class="info-item"><div class="info-label">Type recherché</div>{demande.genre_recherche}</div>
            <div class="info-item"><div class="info-label">🎭 Spécialités</div>{demande.specialites_recherchees.replace(',', ', ') if demande.specialites_recherchees else 'Non précisées'}</div>
            <div class="info-item"><div class="info-label">👥 Jauge</div>{demande.jauge}</div>
            <div class="info-item"><div class="info-label">💰 Budget</div>{demande.budget}</div>
            <div class="info-item"><div class="info-label">👶 Public</div>{demande.age_range}</div>
        </div>
        <p><strong>🏢 Type d'espace :</strong> {demande.type_espace}</p>
        <p style="color:#333;"><strong>📝 Intitulé :</strong> {demande.intitule or 'Non précisé'}</p>
        <p><strong>♿ Accessibilité :</strong> {demande.accessibilite or 'Non précisée'}</p>
    </div>
    <div class="contact-box">
        <h3>📞 Coordonnées du demandeur</h3>
        <p><strong>Structure :</strong> {demande.structure}<br>
        <strong>Contact :</strong> {demande.nom}<br>
        <strong>Email :</strong> <a href="mailto:{demande.contact_email}" style="color:#1b5e20;">{demande.contact_email}</a><br>
        <strong>Téléphone :</strong> {demande.telephone}</p>
        <p style="text-align:center;"><a href="mailto:{demande.contact_email}" class="btn">✉️ Contacter le demandeur</a></p>
        <p style="text-align:center;margin-top:8px;"><a href="https://www.spectacleanimation.fr/demandes-animation" style="display:inline-block;padding:10px 24px;background:#1b5e20;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">👁️ Voir l'appel d'offre</a></p>
    </div>
    <div style="background-color:#e8eaf6;padding:15px;border-radius:8px;margin:15px 0;">
        <p><strong>✨ Votre spectacle concerné :</strong><br>{show.title} - {show.category}</p>
    </div>
    <div style="background-color:#e3f2fd;padding:15px;border-radius:8px;margin:15px 0;text-align:center;">
        <p><strong>Publiez vos spectacles GRATUITEMENT toute l'année !</strong><br>
        <a href="https://www.spectacleanimation.fr/submit" style="color:#1b5e20;font-weight:bold;">👉 Publier un spectacle</a></p>
    </div>
    <div style="background:linear-gradient(135deg,#d32f2f 0%,#c62828 100%);color:white;padding:20px;border-radius:8px;margin:15px 0;">
        <p style="margin:0 0 10px 0;font-size:1.1em;"><strong>💼 SPECTACLE'MENT VÔTRE VOUS ACCOMPAGNE</strong></p>
        <p style="margin:0 0 15px 0;font-size:0.95em;">Gestion administrative : URSSAF, DSN, DUE, AEM, fiches de salaire, contrats de cession...</p>
        <p style="text-align:center;margin:0;"><a href="https://spectacleanimation.fr/abonnement-compagnie" style="display:inline-block;background-color:white;color:#d32f2f;padding:12px 28px;border-radius:25px;text-decoration:none;font-weight:bold;">📋 Découvrir nos services</a></p>
    </div>
    <div class="footer"><p><strong>L'équipe Spectacle'ment VØtre</strong><br>contact@spectacleanimation.fr</p></div>
</div>
</body>
</html>"""


def _send_recap_to_organisateur(demande, shows_contactes):
    """Envoie un email récap court à l'organisateur de la demande, avec les liens
    des fiches des artistes/spectacles qui ont été contactés.

    - shows_contactes : liste d'objets Show réellement ciblés par l'envoi
    - Silencieux en cas d'erreur (ne doit jamais bloquer l'envoi principal).
    """
    try:
        if not demande or not getattr(demande, "contact_email", None):
            print("[RECAP] Pas d'email organisateur, recap ignoré")
            return False
        if not getattr(current_app, "mail", None):
            print("[RECAP] Mail non configuré, recap ignoré")
            return False
        # Dédoublonnage par show.id
        unique_shows = []
        seen_ids = set()
        for s in (shows_contactes or []):
            if s and s.id not in seen_ids:
                seen_ids.add(s.id)
                unique_shows.append(s)
        if not unique_shows:
            print("[RECAP] Aucun show à lister, recap ignoré")
            return False

        # Construire les lignes de fiches
        rows_html = ""
        for s in unique_shows:
            try:
                show_url = url_for("show_detail", show_id=s.id, _external=True)
            except Exception:
                show_url = f"https://www.spectacleanimation.fr/show/{s.id}"
            cie_name = ""
            if getattr(s, "user", None):
                cie_name = (s.user.company_name or s.user.email or "") if hasattr(s.user, "company_name") else ""
            cie_html = f' <span style="color:#777;font-size:0.9em;">— {cie_name}</span>' if cie_name else ""
            rows_html += (
                f'<li style="margin:8px 0;">'
                f'<a href="{show_url}" style="color:#8b1e1e;font-weight:700;text-decoration:none;">'
                f'🎭 {s.title}</a>{cie_html}<br>'
                f'<a href="{show_url}" style="color:#888;font-size:0.85em;text-decoration:none;">{show_url}</a>'
                f'</li>'
            )

        nb = len(unique_shows)
        intitule = (demande.intitule or demande.genre_recherche or "Votre demande d'animation")
        lieu = demande.lieu_ville or ""
        dates = demande.dates_horaires or ""

        body_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;color:#333;background:#fafafa;">
  <div style="text-align:center;margin:18px 0;">
    <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre" style="max-width:180px;">
  </div>
  <div style="background:linear-gradient(135deg,#1a0a0a 0%,#3d1a1a 50%,#1a0a0a 100%);color:#ffc107;padding:18px 22px;border-radius:10px 10px 0 0;text-align:center;">
    <h2 style="margin:0;font-size:1.25em;">✅ Votre demande a été transmise</h2>
  </div>
  <div style="background:#fff;padding:22px;border-radius:0 0 10px 10px;border:1px solid #eee;border-top:none;">
    <p>Bonjour {demande.nom or ''},</p>
    <p>Bonne nouvelle&nbsp;! Votre appel d'offre a été <strong>transmis à {nb} artiste{'s' if nb > 1 else ''}</strong> correspondant à vos critères.</p>

    <div style="background:#fdf6e3;border-left:4px solid #ffc107;padding:12px 14px;border-radius:6px;margin:16px 0;font-size:0.92em;">
      <strong>📋 Récap de votre demande :</strong><br>
      🎯 {intitule}<br>
      📍 {lieu}{(' — ' + dates) if dates else ''}
    </div>

    <h3 style="color:#8b1e1e;margin:18px 0 8px 0;font-size:1.05em;">🎭 Artistes contactés ({nb})</h3>
    <p style="font-size:0.9em;color:#555;margin:0 0 8px 0;">
      Vous pouvez consulter leurs fiches dès maintenant. Les artistes intéressés vous recontacteront directement
      par email ou via la messagerie de la plateforme.
    </p>
    <ul style="list-style:none;padding-left:0;margin:10px 0;">
      {rows_html}
    </ul>

    <div style="background:#f5f5f5;padding:12px 14px;border-radius:6px;margin-top:18px;font-size:0.88em;color:#555;">
      💡 <strong>Astuce :</strong> n'hésitez pas à contacter directement les artistes qui vous intéressent
      pour échanger sur les détails (devis, disponibilités, options).
    </div>

    <p style="text-align:center;margin-top:22px;color:#888;font-size:0.85em;">
      Spectacle'ment Vôtre<br>
      <a href="https://www.spectacleanimation.fr" style="color:#8b1e1e;text-decoration:none;">spectacleanimation.fr</a>
      &nbsp;·&nbsp;<a href="mailto:contact@spectacleanimation.fr" style="color:#8b1e1e;text-decoration:none;">contact@spectacleanimation.fr</a>
    </p>
  </div>
</body>
</html>"""

        admin_email = current_app.config.get("MAIL_USERNAME", "contact@spectacleanimation.fr")
        msg = MailMessage(
            subject=f"✅ Votre demande a été transmise à {nb} artiste{'s' if nb > 1 else ''}",
            recipients=[demande.contact_email],
        )
        msg.html = body_html
        current_app.mail.send(msg)
        print(f"[RECAP] ✅ Récap envoyé à organisateur {demande.contact_email} ({nb} fiches)")
        # Copie admin (mail séparé si adresse différente)
        if admin_email and admin_email != demande.contact_email:
            try:
                admin_copy = MailMessage(
                    subject=f"[COPIE ADMIN] Récap transmis à {demande.contact_email} — {nb} fiche(s)",
                    recipients=[admin_email],
                )
                admin_copy.html = body_html
                current_app.mail.send(admin_copy)
                print(f"[RECAP] ✅ Copie admin envoyée à {admin_email}")
            except Exception as ae:
                print(f"[RECAP] ⚠️ Copie admin échouée (non bloquant): {ae}")
        return True
    except Exception as e:
        print(f"[RECAP] ⚠️ Erreur envoi récap organisateur: {e}")
        return False


# -----------------------------------------------------
# Routes
# -----------------------------------------------------
def register_routes(app: Flask) -> None:
    # ---------------------------
    # API - Suggestions SEO Intelligence Artificielle
    # ---------------------------
    @app.route("/api/seo-suggest", methods=["POST"])
    def api_seo_suggest():
        """API endpoint pour obtenir des suggestions SEO intelligentes en temps réel."""
        try:
            data = request.get_json() or {}
            title = data.get("title", "").strip()
            category = data.get("category", "").strip()
            location = data.get("location", "").strip()
            age_range = data.get("age_range", "").strip()
            
            if not title:
                return jsonify({"error": "Titre requis"}), 400
            
            # Obtenir les suggestions SEO optimisées
            result = optimize_title_seo(title, category, location, age_range)
            
            return jsonify({
                "success": True,
                "data": result
            }), 200
            
        except Exception as e:
            app.logger.exception(f"Erreur API SEO: {e}")
            return jsonify({"error": "Erreur serveur"}), 500
    
    # ---------------------------
    # Route de test d'envoi de mail (à la fin pour éviter les erreurs)
    # ---------------------------
    @app.route("/test-mail")
    def test_mail():
        if not hasattr(app, "mail") or not app.mail:
            return "Mail non configuré.", 500
        try:
            msg = MailMessage(
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
            # Honeypot anti-bot : si le champ "website" est rempli, c'est un bot
            if request.form.get("website", ""):
                # Simuler un succès pour ne pas alerter le bot
                flash("Votre compte a été créé avec succès.", "success")
                return redirect(url_for("login"))

            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            email = request.form.get("email", "").strip()
            telephone = request.form.get("telephone", "").strip()
            raison_sociale = request.form.get("raison_sociale", "").strip()
            region = fix_mojibake(request.form.get("region", "").strip())
            code_postal = request.form.get("code_postal", "").strip()
            ville = fix_mojibake(request.form.get("ville", "").strip())
            departement = fix_mojibake(request.form.get("departement", "").strip())
            site_internet = request.form.get("site_internet", "").strip()

            if not username or not password or not email:
                flash("Veuillez remplir tous les champs obligatoires.", "danger")
                return render_template("register.html")

            if not raison_sociale:
                flash("La raison sociale est obligatoire.", "danger")
                return render_template("register.html")

            if not region:
                flash("La région est obligatoire.", "danger")
                return render_template("register.html")

            # Validation du mot de passe (minimum 6 caractères)
            if len(password) < 6:
                flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
                return render_template("register.html")

            # Vérifier si le nom d'utilisateur existe déjà
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Ce nom d'utilisateur est déjà utilisé. Si c'est votre compte, essayez de vous connecter ou utilisez 'Mot de passe oublié'.", "warning")
                return render_template("register.html")
            
            # Vérifier si l'email existe déjà
            if email:
                existing_email = User.query.filter_by(email=email).first()
                if existing_email:
                    flash("Cette adresse email est déjà utilisée. Si c'est votre compte, essayez de vous connecter ou utilisez 'Mot de passe oublié'.", "warning")
                    return render_template("register.html")

            try:
                user = User(
                    username=username,
                    email=email or None,
                    raison_sociale=raison_sociale or None,
                    region=region or None,
                    code_postal=code_postal or None,
                    ville=ville or None,
                    departement=departement or None,
                    telephone=telephone or None,
                    site_internet=site_internet or None,
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

                # Envoi d'un email à l'admin avec le pédigrée du nouvel utilisateur
                if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
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
                        msg = MailMessage(subject="Nouvelle inscription utilisateur", recipients=[to_addr])  # type: ignore[arg-type]
                        msg.body = body  # type: ignore[assignment]
                        current_app.mail.send(msg)  # type: ignore[attr-defined]
                        current_app.logger.info(f"[MAIL] ✓ Email envoyé à l'admin pour inscription de {username}")
                    except Exception as e:
                        current_app.logger.error(f"[MAIL] ✗ Envoi impossible (inscription admin): {e}")
                        print("[MAIL] envoi impossible (inscription admin):", e)
                    
                    # Envoi d'un email de bienvenue à l'utilisateur
                    if email:
                        try:
                            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .logo {{ text-align: center; margin: 20px 0; }}
        .logo img {{ max-width: 200px; height: auto; }}
        .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
        h2 {{ color: #1b2a4e; }}
        .highlight {{ background-color: #fff; padding: 15px; border-left: 4px solid #6a1b9a; margin: 15px 0; }}
        ul {{ list-style: none; padding-left: 0; }}
        ul li {{ padding: 5px 0; }}
        ul li:before {{ content: "• "; color: #6a1b9a; font-weight: bold; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
        .btn {{ display: inline-block; padding: 12px 24px; background-color: #6a1b9a; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
    </style>
</head>
<body>
    <div class="logo">
        <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre">
    </div>
    <div class="content">
        <h2>Bonjour {username},</h2>
        <p><strong>Bienvenue sur Spectacle'ment VØtre !</strong></p>
        <p>Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter et :</p>
        <ul>
            <li>Publier vos spectacles et animations <strong>GRATUITEMENT toute l'année</strong></li>
            <li>Annoncer vos événements sans limite de temps : <a href="https://www.spectacleanimation.fr/submit" style="color: #6a1b9a; font-weight: bold;">Publiez ici</a></li>
            <li>Bénéficier d'une visibilité renforcée auprès de notre réseau d'acheteurs</li>
            <li>Profiter de notre diffusion gratuite auprès de plus de 100 000 contacts professionnels</li>
        </ul>
        <p style="text-align: center;">
            <a href="https://www.spectacleanimation.fr/submit" class="btn">👉 Publiez votre spectacle</a>
            <a href="https://www.spectacleanimation.fr/login" class="btn">Se connecter</a>
        </p>
        <p><strong>Nom d'utilisateur :</strong> {username}</p>
        <div style="background:#e8f5e9; border-left:4px solid #2e7d32; padding:18px 20px; border-radius:6px; margin:20px 0;">
            <h3 style="margin:0 0 10px 0; color:#2e7d32; font-size:1.05em;">💚 Pourquoi c'est gratuit ?</h3>
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; line-height:1.6;">
                Spectacle'ment VØtre fonctionne comme un <strong>annuaire national de référence</strong> : plus il y a de spectacles publiés, plus les <strong>mairies, écoles, CSE, agences et organisateurs</strong> prennent l'habitude d'y chercher leurs animations &mdash; et d'y déposer leurs <strong>appels d'offres</strong>.
            </p>
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; line-height:1.6;">
                📍 <strong>Au niveau local</strong>, votre département gagne en visibilité à mesure que des compagnies de la région s'y inscrivent : les acteurs culturels de chez vous tombent alors sur <strong>votre profil en priorité</strong>.
            </p>
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; line-height:1.6;">
                🇫🇷 <strong>Au niveau national</strong>, vous recevrez aussi <strong>gratuitement</strong> des appels d'offres venant de <strong>toute la France</strong> &mdash; un complément précieux à votre démarche commerciale régionale, qui vous ouvre des dates et des territoires que vous n'auriez pas prospectés seul.
            </p>
            <p style="margin:0 0 10px 0; font-size:14px; color:#333; line-height:1.6;">
                C'est cette dynamique collective qui nous permet de maintenir la plateforme <strong>100 % gratuite</strong> pour les compagnies.
            </p>
            <p style="margin:0; font-size:13px; color:#555; line-height:1.6; font-style:italic;">
                C'est en accompagnant les compagnies qui le souhaitent sur le volet administratif (URSSAF, DSN, contrats de cession…) que nous pérennisons ce modèle.
            </p>
        </div>
        <div class="highlight">
            <h3>💼 BESOIN D'AIDE POUR VOTRE ADMINISTRATION ?</h3>
            <p>Spectacle'ment VØtre ne se limite pas à la visibilité ! Depuis plus de 30 ans, nous accompagnons les compagnies de spectacle vivant dans la gestion complexe de leur administration artistique et sociale :</p>
            <ul>
                <li>Gestion URSSAF, DSN, DUE, AEM</li>
                <li>Fiches de salaire et contrats de cession</li>
                <li>Administration complète de votre compagnie</li>
            </ul>
            <p style="text-align: center;">
                <a href="https://spectacleanimation.fr/abonnement-compagnie" class="btn">Découvrez nos services</a>
            </p>
        </div>
        <p>À très bientôt !</p>
        <div class="footer">
            <p><strong>L'équipe Spectacle'ment VØtre</strong><br>
            contact@spectacleanimation.fr</p>
        </div>
    </div>
</body>
</html>
"""
                            msg_user = MailMessage(subject="Bienvenue sur Spectacle'ment VØtre !", recipients=[email])  # type: ignore[arg-type]
                            msg_user.html = body_html  # type: ignore[assignment]
                            current_app.mail.send(msg_user)  # type: ignore[attr-defined]
                            current_app.logger.info(f"[MAIL] ✓ Email de bienvenue envoyé à {email}")
                        except Exception as e:
                            current_app.logger.error(f"[MAIL] ✗ Envoi impossible (inscription utilisateur): {e}")
                            print("[MAIL] envoi impossible (inscription utilisateur):", e)
                else:
                    if not getattr(current_app, "mail", None):
                        current_app.logger.warning("[MAIL] ⚠ Flask-Mail non initialisé")
                    elif not current_app.config.get("MAIL_USERNAME"):
                        current_app.logger.warning("[MAIL] ⚠ MAIL_USERNAME non défini")
                    elif not current_app.config.get("MAIL_PASSWORD"):
                        current_app.logger.warning("[MAIL] ⚠ MAIL_PASSWORD non défini")

                flash("Compte créé ! Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"[INSCRIPTION] Erreur lors de la création du compte pour {username}: {e}")
                print(f"[INSCRIPTION] Erreur: {e}")
                flash("Erreur lors de la création du compte. Veuillez réessayer.", "danger")
                return render_template("register.html")

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

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["username"] = user.username
                flash("Bienvenue, vous êtes connecté !", "success")
                
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

            flash("Nom d'utilisateur ou mot de passe incorrect. Vérifiez vos identifiants.", "danger")

        return render_template("login.html", user=current_user())

    @app.route("/logout")
    def logout():
        if session.get("username"):
            session.pop("username", None)
            flash("Vous êtes déconnecté. À bientôt !", "success")
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
                        msg = MailMessage(
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
        # Incrémenter le compteur de visites (une seule fois par session)
        try:
            # Vérifier si l'utilisateur a déjà été compté dans cette session
            visit_counter = PageVisit.query.filter_by(page_name='home').first()
            if not session.get('home_visit_counted'):
                if not visit_counter:
                    visit_counter = PageVisit(page_name='home', visit_count=1)
                    db.session.add(visit_counter)
                else:
                    visit_counter.visit_count += 1
                    visit_counter.last_visit = datetime.utcnow()
                db.session.commit()
                # Marquer que cette session a été comptée
                session['home_visit_counted'] = True
            
            visit_count = visit_counter.visit_count if visit_counter else 0
        except Exception as e:
            print(f"Erreur lors de l'incrémentation du compteur: {e}")
            visit_count = 0
        
        # Récupérer les spectacles "à la une" pour les afficher
        try:
            spectacles_une = Show.query.filter(
                Show.approved == True,
                Show.is_featured == True
            ).order_by(Show.display_order.asc()).limit(8).all()
        except Exception as e:
            # Fallback si la colonne is_featured n'existe pas encore (avant migration)
            print(f"⚠️  Colonne is_featured non trouvée, affichage des spectacles approuvés: {e}")
            spectacles_une = Show.query.filter(
                Show.approved == True
            ).order_by(Show.display_order.asc()).limit(8).all()
        
        return render_template(
            "home.html",
            user=current_user(),
            spectacles_une=spectacles_une,
            visit_count=visit_count,
        )

    @app.route("/catalogue", endpoint="catalogue")
    def catalogue():
        """Page catalogue avec filtres structurés (spécialité, région, âge) + recherche par nom."""
        # -- Paramètres --
        q                   = request.args.get("q", "", type=str).strip()
        specialites         = [s.strip() for s in request.args.getlist("specialite") if s.strip()]
        specialite          = specialites[0] if specialites else ""  # pour le formulaire du haut
        evenements_selected = [e.strip() for e in request.args.getlist("evenement") if e.strip()]
        region              = request.args.get("region", "", type=str).strip()
        age                 = request.args.get("age", "", type=str).strip()
        # Public ciblé v2 (filtre indépendant du matching)
        public_cats_selected = [c.strip() for c in request.args.getlist("public_categories") if c.strip()]
        public_subs_selected = [s.strip() for s in request.args.getlist("public_sous_options") if s.strip()]
        page                = request.args.get("page", 1, type=int)

        # Résolution ville → région (ex: "Toulouse" → "Occitanie")
        region_resolved = region
        if region:
            city_match = next(
                (c for c in FRENCH_CITIES if c["name"].lower() == region.lower() or c["slug"] == region.lower()),
                None
            )
            if city_match:
                region_resolved = city_match["region"]

        shows = Show.query

        # Visibilité publique
        u = current_user()
        if not u or not u.is_admin:
            shows = shows.filter(Show.approved.is_(True))

        # -- Filtre texte : nom de compagnie ou titre seulement --
        if q:
            like = f"%{q}%"
            shows = shows.filter(or_(
                Show.title.ilike(like),
                Show.raison_sociale.ilike(like),
            ))

        # -- Filtre spécialité : champ structuré specialites + fallback category --
        if specialites:
            conds = []
            for s in specialites:
                # Cas spécial "Spectacle à la une" : on accepte aussi simplement "à la une" / "a la une"
                # (pour rester cohérent avec le diaporama de la home)
                if s.strip().lower() in ("spectacle à la une", "spectacle a la une"):
                    conds.append(Show.specialites.ilike("%à la une%"))
                    conds.append(Show.specialites.ilike("%a la une%"))
                    conds.append(Show.category.ilike("%à la une%"))
                    conds.append(Show.category.ilike("%a la une%"))
                    # + flag boolean is_featured (case cochée par admin/cie)
                    try:
                        conds.append(Show.is_featured.is_(True))
                    except Exception:
                        pass
                else:
                    like = f"%{s}%"
                    conds.append(Show.specialites.ilike(like))
                    conds.append(Show.category.ilike(like))
            shows = shows.filter(or_(*conds))

        # -- Filtre événement --
        if evenements_selected:
            conds = [Show.evenements.ilike(f"%{e}%") for e in evenements_selected]
            shows = shows.filter(or_(*conds))

        # -- Filtre région : champ structuré regions_intervention + fallback region/location --
        if region_resolved:
            like = f"%{region_resolved}%"
            shows = shows.filter(or_(
                Show.regions_intervention.ilike(like),
                Show.region.ilike(like),
                Show.location.ilike(like),
            ))

        # -- Filtre Public ciblé v2 (catégories + sous-options) --
        # Logique : si au moins une catégorie cochée, on garde les shows dont
        # public_categories contient au moins une cat commune. Si en plus des
        # sous-options sont cochées, on exige aussi au moins une sous-option commune.
        # Un show sans public_categories est exclu dès qu'un filtre est actif.
        # Matching CSV strict via délimiteurs (évite les faux positifs).
        def _csv_match_conds(col, codes):
            conds = []
            for c in codes:
                conds.append(col == c)
                conds.append(col.ilike(f"{c},%"))
                conds.append(col.ilike(f"%,{c}"))
                conds.append(col.ilike(f"%,{c},%"))
            return conds

        if public_cats_selected:
            shows = shows.filter(Show.public_categories.isnot(None))
            shows = shows.filter(Show.public_categories != "")
            shows = shows.filter(or_(*_csv_match_conds(Show.public_categories, public_cats_selected)))
            if public_subs_selected:
                shows = shows.filter(Show.public_sous_options.isnot(None))
                shows = shows.filter(or_(*_csv_match_conds(Show.public_sous_options, public_subs_selected)))

        # -- Filtre tranche d'âge / public (STRICT pour nouvelles valeurs, tolérant pour anciennes) --
        if age:
            from utils.matching import _GROUPE_NEUTRE, _GROUPE_ENFANT, _GROUPE_ADULTE, _AGE_PROCHES
            age_lower = age.lower()
            new_codes = {p[0] for p in PUBLICS}
            if age_lower in new_codes:
                # Filtre STRICT pour les nouvelles valeurs : correspondance exacte uniquement
                shows = shows.filter(Show.age_range == age_lower)
            else:
                # Filtre TOLÉRANT pour anciennes valeurs (compat) : exact + proches + neutres
                compatibles = {age_lower} | _AGE_PROCHES.get(age_lower, set()) | _GROUPE_NEUTRE
                if age_lower in _GROUPE_ADULTE:
                    shows = shows.filter(~Show.age_range.in_(list(_GROUPE_ENFANT)))
                elif age_lower in _GROUPE_ENFANT:
                    shows = shows.filter(~Show.age_range.in_(list(_GROUPE_ADULTE)))
                shows = shows.filter(or_(
                    Show.age_range.in_(list(compatibles)),
                    Show.age_range.is_(None),
                    Show.age_range == "",
                ))

        # -- Tri avant pagination (corrigé) --
        shows = shows.order_by(Show.display_order.asc(), Show.created_at.desc())

        # -- Pagination --
        try:
            pagination = shows.paginate(page=page, per_page=16, error_out=False)
            shows_list = pagination.items
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Erreur catalogue: %s", e)
            flash("Une erreur est survenue lors de la recherche.", "danger")
            pagination = None
            shows_list = []

        # -- Liste de toutes les spécialités pour les tags (avec comptage) --
        all_specialites = [s for group in SPECIALITES.values() for s in group]

        # -- H1 SEO dynamique --
        h1_title = "Spectacles et animations pour mairies, écoles et CSE partout en France"
        if specialite and region:
            h1_title = f"{specialite} à {region} - Artistes professionnels"
        elif specialite:
            h1_title = f"{specialite} - Artistes professionnels en France"
        elif region:
            h1_title = f"Spectacles et animations à {region} - Artistes professionnels"

        return render_template(
            "catalogue.html",
            shows=shows_list,
            pagination=pagination,
            q=q,
            specialite=specialite,
            specialites=specialites,
            evenements_selected=evenements_selected,
            specialites_data=SPECIALITES,
            evenements_data=EVENEMENTS,
            region=region,
            age=age,
            public_cats_selected=public_cats_selected,
            public_subs_selected=public_subs_selected,
            all_specialites=all_specialites,
            all_regions=REGIONS_FRANCE,
            age_options=[("", "Tous les publics")] + PUBLICS,
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
            # 🎄 Pages thématiques longue traîne Noël
            ('pere_noel_a_domicile', '0.85'),
            ('spectacles_noel_ecole', '0.85'),
            ('spectacles_noel_entreprise', '0.85'),
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
        
        # Pages SEO des villes françaises
        try:
            for city_slug in get_all_city_slugs():
                pages.append({
                    'loc': url_for('city_spectacles', city_slug=city_slug, _external=True),
                    'changefreq': 'weekly',
                    'priority': '0.8'
                })
        except Exception:
            pass  # Si la fonction n'est pas encore disponible, on ignore
        
        # Pages catalogue
        pages.append({
            'loc': url_for('catalogue', _external=True),
            'changefreq': 'daily',
            'priority': '0.9'
        })
        
        # Pages ville×catégorie (longue traîne SEO)
        try:
            seo_top_cats = [
                "magie", "marionnette", "clown", "theatre", "cirque",
                "spectacle-enfant", "arbre-de-noel", "animation-ecole",
                "pere-noel"
            ]
            for city_slug in get_all_city_slugs():
                for cat_slug in seo_top_cats:
                    pages.append({
                        'loc': url_for('seo_category_city', category_slug=cat_slug, city_slug=city_slug, _external=True),
                        'changefreq': 'weekly',
                        'priority': '0.6'
                    })
        except Exception:
            pass
        
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
        """Endpoint de santé basique pour le monitoring (ne vérifie pas la DB)"""
        from flask import jsonify
        
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        return jsonify(status), 200
    
    @app.route("/health/full")
    def health_check_full():
        """Endpoint de santé complet avec vérification de la base de données"""
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
            # Récupérer la raison sociale du formulaire (un utilisateur peut gérer plusieurs compagnies)
            u = current_user()
            raison_sociale = request.form.get("raison_sociale", "").strip()
            # Si vide, utiliser la raison sociale de l'utilisateur ou son username par défaut
            if not raison_sociale and u:
                raison_sociale = u.raison_sociale if u.raison_sociale else u.username
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            region = fix_mojibake(request.form.get("region", "").strip())
            location = request.form.get("location", "").strip()
            date_str = request.form.get("date", "").strip()
            age_range = request.form.get("age_range", "").strip()
            contact_email = request.form.get("contact_email", "").strip()
            contact_phone = request.form.get("contact_phone", "").strip()
            site_internet = request.form.get("site_internet", "").strip()
            is_event = request.form.get("is_event", "0") == "1"

            # Nouveaux champs matching (CSV)
            specialites_list = request.form.getlist("specialites")
            evenements_list = request.form.getlist("evenements")
            lieux_list = request.form.getlist("lieux_intervention")
            regions_list = request.form.getlist("regions_intervention")
            public_categories_list = request.form.getlist("public_categories")
            public_sous_options_list = request.form.getlist("public_sous_options")

            # Catégorie auto-dérivée de la 1ère spécialité
            category = specialites_list[0] if specialites_list else ""

            # Région auto-dérivée de la 1ère région d'intervention
            if regions_list:
                region = regions_list[0]

            # Validation : au moins 1 spécialité et 1 région + limites max
            if not specialites_list:
                flash("Veuillez cocher au moins une spécialité artistique.", "danger")
                return redirect(request.url)
            if len(specialites_list) > 4:
                flash("Maximum 4 spécialités autorisées.", "danger")
                return redirect(request.url)

            if not regions_list:
                flash("Veuillez cocher au moins une région d'intervention.", "danger")
                return redirect(request.url)

            date_val = None
            if date_str:
                try:
                    date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")

            file = request.files.get("file")
            file_name = None
            file_mimetype = None

            # Validation : minimum 2 photos obligatoires
            file2_prelim = request.files.get("file2")
            if not (file and file.filename) or not (file2_prelim and file2_prelim.filename):
                flash("Vous devez ajouter au minimum 2 photos pour publier votre spectacle.", "danger")
                return redirect(request.url)

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
                try:
                    file_name = upload_file_local(file)
                    file_mimetype = file.mimetype
                except Exception as e:
                    current_app.logger.error(f"Erreur upload fichier principal: {e}")
                    flash("Erreur lors de l'enregistrement du fichier. Veuillez réessayer.", "danger")
                    return redirect(request.url)

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
                try:
                    file_name2 = upload_file_local(file2)
                except Exception as e:
                    current_app.logger.error(f"Erreur upload photo 2: {e}")
                    flash("Erreur lors de l'enregistrement de la photo 2. Veuillez réessayer.", "danger")
                    return redirect(request.url)

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
                try:
                    file_name3 = upload_file_local(file3)
                except Exception as e:
                    current_app.logger.error(f"Erreur upload photo 3: {e}")
                    flash("Erreur lors de l'enregistrement de la photo 3. Veuillez réessayer.", "danger")
                    return redirect(request.url)

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
                specialites=",".join(specialites_list) if specialites_list else None,
                evenements=",".join(evenements_list) if evenements_list else None,
                lieux_intervention=",".join(lieux_list) if lieux_list else None,
                regions_intervention=",".join(regions_list) if regions_list else None,
                public_categories=",".join(public_categories_list) if public_categories_list else None,
                public_sous_options=",".join(public_sous_options_list) if public_sous_options_list else None,
            )
            db.session.add(show)
            db.session.commit()

            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
                try:
                    to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                    type_annonce = "📅 ÉVÉNEMENT" if is_event else "CATALOGUE"
                    body = (
                        f"Nouvelle annonce à valider [{type_annonce}]\n\n"
                        f"👤 Compagnie: {raison_sociale}\n"
                        f"📌 Titre: {title}\n"
                        f"📍 Lieu: {location}\n"
                        f"🎪 Catégorie: {category}\n"
                        f"🎭 Spécialités: {', '.join(specialites_list) if specialites_list else 'Aucune'}\n"
                        f"📋 Type: {type_annonce}\n"
                        + (f"📅 Date: {date_val}\n\n" if date_val else "")
                        + f"Date de création de la fiche : {show.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
                        + f"📧 Email: {contact_email}\n"
                        + f"📱 Téléphone: {contact_phone}\n"
                        + "\n\n✅ Rappel : Le déploiement sur Spectacle'ment Vôtre est entièrement gratuit.\n"
                        + "📢 Nous sélectionnons des artistes d'excellence pour offrir aux programmateurs des spectacles professionnels de qualité.\n\n"
                        + "💼 Service d'administration disponible pour les compagnies (gestion URSSAF, DSN, contrats, etc.).\n"
                        + "\nCordialement,\nL'équipe Spectacle'ment VØtre"
                    )
                    msg = MailMessage(subject="Nouvelle annonce à valider", recipients=[to_addr])  # type: ignore[arg-type]
                    msg.body = body  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                    current_app.logger.info(f"[MAIL] ✓ Email envoyé à l'admin pour nouvelle annonce: {title}")
                except Exception as e:  # pragma: no cover
                    current_app.logger.error(f"[MAIL] ✗ Envoi impossible (nouvelle annonce): {e}")
                    print("[MAIL] envoi impossible:", e)
            else:
                if not getattr(current_app, "mail", None):
                    current_app.logger.warning("[MAIL] ⚠ Flask-Mail non initialisé - Email non envoyé pour nouvelle annonce")
                elif not current_app.config.get("MAIL_USERNAME"):
                    current_app.logger.warning("[MAIL] ⚠ MAIL_USERNAME non défini - Email non envoyé")
                elif not current_app.config.get("MAIL_PASSWORD"):
                    current_app.logger.warning("[MAIL] ⚠ MAIL_PASSWORD non défini - Email non envoyé")

            flash("Annonce envoyée ! Elle sera visible après validation.", "success")
            # Afficher uniquement le message flash après création
            return render_template("flash_only_child.html", user=u)

        return render_template("submit_form.html", user=current_user(),
                               specialites_data=SPECIALITES, evenements_data=EVENEMENTS,
                               lieux_data=LIEUX, regions_data=REGIONS_FRANCE)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        from flask import abort
        
        # Tente d'abord de servir le fichier localement (pour compatibilité)
        local_path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
        if local_path.exists():
            response = send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)
            response.headers["Cache-Control"] = "public, max-age=31536000"
            return response
        
        # Sinon, rediriger vers une URL S3 presigned (pas de proxy = 0 mémoire)
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
            # Vérifier que le fichier existe
            s3_client.head_object(Bucket=s3_bucket, Key=filename)
            # Générer URL presigned (1h) — le navigateur télécharge directement depuis S3
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': s3_bucket, 'Key': filename},
                ExpiresIn=3600
            )
            return redirect(presigned_url)
            
        except botocore.exceptions.ClientError as e:
            current_app.logger.error(f"[S3] Fichier introuvable {filename}: {e}")
            abort(404)
        except Exception as e:
            current_app.logger.error(f"[S3] Erreur presigned URL {filename}: {e}")
            abort(404)

    @app.route("/thumbnails/<path:filename>")
    def thumbnail_file(filename):
        """Sert un thumbnail pré-généré (local ou S3). Ne génère PAS depuis l'original S3."""
        from flask import Response

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
            return redirect(url_for('uploaded_file', filename=filename))

        thumb_name = "thumb_" + filename.rsplit(".", 1)[0] + ".webp"
        thumb_dir = Path(current_app.config.get("THUMBNAIL_FOLDER",
                         Path(current_app.config["UPLOAD_FOLDER"]).parent / "thumbnails"))

        # 1) Servir depuis le cache local
        thumb_path = thumb_dir / thumb_name
        if thumb_path.exists():
            response = send_from_directory(str(thumb_dir), thumb_name, as_attachment=False)
            response.headers["Cache-Control"] = "public, max-age=31536000"
            return response

        # 2) Tenter de générer depuis un fichier local (pas de download S3)
        local_original = Path(current_app.config["UPLOAD_FOLDER"]) / filename
        if local_original.exists():
            result = generate_thumbnail(filename)
            if result and (thumb_dir / result).exists():
                response = send_from_directory(str(thumb_dir), result, as_attachment=False)
                response.headers["Cache-Control"] = "public, max-age=31536000"
                return response

        # 3) Rediriger vers le thumbnail sur S3 (presigned URL = 0 mémoire)
        s3_bucket = current_app.config.get("S3_BUCKET")
        s3_key = current_app.config.get("S3_KEY")
        s3_secret = current_app.config.get("S3_SECRET")
        s3_region = current_app.config.get("S3_REGION")
        if s3_bucket and s3_key and s3_secret and boto3:
            try:
                s3_client = boto3.client("s3", region_name=s3_region,
                    aws_access_key_id=s3_key, aws_secret_access_key=s3_secret)
                s3_client.head_object(Bucket=s3_bucket, Key=thumb_name)
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': s3_bucket, 'Key': thumb_name},
                    ExpiresIn=3600
                )
                return redirect(presigned_url)
            except Exception:
                pass

        # 4) Fallback : rediriger vers l'image originale (aussi en presigned)
        return redirect(url_for('uploaded_file', filename=filename))

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

        # ── Phase 5 : tracking des vues ──
        import hashlib
        sid = session.get("_id", "")
        ip_raw = request.remote_addr or ""
        ip_h = hashlib.sha256(ip_raw.encode()).hexdigest()[:16]
        already = ShowView.query.filter_by(show_id=show_id, session_id=sid).first() if sid else None
        if not already:
            db.session.add(ShowView(show_id=show_id, session_id=sid, ip_hash=ip_h))
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        view_count = ShowView.query.filter_by(show_id=show_id).count()

        # ── Phase 5 : avis approuvés ──
        reviews = Review.query.filter_by(show_id=show_id, approved=True).order_by(Review.created_at.desc()).all()
        avg_rating = 0
        if reviews:
            avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
        
        return render_template("show_detail.html", show=show, user=u, admin_email=admin_email,
                               spectacles_une=spectacles_une, view_count=view_count,
                               reviews=reviews, avg_rating=avg_rating, review_count=len(reviews))

    @app.route("/demande-devis/<int:show_id>", methods=["GET", "POST"])
    def demande_devis(show_id: int):
        show = Show.query.get_or_404(show_id)
        if request.method == "POST":
            nom = request.form.get("nom", "").strip()
            structure = request.form.get("structure", "").strip()
            email = request.form.get("email", "").strip()
            telephone = request.form.get("telephone", "").strip()
            date_manifestation = request.form.get("date_manifestation", "").strip()
            budget = request.form.get("budget", "").strip()
            type_lieu = request.form.get("type_lieu", "").strip()
            message = request.form.get("message", "").strip()

            if not all([nom, email, message]):
                flash("Veuillez remplir les champs obligatoires (nom, email, message).", "danger")
                return render_template("demande_devis.html", show=show, user=current_user())

            # Envoi email à la compagnie + admin en copie
            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                try:
                    admin_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                    compagnie_addr = show.contact_email  # Email de la compagnie (peut être None)

                    body_html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Demande de devis</title></head>
<body style="font-family:Arial,sans-serif; color:#333; max-width:600px; margin:0 auto;">
  <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32); padding:20px; text-align:center; border-radius:8px 8px 0 0;">
    <h2 style="color:#fff; margin:0;">🎭 Nouvelle demande de devis</h2>
    <p style="color:rgba(255,255,255,0.85); margin:8px 0 0 0;">Via Spectacle'ment VØtre</p>
  </div>
  <div style="background:#f9f9f9; padding:24px; border-radius:0 0 8px 8px; border:1px solid #e0e0e0;">

    <div style="background:#e8f5e9; padding:14px; border-radius:8px; margin-bottom:16px; border-left:4px solid #2e7d32;">
      <p style="margin:0; font-weight:700; color:#1b5e20; font-size:1.05rem;">🎭 {show.title}</p>
      <p style="margin:4px 0 0 0; color:#555; font-size:0.9rem;">{show.raison_sociale or ''} — {show.category or ''} — {show.region or ''}</p>
    </div>

    <h3 style="color:#1b5e20; border-bottom:2px solid #e0e0e0; padding-bottom:8px;">👤 Coordonnées du demandeur</h3>
    <table style="width:100%; border-collapse:collapse;">
      <tr><td style="padding:6px 0; color:#666; width:120px;">Nom</td><td style="padding:6px 0; font-weight:600;">{nom}</td></tr>
      <tr><td style="padding:6px 0; color:#666;">Structure</td><td style="padding:6px 0;">{structure or '—'}</td></tr>
      <tr><td style="padding:6px 0; color:#666;">Email</td><td style="padding:6px 0;"><a href="mailto:{email}" style="color:#1b5e20;">{email}</a></td></tr>
      <tr><td style="padding:6px 0; color:#666;">Téléphone</td><td style="padding:6px 0;">{telephone or '—'}</td></tr>
    </table>

    <h3 style="color:#1b5e20; border-bottom:2px solid #e0e0e0; padding-bottom:8px; margin-top:20px;">📅 Événement</h3>
    <table style="width:100%; border-collapse:collapse;">
      <tr><td style="padding:6px 0; color:#666; width:120px;">Date</td><td style="padding:6px 0;">{date_manifestation or '—'}</td></tr>
      <tr><td style="padding:6px 0; color:#666;">Type de lieu</td><td style="padding:6px 0;">{type_lieu or '—'}</td></tr>
      <tr><td style="padding:6px 0; color:#666;">Budget</td><td style="padding:6px 0; font-weight:700; color:#2e7d32;">{budget or '—'}</td></tr>
    </table>

    <h3 style="color:#1b5e20; border-bottom:2px solid #e0e0e0; padding-bottom:8px; margin-top:20px;">💬 Message</h3>
    <div style="background:#fff; padding:14px; border-radius:6px; border:1px solid #e0e0e0; white-space:pre-wrap;">{message}</div>

    <div style="margin-top:20px; text-align:center;">
      <a href="mailto:{email}?subject=Réponse à votre demande de devis — {show.title}"
         style="display:inline-block; padding:12px 28px; background:#1b5e20; color:#fff; text-decoration:none; border-radius:8px; font-weight:700;">
        ✉️ Répondre au demandeur
      </a>
    </div>

    <p style="margin-top:20px; font-size:0.8rem; color:#999; text-align:center;">
      Fiche spectacle : <a href="{url_for('show_detail', show_id=show.id, _external=True)}" style="color:#1b5e20;">{url_for('show_detail', show_id=show.id, _external=True)}</a>
    </p>
  </div>
</body>
</html>"""

                    # Destinataire : admin uniquement (l'admin contacte ensuite la compagnie)
                    recipients = [admin_addr]

                    msg = MailMessage(
                        subject=f"Demande de devis — {show.title} ({type_lieu or 'événement'})",
                        recipients=recipients
                    )
                    msg.html = body_html
                    current_app.mail.send(msg)
                    current_app.logger.info(f"[MAIL] ✓ Email devis envoyé pour show #{show.id} à {recipients}")

                    # Accusé de réception au demandeur
                    try:
                        accuse_html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif; color:#333; max-width:600px; margin:0 auto;">
  <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32); padding:20px; text-align:center; border-radius:8px 8px 0 0;">
    <h2 style="color:#fff; margin:0;">✅ Demande bien reçue !</h2>
  </div>
  <div style="background:#f9f9f9; padding:24px; border-radius:0 0 8px 8px; border:1px solid #e0e0e0;">
    <p>Bonjour <strong>{nom}</strong>,</p>
    <p>Votre demande de devis pour le spectacle <strong>« {show.title} »</strong> a bien été transmise à la compagnie.</p>
    <p>Elle vous contactera directement par email ou téléphone.</p>
    <p style="margin-top:20px; font-size:0.85rem; color:#666;">— L'équipe Spectacle'ment VØtre</p>
  </div>
</body></html>"""
                        accuse_msg = MailMessage(
                            subject=f"Votre demande de devis — {show.title}",
                            recipients=[email]
                        )
                        accuse_msg.html = accuse_html
                        current_app.mail.send(accuse_msg)
                    except Exception:
                        pass  # L'accusé de réception est facultatif

                except Exception as e:
                    current_app.logger.error(f"[MAIL] ✗ Envoi impossible (demande devis): {e}")

            flash("✅ Votre demande a bien été envoyée ! Nous vous répondrons rapidement.", "success")
            return redirect(url_for("show_detail", show_id=show.id))

        return render_template("demande_devis.html", show=show, user=current_user())

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
            s.region = fix_mojibake(request.form.get("region","").strip()) or None
            s.location = request.form.get("location","").strip()
            s.age_range = (request.form.get("age_range","") or None)
            s.site_internet = request.form.get("site_internet","").strip() or None
            s.contact_email = request.form.get("contact_email","").strip() or None
            s.contact_phone = request.form.get("contact_phone","").strip() or None

            # Matching : mise à jour des 4 axes
            spec_list = request.form.getlist("specialites")
            reg_list = request.form.getlist("regions_intervention")

            # Validation : au moins 1 spécialité et 1 région + limites max
            if not spec_list:
                flash("Veuillez cocher au moins une spécialité artistique.", "danger")
                return redirect(request.url)
            if len(spec_list) > 4:
                flash("Maximum 4 spécialités autorisées.", "danger")
                return redirect(request.url)
            if not reg_list:
                flash("Veuillez cocher au moins une région d'intervention.", "danger")
                return redirect(request.url)

            evt_list = request.form.getlist("evenements")
            lieux_list = request.form.getlist("lieux_intervention")

            s.specialites = ",".join(spec_list) if spec_list else None
            s.category = spec_list[0] if spec_list else (s.category or "")
            s.evenements = ",".join(evt_list) if evt_list else None
            s.lieux_intervention = ",".join(lieux_list) if lieux_list else None
            s.regions_intervention = ",".join(reg_list) if reg_list else None

            # Région auto-dérivée de la 1ère région d'intervention
            s.region = reg_list[0] if reg_list else (s.region or None)

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
                try:
                    new_name = upload_file_local(file)
                    s.file_name = new_name
                    s.file_mimetype = file.mimetype
                except Exception as e:
                    current_app.logger.error(f"Erreur upload fichier principal: {e}")
                    flash("Erreur lors de l'enregistrement du fichier. Veuillez réessayer.", "danger")
                    return redirect(request.url)

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
                try:
                    s.file_name2 = upload_file_local(file2)
                    s.file_mimetype2 = file2.mimetype
                except Exception as e:
                    current_app.logger.error(f"Erreur upload photo 2: {e}")
                    flash("Erreur lors de l'enregistrement de la photo 2. Veuillez réessayer.", "danger")
                    return redirect(request.url)

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
                try:
                    s.file_name3 = upload_file_local(file3)
                    s.file_mimetype3 = file3.mimetype
                except Exception as e:
                    current_app.logger.error(f"Erreur upload photo 3: {e}")
                    flash("Erreur lors de l'enregistrement de la photo 3. Veuillez réessayer.", "danger")
                    return redirect(request.url)

            db.session.commit()
            flash("Spectacle mis à jour.", "success")
            return render_template("flash_only_child.html", user=u)

        return render_template("show_form_edit.html", show=s, user=u,
                               specialites_data=SPECIALITES, evenements_data=EVENEMENTS,
                               lieux_data=LIEUX, regions_data=REGIONS_FRANCE)

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

        # Supprimer les enregistrements liés (FK sans CASCADE)
        from models.models import ShowView, Review, Conversation, Message
        ShowView.query.filter_by(show_id=s.id).delete()
        Review.query.filter_by(show_id=s.id).delete()
        for conv in Conversation.query.filter_by(show_id=s.id).all():
            Message.query.filter_by(conversation_id=conv.id).delete()
            db.session.delete(conv)

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
    
    @app.route("/admin/statistiques", endpoint="admin_statistics")
    @login_required
    @admin_required
    def admin_statistics():
        """
        Page de statistiques des visiteurs (conforme RGPD - données anonymisées)
        
        Optimisations appliquées :
        - Filtre is_bot == False sur toutes les requêtes (humains uniquement)
        - Regroupement des comptages en 1 requête au lieu de 6 (performance)
        - Suppression de la vue horaire instable (DATE_TRUNC PostgreSQL)
        - 100 derniers visiteurs humains au lieu de 200
        - Affichage des VISITEURS UNIQUES par jour (COUNT DISTINCT session_id)
        """
        from sqlalchemy import func, desc, text
        from sqlalchemy.exc import ProgrammingError
        from datetime import timedelta
        
        # Période sélectionnée (par défaut: 7 derniers jours)
        period = request.args.get("period", "7", type=str)
        
        # Calculer la date limite selon la période
        if period == "today":
            # Depuis minuit aujourd'hui (00:00:00)
            date_limit = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            days = 1
            period_label = "Aujourd'hui"
        else:
            days = int(period)
            date_limit = datetime.utcnow() - timedelta(days=days)
            period_label = f"{days} dernier{'s' if days > 1 else ''} jour{'s' if days > 1 else ''}"
        
        # Comptages optimisés (1 requête au lieu de 3)
        visit_stats = db.session.query(
            VisitorLog.is_bot,
            func.count(VisitorLog.id).label('visit_count'),
            func.count(func.distinct(VisitorLog.session_id)).label('unique_count')
        ).filter(VisitorLog.visited_at >= date_limit).\
            group_by(VisitorLog.is_bot).all()
        
        # Initialisation des compteurs
        total_visits = 0
        total_bots = 0
        total_humans = 0
        unique_bots = 0
        unique_humans = 0
        
        # Extraction des résultats
        for stat in visit_stats:
            total_visits += stat.visit_count
            if stat.is_bot:
                total_bots = stat.visit_count
                unique_bots = stat.unique_count
            else:
                total_humans = stat.visit_count
                unique_humans = stat.unique_count
        
        # Total visiteurs uniques
        unique_visitors = unique_humans + unique_bots
        
        # Pages les plus visitées - HUMAINS UNIQUEMENT
        top_pages = db.session.query(
            VisitorLog.page_url,
            func.count(VisitorLog.id).label('visits')
        ).filter(
            VisitorLog.visited_at >= date_limit,
            VisitorLog.is_bot == False
        ).group_by(VisitorLog.page_url).\
            order_by(desc('visits')).\
            limit(10).all()
        
        # Référents (d'où viennent les visiteurs) - HUMAINS UNIQUEMENT
        top_referrers = db.session.query(
            VisitorLog.referrer,
            func.count(VisitorLog.id).label('visits')
        ).filter(
            VisitorLog.visited_at >= date_limit,
            VisitorLog.referrer.isnot(None),
            VisitorLog.is_bot == False
        ).group_by(VisitorLog.referrer).\
            order_by(desc('visits')).\
            limit(10).all()
        
        # Visiteurs uniques par jour - HUMAINS UNIQUEMENT pour le graphique
        visits_by_day = db.session.query(
            func.date(VisitorLog.visited_at).label('date'),
            func.count(func.distinct(VisitorLog.session_id)).label('visits')
        ).filter(
            VisitorLog.visited_at >= date_limit,
            VisitorLog.is_bot == False
        ).group_by(func.date(VisitorLog.visited_at)).\
            order_by('date').all()
        
        # Derniers visiteurs uniques (groupés par session) - HUMAINS UNIQUEMENT
        # Sous-requête optimisée : GROUP BY uniquement sur session_id (plus performant)
        # Limite à 100 pour un rendu plus rapide
        subq = db.session.query(
            VisitorLog.session_id,
            func.min(VisitorLog.id).label('min_id'),
            func.min(VisitorLog.visited_at).label('first_visit'),
            func.max(VisitorLog.visited_at).label('last_visit'),
            func.count(VisitorLog.id).label('page_count')
        ).filter(
            VisitorLog.visited_at >= date_limit,
            VisitorLog.is_bot == False
        ).group_by(VisitorLog.session_id).\
            order_by(desc(func.min(VisitorLog.visited_at))).\
            limit(100).subquery()
        
        # Récupération des détails en joignant sur l'ID minimal de chaque session
        recent_visitors = db.session.query(
            subq.c.session_id,
            subq.c.first_visit,
            subq.c.last_visit,
            subq.c.page_count,
            VisitorLog.city,
            VisitorLog.region,
            VisitorLog.country,
            VisitorLog.isp,
            VisitorLog.ip_anonymized,
            VisitorLog.user_agent,
            VisitorLog.user_id,
            VisitorLog.is_bot
        ).join(VisitorLog, VisitorLog.id == subq.c.min_id).all()
        
        # Maximum de visiteurs uniques sur un jour (pour la barre de progression)
        max_visitors_per_day = max([day.visits for day in visits_by_day]) if visits_by_day else 1
        
        # Utilisateurs connectés actifs - HUMAINS UNIQUEMENT
        active_users = db.session.query(
            User.username,
            func.count(VisitorLog.id).label('visits')
        ).join(VisitorLog, VisitorLog.user_id == User.id).\
            filter(
                VisitorLog.visited_at >= date_limit,
                VisitorLog.is_bot == False
            ).\
            group_by(User.username).\
            order_by(desc('visits')).\
            limit(10).all()
        
        return render_template(
            "admin_statistics.html",
            user=current_user(),
            total_visits=total_visits,
            total_bots=total_bots,
            total_humans=total_humans,
            unique_visitors=unique_visitors,
            unique_humans=unique_humans,
            unique_bots=unique_bots,
            top_pages=top_pages,
            top_referrers=top_referrers,
            visits_by_day=visits_by_day,
            max_visitors_per_day=max_visitors_per_day,
            recent_visitors=recent_visitors,
            active_users=active_users,
            days=days,
            period=period,
            period_label=period_label
        )
    
    # Route temporaire pour migration is_bot (À SUPPRIMER après exécution)
    @app.route("/admin/migrate-is-bot")
    @login_required
    @admin_required
    def migrate_is_bot():
        """Migration temporaire : Ajoute la colonne is_bot à visitor_log"""
        from sqlalchemy import text
        
        try:
            # Vérifier si la colonne existe déjà
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='visitor_log' 
                AND column_name='is_bot'
            """)
            
            result = db.session.execute(check_query).fetchone()
            
            if result:
                return "<h1>✓ Migration déjà effectuée</h1><p>La colonne 'is_bot' existe déjà dans visitor_log</p><a href='/admin'>Retour admin</a>"
            
            # Ajouter la colonne is_bot
            db.session.execute(text("""
                ALTER TABLE visitor_log 
                ADD COLUMN is_bot BOOLEAN DEFAULT FALSE NOT NULL
            """))
            
            # Créer un index
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_visitor_log_is_bot 
                ON visitor_log(is_bot)
            """))
            
            # Marquer les bots existants (User-Agent)
            db.session.execute(text("""
                UPDATE visitor_log 
                SET is_bot = TRUE 
                WHERE LOWER(user_agent) LIKE '%bot%'
                   OR LOWER(user_agent) LIKE '%crawler%'
                   OR LOWER(user_agent) LIKE '%spider%'
                   OR LOWER(user_agent) LIKE '%scraper%'
                   OR LOWER(user_agent) LIKE '%wget%'
                   OR LOWER(user_agent) LIKE '%curl%'
                   OR LOWER(user_agent) LIKE '%python%'
                   OR LOWER(user_agent) LIKE '%go-http%'
            """))
            
            # Marquer les bots existants (ISP datacenter)
            db.session.execute(text("""
                UPDATE visitor_log 
                SET is_bot = TRUE 
                WHERE (
                    LOWER(isp) LIKE '%amazon%'
                    OR LOWER(isp) LIKE '%aws%'
                    OR LOWER(isp) LIKE '%google cloud%'
                    OR LOWER(isp) LIKE '%microsoft corporation%'
                    OR LOWER(isp) LIKE '%tencent%'
                    OR LOWER(isp) LIKE '%alibaba%'
                )
                AND (
                    user_agent NOT LIKE '%Chrome%'
                    AND user_agent NOT LIKE '%Firefox%'
                    AND user_agent NOT LIKE '%Safari%'
                    AND user_agent NOT LIKE '%Edge%'
                )
            """))
            
            db.session.commit()
            
            # Statistiques
            total = db.session.execute(text("SELECT COUNT(*) FROM visitor_log")).scalar()
            bots = db.session.execute(text("SELECT COUNT(*) FROM visitor_log WHERE is_bot = TRUE")).scalar()
            humans = total - bots
            
            return f"""
            <h1>✅ Migration réussie !</h1>
            <h2>📊 Statistiques :</h2>
            <ul>
                <li>Total visiteurs: {total}</li>
                <li>Robots détectés: {bots} ({bots*100//total if total > 0 else 0}%)</li>
                <li>Humains: {humans} ({humans*100//total if total > 0 else 0}%)</li>
            </ul>
            <p><strong>✓ Vous pouvez maintenant accéder aux statistiques avec filtres robots/humains</strong></p>
            <a href="/admin/statistiques">Voir les statistiques</a> | <a href="/admin">Retour admin</a>
            """
            
        except Exception as e:
            db.session.rollback()
            return f"<h1>❌ Erreur lors de la migration</h1><pre>{str(e)}</pre><a href='/admin'>Retour admin</a>"
    
    # Route de DEBUG pour voir tous les headers HTTP (TEMPORAIRE)
    @app.route("/admin/debug-headers")
    @admin_required
    def debug_headers():
        """Page de debug pour diagnostiquer la détection d'IP"""
        # Récupérer tous les headers
        all_headers = dict(request.headers)
        
        # Tester la détection d'IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        real_ip = request.headers.get('X-Real-IP')
        cf_ip = request.headers.get('CF-Connecting-IP')
        
        # Déterminer l'IP utilisée par le code
        detected_ip = None
        detection_method = None
        
        if forwarded_for:
            detected_ip = forwarded_for.split(',')[0].strip()
            detection_method = "X-Forwarded-For"
        elif real_ip:
            detected_ip = real_ip.strip()
            detection_method = "X-Real-IP"
        elif cf_ip:
            detected_ip = cf_ip.strip()
            detection_method = "CF-Connecting-IP"
        else:
            detected_ip = request.remote_addr
            detection_method = "request.remote_addr (fallback)"
        
        # Anonymiser comme le code réel
        ip_parts = detected_ip.split('.')
        if len(ip_parts) == 4:
            ip_anonymized = f"{ip_parts[0]}.{ip_parts[1]}.0.0"
        else:
            ip_anonymized = "0.0.0.0"
        
        # Vérifier si IP publique
        is_public = not (detected_ip.startswith('10.') or 
                        detected_ip.startswith('192.168.') or 
                        detected_ip.startswith('172.'))
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Debug Headers IP</title>
            <style>
                body {{ font-family: monospace; padding: 20px; background: #1a1a2e; color: #fff; }}
                h1 {{ color: #6d1313; }}
                h2 {{ color: #ffc107; margin-top: 30px; }}
                .box {{ background: #16213e; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #6d1313; }}
                .success {{ color: #00ff00; }}
                .error {{ color: #ff0000; }}
                .warning {{ color: #ffc107; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #333; }}
                th {{ color: #6d1313; }}
                .highlight {{ background: #2d3561; padding: 10px; border-radius: 4px; }}
                a {{ color: #6d1313; text-decoration: none; font-weight: bold; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>🔍 Diagnostic Détection IP Visiteurs</h1>
            
            <div class="box">
                <h2>📊 Résultat de la Détection</h2>
                <p class="highlight"><strong>Méthode utilisée :</strong> {detection_method}</p>
                <p class="highlight"><strong>IP détectée (brute) :</strong> {detected_ip}</p>
                <p class="highlight"><strong>IP anonymisée (stockée) :</strong> {ip_anonymized}</p>
                <p class="{'success' if is_public else 'error'}">
                    {'✅ IP PUBLIQUE détectée - CORRECT !' if is_public else '❌ IP PRIVÉE - PROBLÈME : header X-Forwarded-For manquant ou invalide'}
                </p>
            </div>
            
            <div class="box">
                <h2>🌐 Headers IP Spécifiques</h2>
                <table>
                    <tr>
                        <th>Header</th>
                        <th>Valeur</th>
                        <th>Status</th>
                    </tr>
                    <tr>
                        <td>X-Forwarded-For</td>
                        <td>{forwarded_for or '<span class="error">NON PRÉSENT</span>'}</td>
                        <td>{'✅ Utilisé' if detection_method == 'X-Forwarded-For' else '⚪'}</td>
                    </tr>
                    <tr>
                        <td>X-Real-IP</td>
                        <td>{real_ip or '<span class="error">NON PRÉSENT</span>'}</td>
                        <td>{'✅ Utilisé' if detection_method == 'X-Real-IP' else '⚪'}</td>
                    </tr>
                    <tr>
                        <td>CF-Connecting-IP</td>
                        <td>{cf_ip or '<span class="error">NON PRÉSENT</span>'}</td>
                        <td>{'✅ Utilisé' if detection_method == 'CF-Connecting-IP' else '⚪'}</td>
                    </tr>
                    <tr>
                        <td>request.remote_addr</td>
                        <td>{request.remote_addr}</td>
                        <td>{'✅ Utilisé (fallback)' if detection_method.startswith('request.remote_addr') else '⚪'}</td>
                    </tr>
                </table>
            </div>
            
            <div class="box">
                <h2>📋 Tous les Headers HTTP Reçus</h2>
                <table>
                    <tr><th>Nom</th><th>Valeur</th></tr>
                    {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in sorted(all_headers.items()))}
                </table>
            </div>
            
            <div class="box">
                <h2>💡 Analyse et Recommandations</h2>
                {'<p class="success">✅ Le système fonctionne correctement. Les vraies IPs publiques sont détectées.</p>' if is_public else 
                 '<p class="error">❌ PROBLÈME : Render ne transmet pas les IPs publiques dans les headers.</p>' +
                 '<p class="warning">⚠️  Solutions possibles :</p>' +
                 '<ul>' +
                 '<li>1. Vérifier configuration Render (proxy headers)</li>' +
                 '<li>2. Contacter support Render</li>' +
                 '<li>3. Utiliser un CDN (Cloudflare) en amont</li>' +
                 '<li>4. Accepter que seules les IPs de Render soient visibles (limitation plateforme)</li>' +
                 '</ul>'}
            </div>
            
            <p style="margin-top: 40px;">
                <a href="/admin/statistiques">← Retour aux statistiques</a>
            </p>
        </body>
        </html>
        """
        
        return html
    
    @app.route("/change-password", methods=["GET", "POST"])
    @login_required
    def change_password():
        """Permet à tout utilisateur connecté de changer son mot de passe"""
        user = current_user()
        
        if request.method == "POST":
            old_password = request.form.get("old_password", "").strip()
            new_password = request.form.get("new_password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()
            
            # Vérifications
            if not old_password or not new_password or not confirm_password:
                flash("Tous les champs sont obligatoires.", "danger")
                return render_template("change_password.html", user=user)
            
            # Vérifier l'ancien mot de passe
            if not user.check_password(old_password):
                flash("L'ancien mot de passe est incorrect.", "danger")
                return render_template("change_password.html", user=user)
            
            # Vérifier que les nouveaux mots de passe correspondent
            if new_password != confirm_password:
                flash("Les nouveaux mots de passe ne correspondent pas.", "danger")
                return render_template("change_password.html", user=user)
            
            # Vérifier la longueur minimale
            if len(new_password) < 6:
                flash("Le nouveau mot de passe doit contenir au moins 6 caractères.", "danger")
                return render_template("change_password.html", user=user)
            
            # Changer le mot de passe
            user.set_password(new_password)
            db.session.commit()
            
            flash("Mot de passe modifié avec succès !", "success")
            
            # Rediriger selon le type d'utilisateur
            if user.is_admin:
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("company_dashboard"))
        
        return render_template("change_password.html", user=user)

    @app.route("/admin/shows/new", methods=["GET"])
    @login_required
    @admin_required
    def show_new():
        u = current_user()
        show = Show(
            raison_sociale=u.raison_sociale if u and u.raison_sociale else (u.username if u else None),
            title="",
            description="",
            category="",
            approved=False,
        )
        db.session.add(show)
        db.session.commit()
        flash("Nouvelle fiche créée — complétez les informations ci-dessous.", "info")
        return redirect(url_for("show_edit", show_id=show.id))

    @app.route("/admin/shows/<int:show_id>/edit", methods=["GET", "POST"])
    @login_required
    @admin_required
    def show_edit(show_id: int):
        show = Show.query.get_or_404(show_id)
        if request.method == "POST":
            show.raison_sociale = request.form.get("raison_sociale", "").strip() or None
            show.title = request.form.get("title", "").strip()
            show.description = request.form.get("description", "").strip()
            show.region = fix_mojibake(request.form.get("region", "").strip()) or None
            show.location = request.form.get("location", "").strip()
            show.category = request.form.get("category", "").strip()  # admin peut forcer la catégorie
            show.age_range = request.form.get("age_range", "").strip() or None
            show.contact_email = request.form.get("contact_email", "").strip() or None
            show.contact_phone = request.form.get("contact_phone", "").strip() or None
            date_str = request.form.get("date", "").strip()
            show.site_internet = request.form.get("site_internet", "").strip() or None
            # Gérer le champ is_event (admin seulement)
            show.is_event = request.form.get("is_event", "0") == "1"
            # Gérer le champ is_featured (admin seulement) - Affichage "à la une"
            show.is_featured = request.form.get("is_featured", "0") == "1"
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
                try:
                    new_name = upload_file_local(file)
                    show.file_name = new_name
                    show.file_mimetype = file.mimetype
                except Exception as e:
                    current_app.logger.error(f"Erreur upload fichier principal: {e}")
                    flash("Erreur lors de l'enregistrement du fichier. Veuillez réessayer.", "danger")
                    return redirect(request.url)

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
                try:
                    show.file_name2 = upload_file_local(file2)
                    show.file_mimetype2 = file2.mimetype
                except Exception as e:
                    current_app.logger.error(f"Erreur upload photo 2: {e}")
                    flash("Erreur lors de l'enregistrement de la photo 2. Veuillez réessayer.", "danger")
                    return redirect(request.url)

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
                try:
                    show.file_name3 = upload_file_local(file3)
                    show.file_mimetype3 = file3.mimetype
                except Exception as e:
                    current_app.logger.error(f"Erreur upload photo 3: {e}")
                    flash("Erreur lors de l'enregistrement de la photo 3. Veuillez réessayer.", "danger")
                    return redirect(request.url)

            # Matching fields
            show.specialites = ",".join(request.form.getlist("specialites"))
            show.evenements = ",".join(request.form.getlist("evenements"))
            show.lieux_intervention = ",".join(request.form.getlist("lieux_intervention"))
            show.regions_intervention = ",".join(request.form.getlist("regions_intervention"))
            _pc_cats = request.form.getlist("public_categories")
            _pc_subs = request.form.getlist("public_sous_options")
            # Appliquer single_select : pour chaque catégorie marquée single_select,
            # ne garder qu'une seule sous-option (la première reçue)
            for _cat_def in PUBLIC_CIBLE_CATEGORIES:
                if _cat_def.get("single_select"):
                    _allowed = [c[0] for c in _cat_def["sous_options"]]
                    _kept = [s for s in _pc_subs if s in _allowed]
                    if len(_kept) > 1:
                        _pc_subs = [s for s in _pc_subs if s not in _allowed] + [_kept[0]]
            # Vérifier les dépendances 'requires' (ex: enfants impose famille)
            # Sauf si une sous-option exclusive (ex: creche) est cochée → dispense
            _exclusive_checked = False
            for _cat_def in PUBLIC_CIBLE_CATEGORIES:
                for _ex in _cat_def.get("exclusive_subs", []) or []:
                    if _ex in _pc_subs:
                        _exclusive_checked = True
                        break
                if _exclusive_checked:
                    break
            _missing_req = []
            if not _exclusive_checked:
                for _cat_def in PUBLIC_CIBLE_CATEGORIES:
                    if _cat_def["code"] in _pc_cats:
                        for _req in _cat_def.get("requires", []) or []:
                            if _req not in _pc_cats:
                                _missing_req.append((_cat_def["code"], _req))
                                continue
                            _req_subs = [c[0] for c in next((c["sous_options"] for c in PUBLIC_CIBLE_CATEGORIES if c["code"] == _req), [])]
                            if not any(s in _req_subs for s in _pc_subs):
                                _missing_req.append((_cat_def["code"], _req))
            if _missing_req:
                msg = " ; ".join(f"« {a} » requiert une option dans « {b} »" for a, b in _missing_req)
                flash(f"Public ciblé incomplet : {msg}", "danger")
                return redirect(request.url)
            show.public_categories = ",".join(_pc_cats) or None
            show.public_sous_options = ",".join(_pc_subs) or None

            db.session.commit()
            flash("Annonce mise à jour.", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("show_form_edit.html", show=show, user=current_user(),
                               specialites_data=SPECIALITES, evenements_data=EVENEMENTS,
                               lieux_data=LIEUX, regions_data=REGIONS_FRANCE,
                               all_users=User.query.filter_by(is_admin=False).order_by(User.username).all())

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

        # Supprimer les enregistrements liés (FK sans CASCADE)
        from models.models import ShowView, Review, Conversation, Message
        ShowView.query.filter_by(show_id=show.id).delete()
        Review.query.filter_by(show_id=show.id).delete()
        for conv in Conversation.query.filter_by(show_id=show.id).all():
            Message.query.filter_by(conversation_id=conv.id).delete()
            db.session.delete(conv)

        db.session.delete(show)
        db.session.commit()
        flash("Annonce supprimée.", "success")
        return redirect(request.referrer or url_for("admin_dashboard"))

    @app.route("/admin/shows/<int:show_id>/approve", methods=["POST"])
    @login_required
    @admin_required
    def show_approve(show_id: int):
        show = Show.query.get_or_404(show_id)
        
        # Vérifier qu'il y a au moins 2 photos avant d'approuver
        photos_count = sum([
            1 if show.file_name else 0,
            1 if show.file_name2 else 0,
            1 if show.file_name3 else 0
        ])
        
        if photos_count < 2:
            flash(f"⚠️ Ce spectacle ne peut pas être approuvé : il doit avoir au moins 2 photos (actuellement : {photos_count} photo{'s' if photos_count > 1 else ''}).", "warning")
            return redirect(url_for("admin_dashboard"))
        
        show.approved = True
        # Annule automatiquement un éventuel préavis de suppression sur le compte propriétaire
        try:
            if show.user_id:
                owner = User.query.get(show.user_id)
                if owner and getattr(owner, 'pending_deletion_at', None):
                    owner.pending_deletion_at = None
                    current_app.logger.info(f"[ADMIN] Préavis suppression annulé auto pour {owner.username} (spectacle approuvé)")
        except Exception as e:
            current_app.logger.warning(f"[ADMIN] Annulation préavis impossible: {e}")
        db.session.commit()
        
        # Envoi automatique d'un email avec le lien du spectacle à la compagnie après validation
        if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
            try:
                # On privilégie l'email de la compagnie si présent, sinon fallback admin
                to_addr = show.contact_email if show.contact_email else (current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME"))
                show_url = url_for("show_detail", show_id=show.id, _external=True)
                
                # Déterminer si c'est une carte créée par l'admin (pas de user_id) ou par l'utilisateur
                if show.user_id:
                    # Carte créée par l'utilisateur lui-même → Email de validation classique
                    subject = "Votre spectacle est validé sur Spectacle'ment VØtre !"
                    abonnement_url = url_for('abonnement_compagnie', _external=True)
                    submit_url = url_for('submit_show', _external=True)
                    body_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spectacle validé</title>
</head>
<body style="margin:0; padding:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); overflow: hidden;">
                    <!-- Logo Header -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px 40px;">
                            <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment VØtre" style="max-width: 280px; height: auto;">
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h1 style="color: #667eea; font-size: 28px; margin: 0 0 20px 0; text-align: center;">
                                ✅ Félicitations !
                            </h1>
                            <p style="font-size: 16px; color: #333; line-height: 1.6; margin: 0 0 20px 0;">
                                Votre spectacle vient d'être <strong>validé et publié</strong> sur Spectacle'ment VØtre.
                            </p>
                            
                            <!-- Spectacle Info Card -->
                            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 12px; padding: 25px; margin: 25px 0;">
                                <h2 style="color: #764ba2; font-size: 20px; margin: 0 0 15px 0;">{show.title}</h2>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 14px; color: #555;">
                                    <div><strong>Compagnie :</strong><br>{show.raison_sociale or 'Non renseignée'}</div>
                                    <div><strong>Lieu :</strong><br>{show.location}</div>
                                    <div><strong>Catégorie :</strong><br>{show.category}</div>
                                    <div><strong>Publié le :</strong><br>{show.created_at.strftime('%d/%m/%Y %H:%M') if show.created_at else 'N/A'}</div>
                                </div>
                            </div>
                            
                            <!-- View Button -->
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{show_url}" style="display: inline-block; background-color: #667eea; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff !important; text-decoration: none; padding: 14px 40px; border-radius: 30px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                                    <span style="color:#ffffff;">👁️ Voir mon annonce</span>
                                </a>
                            </div>
                            
                            <!-- Info Section -->
                            <div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin: 25px 0; border-radius: 8px;">
                                <p style="margin: 0 0 12px 0; font-size: 15px; color: #333; line-height: 1.6;">
                                    <strong>📢 Spectacle'ment VØtre</strong> est un annuaire gratuit qui sélectionne des artistes d'excellence pour offrir aux programmateurs (écoles, mairies, CSE, centres culturels) des spectacles professionnels de qualité.
                                </p>
                                <p style="margin: 0; font-size: 15px; color: #28a745; font-weight: bold;">
                                    ✅ Votre déploiement sur la plateforme est <u>entièrement gratuit</u>.
                                </p>
                            </div>
                            
                            <!-- Admin Services -->
                            <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); border-radius: 12px; padding: 25px; margin: 25px 0;">
                                <h3 style="color: #d63031; font-size: 18px; margin: 0 0 12px 0;">💼 Besoin d'aide administrative ?</h3>
                                <p style="font-size: 14px; color: #333; line-height: 1.6; margin: 0 0 15px 0;">
                                    Spectacle'ment VØtre propose également un service d'administration pour les compagnies (gestion URSSAF, DSN, DUE, fiches de salaire, contrats).
                                </p>
                                <a href="{abonnement_url}" style="display: inline-block; background: #d63031; color: white; text-decoration: none; padding: 12px 28px; border-radius: 25px; font-weight: bold; font-size: 14px;">
                                    Découvrir l'offre premium
                                </a>
                            </div>
                            
                            <!-- Event Publishing Reminder -->
                            <div style="background: #e3f2fd; border-radius: 8px; padding: 20px; margin: 25px 0; border: 2px solid #2196F3;">
                                <p style="margin: 0; font-size: 15px; color: #1976D2; line-height: 1.6; text-align: center;">
                                    📅 <strong>Astuce :</strong> <a href="{submit_url}" style="color: #1565C0; font-weight: bold; text-decoration: none;">Annoncez vos événements GRATUITEMENT</a> toute l'année sur notre plateforme !
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #f8f9fa; padding: 30px 40px; text-align: center; border-top: 3px solid #667eea;">
                            <p style="font-size: 13px; color: #666; margin: 0 0 8px 0; line-height: 1.5;">
                                Si vous souhaitez retirer ou modifier votre fiche, contactez-nous par simple retour de mail.
                            </p>
                            <p style="font-size: 14px; color: #333; margin: 0; font-weight: bold;">
                                Spectaclement vôtre,<br>
                                L'équipe Spectacle'ment VØtre
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
                else:
                    # Carte créée par l'admin → Email de découverte (HTML)
                    subject = "Votre spectacle a été repéré pour notre annuaire Spectacle'ment VØtre !"
                    abonnement_url = url_for('abonnement_compagnie', _external=True)
                    date_publication = show.created_at.strftime('%d/%m/%Y %H:%M') if show.created_at else 'N/A'
                    body_html_decouverte = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background:#f4f4f7; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7; padding:30px 0;">
    <tr>
        <td align="center">
            <table role="presentation" width="620" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:12px; box-shadow:0 4px 24px rgba(0,0,0,0.08); overflow:hidden; max-width:620px;">
                <tr>
                    <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); padding:40px 40px 30px; text-align:center;">
                        <img src="https://spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment VØtre" width="120" style="display:block; margin:0 auto 16px; max-width:120px; height:auto;">
                        <h1 style="margin:0 0 8px 0; font-size:26px; color:#fff; font-weight:700; letter-spacing:0.5px;">Spectacle'ment V&Oslash;tre</h1>
                        <p style="margin:0; font-size:14px; color:rgba(255,255,255,0.8); letter-spacing:2px; text-transform:uppercase;">Annuaire du spectacle vivant</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding:35px 40px 20px;">
                        <p style="margin:0 0 18px 0; font-size:16px; color:#333; line-height:1.7;">Bonjour,</p>
                        <p style="margin:0 0 18px 0; font-size:16px; color:#333; line-height:1.7;"><strong>F&eacute;licitations !</strong> Votre talent a retenu notre attention et nous avons cr&eacute;&eacute; une fiche pour vous sur notre annuaire gratuit.</p>
                        <p style="margin:0 0 18px 0; font-size:15px; color:#444; line-height:1.7;">Vous profitez d&eacute;sormais des <strong>appels d'offres</strong> du site Spectacle'ment V&Oslash;tre gratuitement. En vous inscrivant, vous pourrez aller plus loin : annoncer vos &eacute;v&eacute;nements, d&eacute;ployer vos spectacles sur notre plateforme et recevoir directement les appels d'offres de nos partenaires, le tout <strong>gratuitement</strong>.</p>
                        <div style="background:#e8f5e9; border:1px solid #a5d6a7; border-radius:8px; padding:16px 20px; margin-bottom:18px; text-align:center;">
                            <p style="margin:0 0 8px 0; font-size:15px; color:#2e7d32; font-weight:600;">Votre d&eacute;ploiement sur notre plateforme est enti&egrave;rement gratuit.</p>
                            <p style="margin:0 0 8px 0; font-size:13px; color:#388e3c; line-height:1.5;">Pourquoi ? Notre vocation depuis plus de 30 ans est de connecter artistes et programmateurs. Votre visibilit&eacute; enrichit notre annuaire et profite &agrave; l'ensemble du r&eacute;seau culturel. C'est en accompagnant les compagnies qui le souhaitent sur le volet administratif que nous p&eacute;rennisons ce mod&egrave;le gratuit.</p>
                            <p style="margin:0; font-size:13px; color:#388e3c; line-height:1.5;">Chaque compagnie inscrite apporte sa pierre &agrave; l'&eacute;difice : plus l'annuaire est riche, plus les programmateurs y trouvent leur bonheur, et plus les opportunit&eacute;s reviennent vers vous.</p>
                        </div>
                        <p style="margin:0; font-size:15px; color:#444; line-height:1.7;"><strong>Notre mission :</strong> Rep&eacute;rer les meilleurs artistes et compagnies pour offrir de l'excellence aux programmateurs qui recherchent des spectacles professionnels.</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding:0 40px;">
                        <div style="background:linear-gradient(135deg,#f5f7fa 0%,#e8ecf1 100%); border-radius:10px; padding:24px; border-left:5px solid #764ba2;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Compagnie</span><br><span style="font-size:16px; color:#1a1a2e; font-weight:600;">{show.raison_sociale or 'Non renseign&eacute;e'}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Titre du spectacle</span><br><span style="font-size:16px; color:#1a1a2e; font-weight:600;">{show.title}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Lieu</span><br><span style="font-size:15px; color:#333;">{show.location}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Cat&eacute;gorie</span><br><span style="font-size:15px; color:#333;">{show.category}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Date de publication</span><br><span style="font-size:15px; color:#333;">{date_publication}</span></td></tr>
                            </table>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding:30px 40px; text-align:center;">
                        <a href="{show_url}" style="display:inline-block; background-color:#667eea; background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:#ffffff !important; text-decoration:none; padding:16px 44px; border-radius:8px; font-weight:700; font-size:16px; letter-spacing:0.5px;">Voir mon annonce</a>
                    </td>
                </tr>
                <tr><td style="padding:30px 40px 0;"><hr style="border:none; border-top:1px solid #e0e0e0; margin:0;"></td></tr>
                <tr>
                    <td style="padding:30px 40px 10px;">
                        <h2 style="margin:0 0 6px 0; font-size:18px; color:#1a1a2e; font-weight:700;">L'accompagnement administratif complet</h2>
                        <p style="margin:0 0 12px 0; font-size:14px; color:#666; line-height:1.6;">Au-del&agrave; de la visibilit&eacute;, Spectacle'ment V&Oslash;tre propose un service d'administration complet pour lib&eacute;rer les compagnies de la gestion administrative.</p>
                        <p style="margin:0 0 20px 0; font-size:14px; color:#666; line-height:1.6;">Nous accompagnons &eacute;galement les <strong>compagnies &eacute;mergentes et artistes en devenir</strong> avec du conseil personnalis&eacute; sur tous les aspects administratifs li&eacute;s &agrave; la vie d'une compagnie : cr&eacute;ation de structure, obligations l&eacute;gales, gestion sociale, strat&eacute;gie de d&eacute;veloppement et bien plus encore.</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding:0 40px 10px;">
                        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td width="50%" style="padding:8px 8px 8px 0; vertical-align:top;"><div style="background:#f8f9fa; border-radius:8px; padding:14px 16px; border-left:3px solid #764ba2;"><span style="font-size:14px; color:#333; font-weight:600;">URSSAF</span><br><span style="font-size:13px; color:#666;">D&eacute;clarations et cotisations</span></div></td>
                                <td width="50%" style="padding:8px 0 8px 8px; vertical-align:top;"><div style="background:#f8f9fa; border-radius:8px; padding:14px 16px; border-left:3px solid #764ba2;"><span style="font-size:14px; color:#333; font-weight:600;">DSN</span><br><span style="font-size:13px; color:#666;">D&eacute;claration Sociale Nominative</span></div></td>
                            </tr>
                            <tr>
                                <td width="50%" style="padding:8px 8px 8px 0; vertical-align:top;"><div style="background:#f8f9fa; border-radius:8px; padding:14px 16px; border-left:3px solid #764ba2;"><span style="font-size:14px; color:#333; font-weight:600;">DUE</span><br><span style="font-size:13px; color:#666;">D&eacute;claration Unique d'Embauche</span></div></td>
                                <td width="50%" style="padding:8px 0 8px 8px; vertical-align:top;"><div style="background:#f8f9fa; border-radius:8px; padding:14px 16px; border-left:3px solid #764ba2;"><span style="font-size:14px; color:#333; font-weight:600;">AEM</span><br><span style="font-size:13px; color:#666;">Attestation Employeur Mensuelle</span></div></td>
                            </tr>
                            <tr>
                                <td width="50%" style="padding:8px 8px 8px 0; vertical-align:top;"><div style="background:#f8f9fa; border-radius:8px; padding:14px 16px; border-left:3px solid #764ba2;"><span style="font-size:14px; color:#333; font-weight:600;">Fiches de paie</span><br><span style="font-size:13px; color:#666;">&Eacute;dition et gestion</span></div></td>
                                <td width="50%" style="padding:8px 0 8px 8px; vertical-align:top;"><div style="background:#f8f9fa; border-radius:8px; padding:14px 16px; border-left:3px solid #764ba2;"><span style="font-size:14px; color:#333; font-weight:600;">Contrats de cession</span><br><span style="font-size:13px; color:#666;">R&eacute;daction et suivi</span></div></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="padding:10px 40px 5px; text-align:center;">
                        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
                            <tr>
                                <td style="padding:0 14px; text-align:center;"><span style="display:block; font-size:20px; color:#764ba2; font-weight:700;">30+</span><span style="font-size:12px; color:#888;">ans d'exp&eacute;rience</span></td>
                                <td style="border-left:1px solid #e0e0e0; padding:0 14px; text-align:center;"><span style="display:block; font-size:14px; color:#764ba2; font-weight:700;">S&eacute;curit&eacute;</span><span style="font-size:12px; color:#888;">juridique</span></td>
                                <td style="border-left:1px solid #e0e0e0; padding:0 14px; text-align:center;"><span style="display:block; font-size:14px; color:#764ba2; font-weight:700;">Expertise</span><span style="font-size:12px; color:#888;">d&eacute;di&eacute;e</span></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="padding:25px 40px; text-align:center;">
                        <a href="{abonnement_url}" style="display:inline-block; background:#fff; color:#764ba2; text-decoration:none; padding:14px 36px; border-radius:8px; font-weight:700; font-size:15px; border:2px solid #764ba2; letter-spacing:0.3px;">D&eacute;couvrir l'accompagnement Premium</a>
                    </td>
                </tr>
                <tr>
                    <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); padding:30px 40px; text-align:center;">
                        <p style="margin:0 0 12px 0; font-size:13px; color:rgba(255,255,255,0.75); line-height:1.6;">Pour retirer ou modifier votre fiche, contactez-nous par simple retour de mail.</p>
                        <p style="margin:0 0 4px 0; font-size:14px; color:#fff; font-weight:600;">Spectaclement v&ocirc;tre,</p>
                        <p style="margin:0; font-size:13px; color:rgba(255,255,255,0.65);">L'&eacute;quipe Spectacle'ment V&Oslash;tre</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>"""
                
                msg = MailMessage(subject=subject, recipients=[to_addr])  # type: ignore[arg-type]
                
                # Ajouter l'admin en copie cachée pour suivi
                admin_email = "contact@spectacleanimation.fr"
                if to_addr != admin_email:  # Éviter duplication si l'utilisateur EST l'admin
                    msg.bcc = [admin_email]  # type: ignore[assignment]
                
                # Assigner le bon format selon le type de spectacle
                if show.user_id:
                    # Spectacle créé par utilisateur : email HTML
                    msg.html = body_html  # type: ignore[assignment]
                    msg.body = f"Votre spectacle '{show.title}' a été validé et publié sur Spectacle'ment VØtre !\n\nConsultez votre annonce : {show_url}\n\nSpectaclement vôtre,\nL'équipe Spectacle'ment VØtre"  # type: ignore[assignment]
                else:
                    # Spectacle créé par admin : email HTML découverte
                    msg.html = body_html_decouverte  # type: ignore[assignment]
                    msg.body = f"Félicitations ! Votre talent a retenu notre attention. Nous avons créé une fiche pour vous sur notre annuaire gratuit.\n\nConsultez votre annonce : {show_url}\n\nSpectaclement vôtre,\nL'équipe Spectacle'ment VØtre"  # type: ignore[assignment]
                
                current_app.mail.send(msg)  # type: ignore[attr-defined]
                current_app.logger.info(f"[MAIL] ✓ Email envoyé à {to_addr} (copie admin: {admin_email}) pour validation de spectacle: {show.title}")
            except Exception as e:
                current_app.logger.error(f"[MAIL] ✗ Envoi impossible (validation spectacle): {e}")
                print("[MAIL] envoi automatique impossible:", e)
        else:
            if not getattr(current_app, "mail", None):
                current_app.logger.warning("[MAIL] ⚠ Flask-Mail non initialisé - Email validation non envoyé")
            elif not current_app.config.get("MAIL_USERNAME"):
                current_app.logger.warning("[MAIL] ⚠ MAIL_USERNAME non défini")
            elif not current_app.config.get("MAIL_PASSWORD"):
                current_app.logger.warning("[MAIL] ⚠ MAIL_PASSWORD non défini")
        
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
            structure = request.form.get("structure", "").strip()
            telephone = request.form.get("telephone", "").strip()
            lieu_ville = fix_mojibake(request.form.get("lieu_ville", "").strip()).split("·")[0].strip()
            code_postal = request.form.get("code_postal", "").strip()
            region = fix_mojibake(request.form.get("region", "").strip())
            nom = request.form.get("nom", "").strip()
            date_debut = request.form.get("date_debut", "").strip()
            date_fin = request.form.get("date_fin", "").strip()
            dates_horaires = request.form.get("dates_horaires", "").strip()
            # Auto-construire dates_horaires à partir des sélecteurs de date si remplis
            if date_debut:
                from datetime import datetime as _dt
                try:
                    d1 = _dt.strptime(date_debut, "%Y-%m-%d").strftime("%d/%m/%Y")
                    if date_fin and date_fin != date_debut:
                        d2 = _dt.strptime(date_fin, "%Y-%m-%d").strftime("%d/%m/%Y")
                        dates_horaires = f"Du {d1} au {d2}"
                    else:
                        dates_horaires = d1
                except ValueError:
                    pass
            type_espace = request.form.get("type_espace", "").strip()
            type_evenement = request.form.get("type_evenement", "").strip()
            autre_evenement = request.form.get("autre_evenement", "").strip()
            auto_datetime = request.form.get("auto_datetime", "")
            
            # Si "Autre" est sélectionné pour le type d'événement et qu'un type personnalisé est renseigné
            if type_evenement == "Autre" and autre_evenement:
                type_evenement = autre_evenement
            
            genre_recherche = request.form.get("genre_recherche", "").strip()
            
            age_range = request.form.get("age_range", "").strip()
            jauge = request.form.get("jauge", "").strip()
            budget = request.form.get("budget", "").strip()
            contraintes = request.form.get("contraintes", "").strip()
            accessibilite = request.form.get("accessibilite", "").strip()
            contact_email = request.form.get("contact_email", "").strip()
            intitule = request.form.get("intitule", "").strip()

            # Matching fields (accordions)
            specialites_recherchees = ",".join(request.form.getlist("specialites_recherchees"))
            evenements_contexte = ",".join(request.form.getlist("evenements_contexte"))
            lieux_souhaites = ",".join(request.form.getlist("lieux_souhaites"))

            # Public Cible v2 (matching strict)
            public_categories = ",".join(request.form.getlist("public_categories"))
            public_sous_options = ",".join(request.form.getlist("public_sous_options"))

            # Portée géographique
            portee_nationale = request.form.get("portee_nationale", "1") == "1"

            # Si genre_recherche est vide mais des spécialités sont cochées, prendre la première
            if not genre_recherche and specialites_recherchees:
                genre_recherche = specialites_recherchees.split(",")[0]

            # Si type_espace vide, le déduire des lieux cochés
            if not type_espace and lieux_souhaites:
                type_espace = lieux_souhaites.split(",")[0]

            # Validation basique - TELEPHONE est optionnel !
            champs_requis = {
                "Structure": structure, "Ville": lieu_ville, "Code postal": code_postal,
                "Nom": nom, "Dates et horaires": dates_horaires,
                "Spécialité (cochez au moins une case)": genre_recherche,
                "Tranche d'âge": age_range, "Jauge": jauge, "Budget": budget,
                "Email de contact": contact_email, "Intitulé": intitule,
            }
            champs_vides = [nom_champ for nom_champ, val in champs_requis.items() if not val]
            if champs_vides:
                flash(f"Champs manquants : {', '.join(champs_vides)}", "danger")
                # Préserver les checkboxes cochées au re-rendu
                return render_template("demande_animation.html", user=current_user(),
                                       specialites_data=SPECIALITES, evenements_data=EVENEMENTS, lieux_data=LIEUX), 400

            # Envoi d'email si configuré
            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
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
Type d'événement: {type_evenement or 'Non précisé'}
Genre recherché: {genre_recherche}
Spécialités recherchées: {specialites_recherchees or 'Non précisées'}
Tranche d'âge: {age_range}
Jauge: {jauge}
Budget: {budget}
Contraintes techniques: {contraintes}
Accessibilité: {accessibilite}
"""
                    msg = MailMessage(subject="Nouvelle demande d'animation", recipients=[to_addr])  # type: ignore[arg-type]
                    msg.body = body  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                    current_app.logger.info(f"[MAIL] ✓ Email envoyé à l'admin pour demande d'animation de {structure}")
                except Exception as e:  # pragma: no cover
                    current_app.logger.error(f"[MAIL] ✗ Envoi impossible (demande animation): {e}")
                    print("[MAIL] envoi impossible:", e)
            else:
                if not getattr(current_app, "mail", None):
                    current_app.logger.warning("[MAIL] ⚠ Flask-Mail non initialisé - Email demande animation non envoyé")
                elif not current_app.config.get("MAIL_USERNAME"):
                    current_app.logger.warning("[MAIL] ⚠ MAIL_USERNAME non défini")
                elif not current_app.config.get("MAIL_PASSWORD"):
                    current_app.logger.warning("[MAIL] ⚠ MAIL_PASSWORD non défini")

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
                date_debut=date_debut or None,
                date_fin=date_fin or None,
                type_espace=type_espace,
                type_evenement=type_evenement,
                genre_recherche=genre_recherche,
                age_range=age_range,
                jauge=jauge,
                budget=budget,
                contraintes=contraintes,
                accessibilite=accessibilite,
                contact_email=contact_email,
                intitule=intitule,
                specialites_recherchees=specialites_recherchees,
                evenements_contexte=evenements_contexte,
                lieux_souhaites=lieux_souhaites,
                public_categories=public_categories or None,
                public_sous_options=public_sous_options or None,
                portee_nationale=portee_nationale,
                is_private=False,  # Publique par défaut
                approved=False  # En attente de validation par l'admin
            )
            db.session.add(demande)
            db.session.commit()

            # Email d'accusé de réception à l'auteur de la demande
            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                try:
                    confirmation_html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background:#f4f4f7; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7; padding:30px 0;">
    <tr>
        <td align="center">
            <table role="presentation" width="620" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:12px; box-shadow:0 4px 24px rgba(0,0,0,0.08); overflow:hidden; max-width:620px;">
                <tr>
                    <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); padding:40px 40px 30px; text-align:center;">
                        <img src="https://spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment VØtre" width="120" style="display:block; margin:0 auto 16px; max-width:120px; height:auto;">
                        <h1 style="margin:0 0 8px 0; font-size:26px; color:#fff; font-weight:700; letter-spacing:0.5px;">Spectacle'ment V&Oslash;tre</h1>
                        <p style="margin:0; font-size:14px; color:rgba(255,255,255,0.8); letter-spacing:2px; text-transform:uppercase;">Annuaire du spectacle vivant</p>
                        <p style="margin:12px 0 0 0; font-size:15px; color:rgba(255,255,255,0.95); font-style:italic;">Vous ne cherchez plus, ce sont les artistes qui viennent &agrave; vous !</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding:0 40px;">
                        <div style="background:#e8f5e9; border:1px solid #a5d6a7; padding:20px; border-radius:0 0 10px 10px; text-align:center; margin-bottom:25px;">
                            <p style="margin:0; font-size:20px; font-weight:700; color:#2e7d32;">Bravo et merci ! Votre demande est en cours de validation</p>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding:0 40px 20px;">
                        <p style="margin:0 0 18px 0; font-size:16px; color:#333; line-height:1.7;">Bonjour <strong>{nom}</strong>,</p>
                        <p style="margin:0 0 18px 0; font-size:15px; color:#444; line-height:1.7;">Nous avons bien re&ccedil;u votre appel d'offre et son intitul&eacute; <strong>&laquo; {intitule} &raquo;</strong>.<br>Notre &eacute;quipe va le v&eacute;rifier et le publier dans les <strong>24 heures</strong>.</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding:0 40px 25px;">
                        <div style="background:linear-gradient(135deg,#f5f7fa 0%,#e8ecf1 100%); border-radius:10px; padding:24px; border-left:5px solid #764ba2;">
                            <p style="margin:0 0 14px 0; font-size:15px; color:#764ba2; font-weight:700; text-transform:uppercase; letter-spacing:1px;">R&eacute;capitulatif</p>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Structure</span><br><span style="font-size:15px; color:#333; font-weight:600;">{structure}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Genre recherch&eacute;</span><br><span style="font-size:15px; color:#333; font-weight:600;">{genre_recherche}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Sp&eacute;cialit&eacute;s</span><br><span style="font-size:15px; color:#333;">{specialites_recherchees.replace(',', ', ') if specialites_recherchees else 'Non pr&eacute;cis&eacute;es'}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Lieu</span><br><span style="font-size:15px; color:#333;">{lieu_ville}{f' ({code_postal})' if code_postal else ''}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">R&eacute;gion</span><br><span style="font-size:15px; color:#333;">{region or 'Non pr&eacute;cis&eacute;e'}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Date(s)</span><br><span style="font-size:15px; color:#333;">{dates_horaires}</span></td></tr>
                                <tr><td style="padding:6px 0;"><span style="font-size:12px; color:#888; text-transform:uppercase; letter-spacing:1px;">Budget</span><br><span style="font-size:15px; color:#333; font-weight:600;">{budget}</span></td></tr>
                            </table>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding:0 40px 25px;">
                        <div style="background:#e8f5e9; border:1px solid #a5d6a7; border-radius:8px; padding:14px 18px; text-align:center;">
                            <p style="margin:0; font-size:14px; color:#2e7d32; font-weight:600;">Vous recevrez un second email d&egrave;s que votre annonce sera en ligne.</p>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); padding:30px 40px; text-align:center;">
                        <p style="margin:0 0 4px 0; font-size:14px; color:#fff; font-weight:600;">Spectaclement v&ocirc;tre,</p>
                        <p style="margin:0 0 8px 0; font-size:13px; color:rgba(255,255,255,0.65);">L'&eacute;quipe Spectacle'ment V&Oslash;tre</p>
                        <p style="margin:0; font-size:12px; color:rgba(255,255,255,0.5);">contact@spectacleanimation.fr</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>"""
                    msg_conf = MailMessage(
                        subject=f"⏳ Votre demande d'animation est en attente de validation",
                        recipients=[contact_email]
                    )
                    msg_conf.html = confirmation_html
                    current_app.mail.send(msg_conf)
                    current_app.logger.info(f"[MAIL] ✓ Email accusé de réception envoyé à {contact_email}")
                except Exception as e:
                    current_app.logger.error(f"[MAIL] ✗ Envoi email accusé réception impossible: {e}")

            flash("✅ Votre demande a bien été envoyée ! Elle sera publiée après validation par notre équipe (sous 24h).", "success")
            return redirect(url_for("home"))

        # Récupérer les spectacles "à la une" pour affichage
        spectacles_une = Show.query.filter(
            Show.approved.is_(True),
            Show.category.ilike('%Spectacle à la une%')
        ).order_by(Show.created_at.desc()).limit(8).all()

        return render_template("demande_animation.html", user=current_user(), spectacles_une=spectacles_une,
                               specialites_data=SPECIALITES, evenements_data=EVENEMENTS, lieux_data=LIEUX)

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
                # Champs structurés (matching)
                Show.age_range.in_(['enfant', 'enfant_2_6', 'enfant_5_10', 'enfants_2_10', 'familial', 'tout public']),
                # Fallback texte libre
                Show.category.ilike('%enfant%'),
                Show.category.ilike('%jeune public%'),
                Show.category.ilike('%famille%'),
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
        return render_template("spectacles_enfants.html", shows=shows, user=current_user())

    @app.route("/animations-enfants")
    def animations_enfants():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                # Champs structurés (matching)
                Show.specialites.ilike('%Atelier%'),
                Show.specialites.ilike('%Conte%'),
                Show.specialites.ilike('%Marionnettes%'),
                Show.specialites.ilike('%Clown%'),
                Show.age_range.in_(['enfant', 'enfant_2_6', 'enfant_5_10', 'enfants_2_10', 'familial']),
                # Fallback texte libre
                Show.category.ilike('%animation%'),
                Show.category.ilike('%atelier%'),
                Show.category.ilike('%jeu%'),
                Show.title.ilike('%animation%')
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
        return render_template("animations_enfants.html", shows=shows, user=current_user())

    @app.route("/spectacles-noel")
    def spectacles_noel():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                # Champs structurés (matching)
                Show.evenements.ilike('%Arbre de Noël%'),
                Show.evenements.ilike('%Marché de Noël%'),
                Show.specialites.ilike('%Père Noël%'),
                # Fallback texte libre
                Show.title.ilike('%noël%'),
                Show.title.ilike('%noel%'),
                Show.description.ilike('%noël%'),
                Show.description.ilike('%noel%'),
                Show.category.ilike('%noël%'),
                Show.category.ilike('%noel%')
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
        return render_template("spectacles_noel.html", shows=shows, user=current_user())

    # ─── 🎄 Pages thématiques longue traîne Noël ───
    @app.route("/pere-noel-a-domicile")
    def pere_noel_a_domicile():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.specialites.ilike('%Père Noël%'),
                Show.title.ilike('%père noël%'),
                Show.title.ilike('%pere noel%'),
                Show.description.ilike('%père noël%'),
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).limit(24).all()
        return render_template("pere_noel_a_domicile.html", shows=shows, user=current_user())

    @app.route("/spectacles-noel-ecole")
    def spectacles_noel_ecole():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.title.ilike('%noël%'),
                Show.title.ilike('%noel%'),
                Show.description.ilike('%noël%'),
                Show.description.ilike('%noel%'),
                Show.evenements.ilike('%Arbre de Noël%'),
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).limit(24).all()
        return render_template("spectacles_noel_ecole.html", shows=shows, user=current_user())

    @app.route("/spectacles-noel-entreprise")
    def spectacles_noel_entreprise():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                Show.evenements.ilike('%Arbre de Noël%'),
                Show.title.ilike('%noël%'),
                Show.title.ilike('%noel%'),
                Show.description.ilike('%noël%'),
                Show.description.ilike('%noel%'),
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).limit(24).all()
        return render_template("spectacles_noel_entreprise.html", shows=shows, user=current_user())

    @app.route("/animations-entreprises")
    def animations_entreprises():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                # Champs structurés (matching)
                Show.evenements.ilike('%Comité d\'entreprise%'),
                Show.evenements.ilike('%CSE%'),
                Show.evenements.ilike('%Séminaire%'),
                Show.evenements.ilike('%Animation commerciale%'),
                Show.evenements.ilike('%Inauguration%'),
                Show.evenements.ilike('%Journée portes ouvertes%'),
                # Fallback texte libre
                Show.category.ilike('%entreprise%'),
                Show.category.ilike('%corporate%'),
                Show.category.ilike('%CSE%'),
                Show.description.ilike('%entreprise%'),
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
        return render_template("animations_entreprises.html", shows=shows, user=current_user())

    @app.route("/marionnettes")
    def marionnettes():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                # Champ structuré (matching)
                Show.specialites.ilike('%Marionnettes%'),
                # Fallback texte libre
                Show.category.ilike('%marionnette%'),
                Show.title.ilike('%marionnette%'),
                Show.description.ilike('%marionnette%')
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
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
                # Champs structurés (matching)
                Show.specialites.ilike('%Magie et Magicien%'),
                Show.specialites.ilike('%Prestidigitateur%'),
                Show.specialites.ilike('%Mentaliste%'),
                # Fallback texte libre
                Show.category.ilike('%magie%'),
                Show.category.ilike('%magicien%'),
                Show.title.ilike('%magie%'),
                Show.title.ilike('%magicien%')
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
        return render_template("magiciens.html", shows=shows, user=current_user())

    @app.route("/clowns")
    def clowns():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                # Champ structuré (matching)
                Show.specialites.ilike('%Clown%'),
                # Fallback texte libre
                Show.category.ilike('%clown%'),
                Show.title.ilike('%clown%'),
                Show.description.ilike('%clown%')
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
        return render_template("clowns.html", shows=shows, user=current_user())

    # ------------------------------------------------------------------
    # Redirections 301 pour anciennes URLs disparues (signalées par GSC)
    # Évite les 404 dans l'index Google et transmet le jus SEO.
    # ------------------------------------------------------------------
    @app.route("/orchestre/")
    @app.route("/orchestre")
    def _redir_orchestre():
        return redirect(url_for("evenements"), code=301)

    @app.route("/concert/")
    @app.route("/concert")
    def _redir_concert():
        return redirect(url_for("evenements"), code=301)

    @app.route("/enfant/")
    @app.route("/enfant")
    def _redir_enfant():
        return redirect(url_for("spectacles_enfants"), code=301)

    @app.route("/atelier/")
    @app.route("/atelier")
    def _redir_atelier():
        return redirect(url_for("animations_enfants"), code=301)

    @app.route("/animations-anniversaire")
    def animations_anniversaire():
        shows = Show.query.filter(
            Show.approved.is_(True),
            or_(
                # Champ structuré (matching)
                Show.evenements.ilike('%Anniversaire enfant%'),
                Show.evenements.ilike('%Boum pour enfant%'),
                Show.evenements.ilike('%Kermesse%'),
                # Fallback texte libre
                Show.category.ilike('%anniversaire%'),
                Show.title.ilike('%anniversaire%'),
                Show.description.ilike('%anniversaire%'),
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc()).all()
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

        # 2) recherche textuelle — filtrer uniquement les approuvés
        base = Show.query.filter(Show.approved.is_(True))
        if q:
            like = f"%{q}%"
            base = base.filter(Show.title.ilike(like) | Show.description.ilike(like))

        # Limiter les résultats pour éviter de charger toute la DB en mémoire
        shows = base.limit(200).all()
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

    @app.route("/qui-sommes-nous")
    def about():
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            nom = request.form.get("nom", "").strip()
            email = request.form.get("email", "").strip()
            message = request.form.get("message", "").strip()
            try:
                if hasattr(current_app, "mail") and current_app.mail:
                    msg = MailMessage(
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
        
        # Base de la requête - Filtrer les demandes privées ET non approuvées sur la page publique
        user = current_user()
        if user and user.is_admin:
            # Admin voit toutes les demandes (sauf les privées)
            demandes_query = DemandeAnimation.query.filter(DemandeAnimation.is_private == False).order_by(DemandeAnimation.created_at.desc())
        else:
            # Public voit seulement les demandes approuvées et publiques
            demandes_query = DemandeAnimation.query.filter(
                DemandeAnimation.is_private == False,
                DemandeAnimation.approved == True
            ).order_by(DemandeAnimation.created_at.desc())
        
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
        
        # Vérifier si l'utilisateur a un spectacle approuvé
        has_show = False
        if user and user.is_admin:
            has_show = True
        elif user:
            has_show = Show.query.filter(Show.user_id == user.id, Show.approved.is_(True)).count() > 0
        
        return render_template("demandes_animation.html", demandes=demandes, page=page, nb_pages=nb_pages, total=total, per_page=per_page, user=current_user(), has_show=has_show, categories=categories, regions=regions, categorie=categorie, region=region, spectacles_une=spectacles_une)

    @app.route("/mes-appels-offres")
    @login_required
    def mes_appels_offres():
        """Page pour les utilisateurs connectés avec toutes les informations visibles"""
        from models.models import DemandeAnimation
        
        # Vérifier que l'utilisateur a un spectacle approuvé
        user = current_user()
        has_show = Show.query.filter(
            Show.user_id == user.id,
            Show.approved.is_(True)
        ).count() > 0
        
        if not has_show and not user.is_admin:
            flash("Vous devez avoir un spectacle approuvé pour accéder aux appels d'offre.", "warning")
            return redirect(url_for("company_dashboard"))
        
        page = request.args.get('page', 1, type=int)
        per_page = 12
        categorie = request.args.get('categorie', '').strip()
        region = request.args.get('region', '').strip()
        
        # Les utilisateurs connectés voient les demandes publiques approuvées
        demandes_query = DemandeAnimation.query.filter(
            DemandeAnimation.is_private == False,
            DemandeAnimation.approved == True
        ).order_by(DemandeAnimation.created_at.desc())
        
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
        
        return render_template("mes_appels_offres.html", demandes=demandes, page=page, nb_pages=nb_pages, total=total, per_page=per_page, user=current_user(), categories=categories, regions=regions, categorie=categorie, region=region)

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
        return redirect(url_for("admin_demandes_animation"))

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
            demande.date_debut = request.form.get("date_debut", demande.date_debut) or None
            demande.date_fin = request.form.get("date_fin", demande.date_fin) or None
            # Auto-reconstruire dates_horaires si les dates sont renseignées
            _new_debut = request.form.get("date_debut", "").strip()
            _new_fin = request.form.get("date_fin", "").strip()
            if _new_debut:
                from datetime import datetime as _dt3
                try:
                    d1 = _dt3.strptime(_new_debut, "%Y-%m-%d").strftime("%d/%m/%Y")
                    if _new_fin and _new_fin != _new_debut:
                        d2 = _dt3.strptime(_new_fin, "%Y-%m-%d").strftime("%d/%m/%Y")
                        demande.dates_horaires = f"Du {d1} au {d2}"
                    else:
                        demande.dates_horaires = d1
                except ValueError:
                    demande.dates_horaires = request.form.get("dates_horaires", demande.dates_horaires)
            else:
                demande.dates_horaires = request.form.get("dates_horaires", demande.dates_horaires)
            demande.type_espace = request.form.get("type_espace", demande.type_espace)
            demande.type_evenement = request.form.get("type_evenement", demande.type_evenement)
            demande.genre_recherche = request.form.get("genre_recherche", demande.genre_recherche)
            demande.age_range = request.form.get("age_range", demande.age_range)
            demande.jauge = request.form.get("jauge", demande.jauge)
            demande.budget = request.form.get("budget", demande.budget)
            demande.intitule = request.form.get("intitule", demande.intitule)
            demande.contraintes = request.form.get("contraintes", demande.contraintes)
            demande.accessibilite = request.form.get("accessibilite", demande.accessibilite)
            demande.contact_email = request.form.get("contact_email", demande.contact_email)
            demande.code_postal = request.form.get("code_postal", demande.code_postal)
            demande.region = request.form.get("region", demande.region)
            demande.specialites_recherchees = ",".join(request.form.getlist("specialites_recherchees")[:4]) or demande.specialites_recherchees
            demande.evenements_contexte = ",".join(request.form.getlist("evenements_contexte")) or demande.evenements_contexte
            demande.lieux_souhaites = ",".join(request.form.getlist("lieux_souhaites")) or demande.lieux_souhaites
            _new_pc = ",".join(request.form.getlist("public_categories"))
            _new_pso = ",".join(request.form.getlist("public_sous_options"))
            demande.public_categories = _new_pc if _new_pc else demande.public_categories
            demande.public_sous_options = _new_pso if _new_pso else demande.public_sous_options
            demande.portee_nationale = request.form.get("portee_nationale", "1") == "1"
            demande.is_private = request.form.get("is_private") == "on"
            db.session.commit()
            flash("✅ Demande modifiée avec succès !", "success")
            return redirect(url_for("admin_demandes_animation"))
        return render_template("demande_animation.html", demande=demande, user=current_user(),
                               specialites_data=SPECIALITES, evenements_data=EVENEMENTS, lieux_data=LIEUX)

    @app.route("/admin/approve-demande/<int:demande_id>")
    @login_required
    @admin_required
    def approve_demande_animation(demande_id):
        """Approuver et publier un appel d'offre, puis envoyer un email à l'auteur"""
        from models.models import DemandeAnimation
        demande = DemandeAnimation.query.get_or_404(demande_id)
        
        # Vérifier si déjà approuvé
        if demande.approved:
            flash("⚠️ Cette demande est déjà publiée.", "warning")
            return redirect(url_for("admin_demandes_animation"))
        
        # Approuver la demande
        demande.approved = True
        db.session.commit()
        
        # Envoyer un email à l'auteur
        try:
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .logo {{ text-align: center; margin: 20px 0; }}
        .logo img {{ max-width: 200px; height: auto; }}
        .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
        h2 {{ color: #1b2a4e; margin-top: 0; }}
        .success-box {{ background: linear-gradient(135deg, #28a745 0%, #34ce57 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
        .success-box h3 {{ margin-top: 0; color: white; }}
        .info-box {{ background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
        .btn {{ display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="logo">
        <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre">
    </div>
    <div class="content">
        <div class="success-box">
            <h3>✅ Votre appel d'offre est maintenant en ligne !</h3>
        </div>
        
        <h2>Félicitations !</h2>
        <p>Bonjour,</p>
        <p>Votre appel d'offre <strong>"{demande.intitule or demande.genre_recherche}"</strong> a été validé et est maintenant visible sur notre site.</p>
        
        <div class="info-box">
            <p><strong>📋 Votre demande :</strong></p>
            <p><strong>Genre recherché :</strong> {demande.genre_recherche}<br>
            <strong>Spécialités :</strong> {demande.specialites_recherchees.replace(',', ', ') if demande.specialites_recherchees else 'Non précisées'}<br>
            <strong>Lieu :</strong> {demande.lieu_ville}<br>
            <strong>Date(s) :</strong> {demande.dates_horaires}</p>
        </div>
        
        <p style="text-align: center;">
            <a href="https://www.spectacleanimation.fr/demandes-animation" class="btn" style="display:inline-block;padding:14px 28px;background:#1b5e20;color:white;text-decoration:none;border-radius:8px;font-weight:700;font-size:1rem;">👉 Voir mon appel d'offre publié</a>
        </p>
        
        <p>Les compagnies de spectacle correspondant à votre recherche vont pouvoir consulter votre demande et vous contacter directement à l'adresse <strong>{demande.contact_email}</strong>.</p>
        
        <div class="footer">
            <p><strong>L'équipe Spectacle'ment Vôtre</strong><br>
            contact@spectacleanimation.fr</p>
        </div>
    </div>
</body>
</html>
"""
            msg = MailMessage(
                subject=f"✅ Votre appel d'offre est en ligne - {demande.genre_recherche} à {demande.lieu_ville}",
                recipients=[demande.contact_email]
            )
            msg.html = body_html
            
            # Ajouter l'admin en copie cachée pour suivi
            admin_email = "contact@spectacleanimation.fr"
            if demande.contact_email != admin_email:  # Éviter duplication
                msg.bcc = [admin_email]
            
            current_app.mail.send(msg)
            print(f"[DEBUG] ✅ Email de confirmation envoyé à {demande.contact_email} (copie admin: {admin_email})")
            flash(f"✅ Appel d'offre approuvé et publié ! Email de confirmation envoyé à {demande.contact_email}", "success")
        except Exception as e:
            print(f"[MAIL] ❌ Erreur envoi email de confirmation : {e}")
            flash(f"✅ Appel d'offre approuvé et publié ! ⚠️ Erreur lors de l'envoi de l'email de confirmation.", "warning")
        
        return redirect(url_for("admin_demandes_animation"))

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
        
        # Demandes EN ATTENTE de validation (approved=False, is_private=False)
        pending = DemandeAnimation.query.filter(
            DemandeAnimation.is_private.is_(False),
            DemandeAnimation.approved.is_(False)
        ).order_by(DemandeAnimation.created_at.desc()).all()
        
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
        nb_en_attente = len(pending)
        
        return render_template(
            "admin_demandes_animation.html", 
            pending=pending,
            demandes=demandes, 
            page=page, 
            nb_pages=nb_pages, 
            total=total, 
            per_page=per_page,
            nb_privees=nb_privees,
            nb_publiques=nb_publiques,
            nb_en_attente=nb_en_attente,
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
            lieu_ville = fix_mojibake(request.form.get("lieu_ville", "").strip()).split("·")[0].strip()
            code_postal = request.form.get("code_postal", "").strip()
            region = fix_mojibake(request.form.get("region", "").strip())
            nom = request.form.get("nom", "").strip()
            date_debut = request.form.get("date_debut", "").strip()
            date_fin = request.form.get("date_fin", "").strip()
            dates_horaires = request.form.get("dates_horaires", "").strip()
            # Auto-construire dates_horaires à partir des sélecteurs de date si remplis
            if date_debut:
                from datetime import datetime as _dt2
                try:
                    d1 = _dt2.strptime(date_debut, "%Y-%m-%d").strftime("%d/%m/%Y")
                    if date_fin and date_fin != date_debut:
                        d2 = _dt2.strptime(date_fin, "%Y-%m-%d").strftime("%d/%m/%Y")
                        dates_horaires = f"Du {d1} au {d2}"
                    else:
                        dates_horaires = d1
                except ValueError:
                    pass
            type_espace = request.form.get("type_espace", "").strip()
            type_evenement = request.form.get("type_evenement", "").strip()
            autre_evenement = request.form.get("autre_evenement", "").strip()
            
            # Si "Autre" est sélectionné pour le type d'événement
            if type_evenement == "Autre" and autre_evenement:
                type_evenement = autre_evenement
            
            genre_recherche = request.form.get("genre_recherche", "").strip()
            age_range = request.form.get("age_range", "").strip()
            jauge = request.form.get("jauge", "").strip()
            budget = request.form.get("budget", "").strip()
            intitule = request.form.get("intitule", "").strip()
            contraintes = request.form.get("contraintes", "").strip()
            accessibilite = request.form.get("accessibilite", "").strip()
            contact_email = request.form.get("contact_email", "").strip()
            is_private = request.form.get("is_private") == "on"
            send_emails = request.form.get("send_emails") == "on"
            publish_immediately = request.form.get("publish_immediately") == "on"

            # Matching fields (accordions)
            specialites_recherchees = ",".join(request.form.getlist("specialites_recherchees"))
            evenements_contexte = ",".join(request.form.getlist("evenements_contexte"))
            lieux_souhaites = ",".join(request.form.getlist("lieux_souhaites"))

            # Public Cible v2
            public_categories = ",".join(request.form.getlist("public_categories"))
            public_sous_options = ",".join(request.form.getlist("public_sous_options"))

            # Portée géographique
            portee_nationale = request.form.get("portee_nationale", "1") == "1"

            # Validation basique - TELEPHONE est optionnel ! age_range remplacé par public_categories (Public Cible v2)
            if not all([structure, lieu_ville, nom, dates_horaires, 
                       genre_recherche, jauge, budget, contact_email]):
                flash("Veuillez remplir tous les champs obligatoires.", "danger")
                return render_template("admin_create_demande.html", user=current_user(),
                                       specialites_data=SPECIALITES, evenements_data=EVENEMENTS, lieux_data=LIEUX), 400

            # Créer la demande
            demande = DemandeAnimation(
                auto_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                structure=structure,
                telephone=telephone,
                lieu_ville=lieu_ville,
                code_postal=code_postal,
                region=region,
                nom=nom,
                dates_horaires=dates_horaires,
                date_debut=date_debut or None,
                date_fin=date_fin or None,
                type_espace=type_espace,
                type_evenement=type_evenement,
                genre_recherche=genre_recherche,
                age_range=age_range,
                jauge=jauge,
                budget=budget,
                intitule=intitule,
                contraintes=contraintes,
                accessibilite=accessibilite,
                contact_email=contact_email,
                specialites_recherchees=specialites_recherchees,
                evenements_contexte=evenements_contexte,
                lieux_souhaites=lieux_souhaites,
                public_categories=public_categories or None,
                public_sous_options=public_sous_options or None,
                portee_nationale=portee_nationale,
                is_private=is_private,
                approved=publish_immediately  # Approuvé seulement si demandé
            )
            db.session.add(demande)
            db.session.commit()

            # Envoyer un email récapitulatif à l'admin à chaque création
            admin_email = current_user().email if current_user() and current_user().email else None
            if admin_email and getattr(current_app, "mail", None):
                try:
                    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .logo {{ text-align: center; margin: 20px 0; }}
        .logo img {{ max-width: 200px; height: auto; }}
        .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
        h2 {{ color: #1b2a4e; margin-top: 0; }}
        .create-notice {{ background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%); color: white; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; font-weight: bold; }}
        .info-box {{ background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
        .info-item {{ background-color: rgba(255,255,255,0.9); padding: 10px; border-radius: 5px; border-left: 3px solid #1976d2; }}
        .status-box {{ background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ff9800; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="logo">
        <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre">
    </div>
    <div class="content">
        <div class="create-notice">
            ✅ NOUVEL APPEL D'OFFRE CRÉÉ
        </div>
        <p style="font-size:0.95em; color:#444; margin:0 0 16px 0;"><strong>Appel d'offre créé :</strong> {demande.intitule or demande.genre_recherche}</p>
        
        <div class="info-box">
            <p><strong>📋 Informations de l'appel d'offre :</strong></p>
            <div class="info-grid">
                <div class="info-item">
                    <strong>🏢 Structure :</strong> {demande.structure}
                </div>
                <div class="info-item">
                    <strong>👤 Contact :</strong> {demande.nom}
                </div>
                <div class="info-item">
                    <strong>📍 Lieu :</strong> {demande.lieu_ville}
                </div>
                <div class="info-item">
                    <strong>📅 Date(s) :</strong> {demande.dates_horaires}
                </div>
                <div class="info-item">
                    <strong>🎭 Genre :</strong> {demande.genre_recherche}
                </div>
                <div class="info-item">
                    <strong>👥 Jauge :</strong> {demande.jauge}
                </div>
                <div class="info-item">
                    <strong>💰 Budget :</strong> {demande.budget}
                </div>
                <div class="info-item">
                    <strong>👶 Public :</strong> {demande.age_range}
                </div>
            </div>
            <p><strong>🏢 Type d'espace :</strong> {demande.type_espace}</p>
            <p><strong>📋 Intitulé :</strong> {demande.intitule or 'Non précisé'}</p>
            <p><strong>♿ Accessibilité :</strong> {demande.accessibilite or 'Non précisée'}</p>
            <p><strong>📝 Contraintes :</strong> {demande.contraintes or 'Aucune'}</p>
            <p><strong>📧 Email :</strong> {demande.contact_email}</p>
            <p><strong>📞 Téléphone :</strong> {demande.telephone}</p>
        </div>
        
        <div class="status-box">
            <p><strong>🔒 Statut :</strong> {'🔒 BROUILLON PRIVÉ (non publié)' if is_private else '📢 PUBLIC'}</p>
            <p><strong>✅ Validation :</strong> {'✅ APPROUVÉ (publié immédiatement)' if publish_immediately else '⏳ EN ATTENTE (nécessite validation)'}</p>
            <p><strong>📧 Emails compagnies :</strong> {'✅ OUI (redirection vers sélection)' if send_emails else '❌ NON'}</p>
        </div>
        
        <div class="footer">
            <p><strong>L'équipe Spectacle'ment Vôtre</strong><br>
            Notification automatique de création</p>
        </div>
    </div>
</body>
</html>
"""
                    status_text = "Brouillon privé" if is_private else ("Publié" if publish_immediately else "En attente")
                    msg = MailMessage(
                        subject=f"✅ Nouvel appel d'offre créé ({status_text}) : {demande.genre_recherche} à {demande.lieu_ville}",
                        recipients=[admin_email]
                    )
                    msg.html = body_html
                    current_app.mail.send(msg)
                    print(f"[CREATE] ✅ Email de notification envoyé à {admin_email}")
                except Exception as e:
                    print(f"[CREATE] ❌ Erreur envoi email : {e}")

            # Si brouillon privé
            if is_private:
                flash("🔒 Brouillon privé créé ! Non publié sur le site.", "success")
                return redirect(url_for("demandes_animation"))
            
            # Si publication immédiate
            if publish_immediately:
                # Si envoi d'emails souhaité, rediriger vers la page d'envoi
                if send_emails:
                    flash("✅ Carte créée et publiée ! Sélectionnez les catégories et régions pour l'envoi.", "success")
                    return redirect(url_for("envoyer_demande_animation", demande_id=demande.id))
                else:
                    flash("✅ Appel d'offre publié sur le site (aucun email envoyé).", "success")
            else:
                flash("⏳ Appel d'offre créé ! En attente de validation avant publication.", "info")
            
            return redirect(url_for("demandes_animation"))

        return render_template("admin_create_demande.html", user=current_user(),
                               specialites_data=SPECIALITES, evenements_data=EVENEMENTS, lieux_data=LIEUX)

    @app.route("/admin/envoyer-demande/<int:demande_id>", methods=["GET", "POST"])
    @login_required
    @admin_required
    def envoyer_demande_animation(demande_id):
        """Interface pour envoyer une demande d'animation aux utilisateurs par catégorie"""
        from models.models import DemandeAnimation
        demande = DemandeAnimation.query.get_or_404(demande_id)
        
        if request.method == "POST":
            print(f"[DEBUG] POST reçu pour demande_id={demande_id}")
            action = request.form.get("action", "preview")
            print(f"[DEBUG] Action: {action}")
            
            # === ACTION send_matched_recap_only : envoie UNIQUEMENT le récap à l'organisateur ===
            # Réutilise les compagnies cochées dans la liste auto-matching, sans envoyer aux artistes
            if action == "send_matched_recap_only":
                matched_ids = request.form.getlist("matched_show_ids")
                print(f"[DEBUG] send_matched_recap_only : {len(matched_ids)} shows cochés")
                if not matched_ids:
                    flash("Veuillez cocher au moins une compagnie pour le récap.", "warning")
                    return redirect(request.url)
                try:
                    show_ids = [int(sid) for sid in matched_ids]
                except ValueError:
                    flash("IDs invalides.", "danger")
                    return redirect(request.url)
                shows_recap = Show.query.filter(Show.id.in_(show_ids), Show.approved.is_(True)).all()
                if not shows_recap:
                    flash("Aucune fiche valide trouvée.", "warning")
                    return redirect(url_for("admin_demandes_animation"))
                ok = _send_recap_to_organisateur(demande, shows_recap)
                if ok:
                    flash(f"📧 Récap envoyé à l'organisateur ({demande.contact_email}) avec {len(shows_recap)} fiche(s). Aucun mail aux artistes.", "success")
                else:
                    flash("⚠️ Le récap n'a pas pu être envoyé à l'organisateur (voir les logs).", "warning")
                return redirect(url_for("admin_demandes_animation"))
            
            # === ACTION send_matched : envoi direct aux shows sélectionnés par auto-matching ===
            if action == "send_matched":
                matched_ids = request.form.getlist("matched_show_ids")
                print(f"[DEBUG] Envoi auto-matching : {len(matched_ids)} shows sélectionnés: {matched_ids}")
                if not matched_ids:
                    flash("Veuillez sélectionner au moins une compagnie.", "warning")
                    return redirect(request.url)
                
                # Charger les shows par ID
                try:
                    show_ids = [int(sid) for sid in matched_ids]
                except ValueError:
                    flash("IDs invalides.", "danger")
                    return redirect(request.url)
                
                shows = Show.query.filter(Show.id.in_(show_ids), Show.approved.is_(True)).all()
                print(f"[DEBUG] {len(shows)} shows chargés pour envoi")
                
                # Vérifier si mail est configuré
                if not getattr(current_app, "mail", None):
                    flash("❌ Erreur : le service email n'est pas configuré.", "danger")
                    return redirect(url_for("admin_demandes_animation"))
                
                import time
                emails_sent = set()
                success_count = 0
                error_count = 0
                errors_detail = []
                
                for show in shows:
                    email = show.contact_email
                    if not email and show.user:
                        email = show.user.email if hasattr(show.user, 'email') else None
                    
                    if email and email not in emails_sent:
                        emails_sent.add(email)
                        body_html = _build_appel_offre_email(demande, show)
                        try:
                            msg = MailMessage(
                                subject=f"Nouvelle Opportunité - {demande.genre_recherche} à {demande.lieu_ville}",
                                recipients=[email]
                            )
                            msg.html = body_html
                            current_app.mail.send(msg)
                            success_count += 1
                            print(f"[DEBUG] ✅ Email envoyé à {email}")
                        except Exception as e:
                            error_count += 1
                            errors_detail.append(f"{email}: {str(e)[:100]}")
                            print(f"[MAIL] ❌ Erreur envoi à {email}: {e}")
                
                # Copie admin
                admin_email = current_user().email if current_user() and current_user().email else None
                if not admin_email:
                    admin_email = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                if admin_email:
                    try:
                        # Liste des compagnies contactées
                        cie_rows = ""
                        for show in shows:
                            s_email = show.contact_email or (show.user.email if show.user and hasattr(show.user, 'email') else "—")
                            cie_rows += f'<tr><td style="padding:6px 10px;border-bottom:1px solid #eee;">{show.title}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;">{show.category or "—"}</td><td style="padding:6px 10px;border-bottom:1px solid #eee;">{s_email}</td></tr>'
                        # Erreurs éventuelles
                        err_html = ""
                        if errors_detail:
                            err_html = '<div style="background:#fff3cd;padding:10px;border-radius:6px;margin:12px 0;"><strong>⚠️ Erreurs :</strong><ul style="margin:4px 0;">'
                            for ed in errors_detail[:10]:
                                err_html += f"<li>{ed}</li>"
                            err_html += "</ul></div>"

                        admin_body = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="font-family:Arial,sans-serif;max-width:650px;margin:0 auto;color:#333;">
<div style="text-align:center;margin:16px 0;"><img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Logo" style="max-width:180px;"></div>
<div style="background:#1b2a4e;color:#fff;padding:14px 20px;border-radius:8px 8px 0 0;text-align:center;font-weight:700;font-size:1.1em;">📋 COPIE ADMIN — Auto-matching envoyé à {success_count} compagnie(s)</div>
<div style="background:#f9f9f9;padding:18px;border-radius:0 0 8px 8px;">
<h3 style="margin:0 0 10px 0;color:#6a1b9a;">🎭 {demande.genre_recherche} à {demande.lieu_ville}</h3>
<table style="width:100%;font-size:0.9em;margin:8px 0;" cellpadding="0" cellspacing="0">
<tr><td style="padding:3px 0;"><strong>📝 Intitulé :</strong></td><td>{demande.intitule or 'Non précisé'}</td></tr>
<tr><td style="padding:3px 0;"><strong>📅 Dates :</strong></td><td>{demande.dates_horaires}</td></tr>
<tr><td style="padding:3px 0;"><strong>🏢 Structure :</strong></td><td>{demande.structure}</td></tr>
<tr><td style="padding:3px 0;"><strong>👤 Contact :</strong></td><td>{demande.nom} — {demande.telephone}</td></tr>
<tr><td style="padding:3px 0;"><strong>✉️ Email :</strong></td><td>{demande.contact_email}</td></tr>
<tr><td style="padding:3px 0;"><strong>👥 Jauge :</strong></td><td>{demande.jauge}</td></tr>
<tr><td style="padding:3px 0;"><strong>💰 Budget :</strong></td><td>{demande.budget}</td></tr>
<tr><td style="padding:3px 0;"><strong>👶 Public :</strong></td><td>{demande.age_range}</td></tr>
<tr><td style="padding:3px 0;"><strong>🏛️ Espace :</strong></td><td>{demande.type_espace}</td></tr>
<tr><td style="padding:3px 0;"><strong>📍 Région :</strong></td><td>{demande.region or '—'}</td></tr>
</table>
<h4 style="margin:16px 0 8px 0;color:#1b2a4e;">✅ {success_count} compagnie(s) contactée(s) :</h4>
<table style="width:100%;border-collapse:collapse;font-size:0.85em;background:#fff;border-radius:6px;">
<tr style="background:#e8eaf6;"><th style="padding:8px 10px;text-align:left;">Spectacle</th><th style="padding:8px 10px;text-align:left;">Catégorie</th><th style="padding:8px 10px;text-align:left;">Email</th></tr>
{cie_rows}
</table>
{err_html}
<p style="text-align:center;margin-top:16px;color:#888;font-size:0.85em;">Spectacle'ment Vôtre — contact@spectacleanimation.fr</p>
</div></body></html>"""
                        admin_msg = MailMessage(
                            subject=f"[ADMIN] Appel d'offre envoyé : {demande.genre_recherche} à {demande.lieu_ville} ({success_count} cie)",
                            recipients=[admin_email]
                        )
                        admin_msg.html = admin_body
                        current_app.mail.send(admin_msg)
                        # Copie de l'email artiste (tel que reçu par les compagnies)
                        if shows:
                            sample_show = shows[0]
                            artist_copy = MailMessage(
                                subject=f"[ADMIN COPIE ARTISTE] Nouvelle Opportunité - {demande.genre_recherche} à {demande.lieu_ville}",
                                recipients=[admin_email]
                            )
                            artist_copy.html = _build_appel_offre_email(demande, sample_show)
                            current_app.mail.send(artist_copy)
                    except Exception as e:
                        print(f"[MAIL] ⚠️ Erreur copie admin: {e}")

                if success_count > 0:
                    flash(f"✅ Appel d'offre envoyé à {success_count} compagnie(s) !", "success")
                if error_count > 0:
                    flash(f"⚠️ {error_count} email(s) en erreur.", "warning")
                if success_count == 0 and error_count == 0:
                    flash("⚠️ Aucun email à envoyer.", "warning")
                
                return redirect(url_for("admin_demandes_animation"))

            # === ACTION send_recap_only : envoi UNIQUEMENT du récap à l'organisateur ===
            # (rien n'est envoyé aux artistes — utile pour renvoyer la sélection après-coup)
            if action == "send_recap_only":
                selected_emails = request.form.getlist("emails[]")
                print(f"[DEBUG] send_recap_only : {len(selected_emails)} email(s) coché(s)")
                if not selected_emails:
                    flash("❌ Cochez au moins une fiche à inclure dans le récap.", "warning")
                    return redirect(request.url)
                # Récupérer les shows correspondant aux emails cochés
                # On accepte aussi bien show.contact_email que show.user.email
                from sqlalchemy import or_ as _or
                shows_recap = (
                    Show.query
                    .outerjoin(Show.user)
                    .filter(Show.approved.is_(True))
                    .filter(_or(
                        Show.contact_email.in_(selected_emails),
                        User.email.in_(selected_emails),
                    ))
                    .all()
                )
                print(f"[DEBUG] {len(shows_recap)} show(s) résolus pour le récap")
                if not shows_recap:
                    flash("⚠️ Aucune fiche valide trouvée pour les emails cochés.", "warning")
                    return redirect(url_for("admin_demandes_animation"))
                ok = _send_recap_to_organisateur(demande, shows_recap)
                if ok:
                    flash(f"📧 Récap envoyé à l'organisateur ({demande.contact_email}) avec {len(shows_recap)} fiche(s). Aucun mail aux artistes.", "success")
                else:
                    flash("⚠️ Le récap n'a pas pu être envoyé à l'organisateur (voir les logs).", "warning")
                return redirect(url_for("admin_demandes_animation"))

            # === ACTIONS preview / send : recherche manuelle par catégories ===
            categories = (request.form.getlist("cat_specialites")
                          + request.form.getlist("cat_evenements")
                          + request.form.getlist("cat_lieux")
                          + request.form.getlist("categories"))
            regions = request.form.getlist("regions")
            print(f"[DEBUG] Catégories sélectionnées: {categories}")
            print(f"[DEBUG] Régions sélectionnées: {regions}")
            
            if not categories:
                print("[DEBUG] Aucune catégorie sélectionnée")
                flash("Veuillez sélectionner au moins une spécialité, un événement ou un lieu.", "warning")
                return redirect(request.url)
            
            print(f"[DEBUG] Recherche des spectacles pour {len(categories)} catégories et {len(regions)} régions")
            # Récupérer tous les spectacles correspondants
            query = Show.query.filter(Show.approved.is_(True))
            
            if categories:
                # Recherche directe par valeur exacte (les valeurs viennent des checkboxes = mêmes que en DB)
                category_filters = []
                for cat in categories:
                    category_filters.extend([
                        Show.category.ilike(f"%{cat}%"),
                        Show.specialites.ilike(f"%{cat}%"),
                        Show.evenements.ilike(f"%{cat}%"),
                        Show.lieux_intervention.ilike(f"%{cat}%"),
                    ])
                query = query.filter(or_(*category_filters))
            
            # Filtrer par région si des régions sont sélectionnées
            if regions:
                # Filtrer sur la région du spectacle OU la région de l'utilisateur propriétaire
                from models.models import User as UserModel
                user_ids_in_region = db.session.query(UserModel.id).filter(
                    or_(*[UserModel.region.ilike(f"%{reg}%") for reg in regions])
                ).subquery()
                region_filters = []
                for reg in regions:
                    region_filters.append(Show.region.ilike(f"%{reg}%"))
                    region_filters.append(Show.regions_intervention.ilike(f"%{reg}%"))
                region_filters.append(Show.user_id.in_(user_ids_in_region))
                query = query.filter(or_(*region_filters))
            
            shows = query.all()
            
            print(f"[DEBUG] {len(shows)} spectacles trouvés")
            # Récupérer les emails uniques des utilisateurs
            emails_sent = set()
            success_count = 0
            error_count = 0
            errors_detail = []  # Liste des erreurs détaillées
            
            # Vérifier si mail est configuré
            if not getattr(current_app, "mail", None):
                print("[DEBUG ERREUR] Flask-Mail n'est pas configuré !")
                flash("❌ Erreur : le service email n'est pas configuré.", "danger")
                return redirect(url_for("admin_demandes_animation"))
            
            # Si des régions sont sélectionnées, ajouter aussi les utilisateurs directement
            # (ceux qui ont une région correspondante ET au moins un spectacle approuvé ET correspondant aux catégories)
            additional_users = []
            if regions:
                from models.models import User as UserModel
                user_region_filters = []
                for reg in regions:
                    user_region_filters.append(UserModel.region.ilike(f"%{reg}%"))
                # Filtrer aussi par catégorie pour ne cibler que les artistes pertinents
                additional_query = UserModel.query.join(Show).filter(
                    UserModel.email.isnot(None),
                    or_(*user_region_filters),
                    Show.approved.is_(True)
                )
                if categories:
                    cat_filters = []
                    for cat in categories:
                        cat_filters.extend([
                            Show.category.ilike(f"%{cat}%"),
                            Show.specialites.ilike(f"%{cat}%"),
                            Show.evenements.ilike(f"%{cat}%"),
                            Show.lieux_intervention.ilike(f"%{cat}%"),
                        ])
                    additional_query = additional_query.filter(or_(*cat_filters))
                additional_users = additional_query.distinct().all()
                print(f"[DEBUG] {len(additional_users)} utilisateurs supplémentaires avec région + catégorie correspondantes")
            
            # === SI ACTION = PREVIEW : Retourner liste des destinataires pour sélection manuelle ===
            if action == "preview":
                destinataires = []
                emails_seen = set()
                
                # Collecter les destinataires des spectacles
                for show in shows:
                    if regions and show.user and show.user.region:
                        user_region_match = any(reg.lower() in show.user.region.lower() for reg in regions)
                        show_region_match = show.region and any(reg.lower() in show.region.lower() for reg in regions)
                        if not user_region_match and not show_region_match:
                            continue
                    
                    email = show.contact_email
                    if not email and show.user:
                        email = show.user.email if hasattr(show.user, 'email') else None
                    
                    if email and email not in emails_seen:
                        emails_seen.add(email)
                        destinataires.append({
                            'email': email,
                            'show_title': f"{show.title} - {show.category}",
                            'category': show.category,
                            'region': show.region or (show.user.region if show.user else ""),
                            'show_id': show.id,
                            'type': 'spectacle'
                        })
                
                # Collecter les destinataires régionaux additionnels
                for user in additional_users:
                    if user.email and user.email not in emails_seen:
                        emails_seen.add(user.email)
                        destinataires.append({
                            'email': user.email,
                            'show_title': f"Région: {user.region}" if user.region else "Utilisateur régional",
                            'category': "Utilisateur régional",
                            'region': user.region or "",
                            'show_id': None,
                            'type': 'region'
                        })
                
                print(f"[DEBUG] {len(destinataires)} destinataires uniques trouvés pour prévisualisation")
                
                # Retourner le template de prévisualisation
                return render_template(
                    "admin_preview_destinataires.html",
                    user=current_user(),
                    demande=demande,
                    destinataires=destinataires,
                    categories=categories,
                    regions=regions
                )
            
            # === SINON (ACTION = SEND ou autre) : Continuer avec l'envoi normal ===
            # Filtrer par emails sélectionnés si fournis
            selected_emails = request.form.getlist("emails[]")
            if selected_emails:
                print(f"[DEBUG] Envoi limité à {len(selected_emails)} emails sélectionnés")
            
            # === PHASE 1 : COLLECTER TOUS LES EMAILS À ENVOYER ===
            import time
            emails_to_send = []  # Liste de tuples (email, body_html, show_title)
            
            print(f"[DEBUG] Phase 1 : Collecte des destinataires...")
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
                
                if email and email not in emails_sent and (not selected_emails or email in selected_emails):
                    emails_sent.add(email)
                    
                    # Préparer le HTML de l'email (sans l'envoyer tout de suite)
                    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .logo {{ text-align: center; margin: 20px 0; }}
        .logo img {{ max-width: 200px; height: auto; }}
        .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
        h2 {{ color: #1b2a4e; margin-top: 0; }}
        .opportunity-box {{ background: #e8f5e9; border: 1px solid #a5d6a7; color: #1b5e20; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .opportunity-box h3 {{ margin-top: 0; color: #1b5e20; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
        .info-item {{ background-color: rgba(255,255,255,0.6); padding: 10px; border-radius: 5px; }}
        .info-label {{ font-weight: bold; font-size: 0.9em; }}
        .contact-box {{ background-color: #fff; padding: 15px; border-left: 4px solid #2e7d32; margin: 15px 0; }}
        .show-info {{ background-color: #e8eaf6; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
        .btn {{ display: inline-block; padding: 12px 24px; background-color: #1b5e20; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="logo">
        <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre">
    </div>
    <div class="content">
        <h2>Nouvelle Opportunité à {demande.lieu_ville}</h2>
        <p>Bonjour,</p>
        <p>Bonne nouvelle ! Nous avons reçu une demande d'animation pour <strong>{demande.genre_recherche}</strong> qui correspond parfaitement à votre profil :</p>
        
        <div class="opportunity-box">
            <h3>📋 {demande.genre_recherche} à {demande.lieu_ville}</h3>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">📍 Lieu</div>
                    {demande.lieu_ville}
                </div>
                <div class="info-item">
                    <div class="info-label">📅 Date(s)</div>
                    {demande.dates_horaires}
                </div>
                <div class="info-item">
                    <div class="info-label">Type recherché</div>
                    {demande.genre_recherche}
                </div>
                <div class="info-item">
                    <div class="info-label">🎭 Spécialités</div>
                    {demande.specialites_recherchees.replace(',', ', ') if demande.specialites_recherchees else 'Non précisées'}
                </div>
                <div class="info-item">
                    <div class="info-label">👥 Jauge</div>
                    {demande.jauge}
                </div>
                <div class="info-item">
                    <div class="info-label">💰 Budget</div>
                    {demande.budget} €
                </div>
                <div class="info-item">
                    <div class="info-label">👶 Public</div>
                    {demande.age_range}
                </div>
            </div>
            <p><strong>🏢 Type d'espace :</strong> {demande.type_espace}</p>
            <p style="color: #333;"><strong>📝 Intitulé de la mission :</strong> {demande.intitule or 'Non précisé'}</p>
            <p><strong>♿ Accessibilité :</strong> {demande.accessibilite or 'Non précisée'}</p>
        </div>
        
        <div class="contact-box">
            <h3>📞 Coordonnées du demandeur</h3>
            <p><strong>Structure :</strong> {demande.structure}<br>
            <strong>Contact :</strong> {demande.nom}<br>
            <strong>Email :</strong> <a href="mailto:{demande.contact_email}" style="color: #1b5e20;">{demande.contact_email}</a><br>
            <strong>Téléphone :</strong> {demande.telephone}</p>
            <p style="text-align: center;">
                <a href="mailto:{demande.contact_email}" class="btn">✉️ Contacter le demandeur</a>
            </p>
            <p style="text-align: center; margin-top: 8px;">
                <a href="https://www.spectacleanimation.fr/demandes-animation" style="display:inline-block;padding:10px 24px;background:#1b5e20;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">👁️ Voir l'appel d'offre</a>
            </p>
        </div>
        
        <div class="show-info">
            <p><strong>✨ Votre spectacle concerné :</strong><br>
            {show.title} - {show.category}</p>
        </div>
        
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center;">
            <p><strong>Vous aussi, annoncez vos événements GRATUITEMENT !</strong><br>
            Publiez vos spectacles toute l'année sans limite de temps.<br>
            <a href="https://www.spectacleanimation.fr/submit" style="color: #1b5e20; font-weight: bold;">👉 Publier un spectacle</a></p>
        </div>
        
        <div style="background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%); color: white; padding: 20px; border-radius: 8px; margin: 15px 0; box-shadow: 0 4px 12px rgba(211,47,47,0.3);">
            <p style="margin: 0 0 10px 0; font-size: 1.1em;"><strong>💼 SPECTACLE'MENT VÔTRE VOUS ACCOMPAGNE</strong></p>
            <p style="margin: 0 0 15px 0; font-size: 0.95em;">Gestion administrative complète de votre compagnie : URSSAF, DSN, DUE, AEM, fiches de salaire, contrats de cession, déclarations sociales...</p>
            <p style="text-align: center; margin: 0;">
                <a href="https://spectacleanimation.fr/abonnement-compagnie" style="display: inline-block; background-color: white; color: #d32f2f; padding: 12px 28px; border-radius: 25px; text-decoration: none; font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">📋 Découvrir nos services</a>
            </p>
        </div>
        
        <div class="footer">
            <p><strong>L'équipe Spectacle'ment VØtre</strong><br>
            contact@spectacleanimation.fr</p>
        </div>
    </div>
</body>
</html>
"""
                    # Ajouter à la liste au lieu d'envoyer immédiatement
                    emails_to_send.append({
                        'email': email,
                        'body_html': body_html,
                        'show_title': f"{show.title} - {show.category}",
                        'type': 'spectacle',
                        'show': show
                    })
            
            # Collecter aussi les utilisateurs additionnels par région
            for user in additional_users:
                if user.email and user.email not in emails_sent and (not selected_emails or user.email in selected_emails):
                    emails_sent.add(user.email)
                    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .logo {{ text-align: center; margin: 20px 0; }}
        .logo img {{ max-width: 200px; height: auto; }}
        .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
        h2 {{ color: #1b2a4e; margin-top: 0; }}
        .opportunity-box {{ background: linear-gradient(135deg, #1b2a4e 0%, #355c7d 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .opportunity-box h3 {{ margin-top: 0; color: white; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
        .info-item {{ background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; }}
        .info-label {{ font-weight: bold; font-size: 0.9em; }}
        .contact-box {{ background-color: #fff; padding: 15px; border-left: 4px solid #1b2a4e; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
        .btn {{ display: inline-block; padding: 12px 24px; background-color: #1b2a4e; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="logo">
        <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre">
    </div>
    <div class="content">
        <h2>Nouvelle Opportunité à {demande.lieu_ville}</h2>
        <p>Bonjour,</p>
        <p>Nous avons reçu une demande d'animation pour <strong>{demande.genre_recherche}</strong> dans votre région qui pourrait vous intéresser :</p>
        
        <div class="opportunity-box">
            <h3>📋 {demande.genre_recherche} à {demande.lieu_ville}</h3>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">📍 Lieu</div>
                    {demande.lieu_ville}
                </div>
                <div class="info-item">
                    <div class="info-label">📅 Date(s)</div>
                    {demande.dates_horaires}
                </div>
                <div class="info-item">
                    <div class="info-label">Type recherché</div>
                    {demande.genre_recherche}
                </div>
                <div class="info-item">
                    <div class="info-label">🎭 Spécialités</div>
                    {demande.specialites_recherchees.replace(',', ', ') if demande.specialites_recherchees else 'Non précisées'}
                </div>
                <div class="info-item">
                    <div class="info-label">👥 Jauge</div>
                    {demande.jauge}
                </div>
                <div class="info-item">
                    <div class="info-label">💰 Budget</div>
                    {demande.budget} €
                </div>
                <div class="info-item">
                    <div class="info-label">👶 Public</div>
                    {demande.age_range}
                </div>
            </div>
            <p><strong>🏢 Type d'espace :</strong> {demande.type_espace}</p>
            <p style="color: #333;"><strong>📝 Intitulé de la mission :</strong> {demande.intitule or 'Non précisé'}</p>
            <p><strong>♿ Accessibilité :</strong> {demande.accessibilite or 'Non précisée'}</p>
        </div>
        
        <div class="contact-box">
            <h3>📞 Coordonnées du demandeur</h3>
            <p><strong>Structure :</strong> {demande.structure}<br>
            <strong>Contact :</strong> {demande.nom}<br>
            <strong>Email :</strong> <a href="mailto:{demande.contact_email}" style="color: #1b2a4e;">{demande.contact_email}</a><br>
            <strong>Téléphone :</strong> {demande.telephone}</p>
            <p style="text-align: center;">
                <a href="mailto:{demande.contact_email}" class="btn">✉️ Contacter le demandeur</a>
            </p>
            <p style="text-align: center; margin-top: 8px;">
                <a href="https://www.spectacleanimation.fr/demandes-animation" style="display:inline-block;padding:10px 24px;background:#1b5e20;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">👁️ Voir l'appel d'offre</a>
            </p>
        </div>
        
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center;">
            <p><strong>Vous aussi, annoncez vos événements GRATUITEMENT !</strong><br>
            Publiez vos spectacles toute l'année sans limite de temps.<br>
            <a href="https://www.spectacleanimation.fr/submit" style="color: #1b2a4e; font-weight: bold;">👉 Publier un spectacle</a></p>
        </div>
        
        <div style="background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%); color: white; padding: 20px; border-radius: 8px; margin: 15px 0; box-shadow: 0 4px 12px rgba(211,47,47,0.3);">
            <p style="margin: 0 0 10px 0; font-size: 1.1em;"><strong>💼 SPECTACLE'MENT VÔTRE VOUS ACCOMPAGNE</strong></p>
            <p style="margin: 0 0 15px 0; font-size: 0.95em;">Gestion administrative complète de votre compagnie : URSSAF, DSN, DUE, AEM, fiches de salaire, contrats de cession, déclarations sociales...</p>
            <p style="text-align: center; margin: 0;">
                <a href="https://spectacleanimation.fr/abonnement-compagnie" style="display: inline-block; background-color: white; color: #d32f2f; padding: 12px 28px; border-radius: 25px; text-decoration: none; font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">📋 Découvrir nos services</a>
            </p>
        </div>
        
        <div class="footer">
            <p><strong>L'équipe Spectacle'ment VØtre</strong><br>
            contact@spectacleanimation.fr</p>
        </div>
    </div>
</body>
</html>
"""
                    # Ajouter à la liste
                    emails_to_send.append({
                        'email': user.email,
                        'body_html': body_html,
                        'show_title': f"Région: {user.region}" if user.region else "Utilisateur régional",
                        'type': 'region'
                    })
            
            print(f"[DEBUG] Phase 1 terminée : {len(emails_to_send)} emails à envoyer")
            
            # === PHASE 2 : ENVOI PAR BATCH AVEC PROGRESSION ===
            BATCH_SIZE = 20  # Nombre d'emails par batch
            PAUSE_SECONDS = 2  # Pause entre les batchs
            
            success_count = 0
            error_count = 0
            errors_detail = []
            
            total_emails = len(emails_to_send)
            if total_emails == 0:
                flash("⚠️ Aucun email à envoyer. Aucun spectacle correspondant trouvé.", "warning")
                return redirect(url_for("admin_demandes_animation"))
            
            print(f"[DEBUG] Phase 2 : Envoi par batchs de {BATCH_SIZE} emails...")
            
            # Découper en batchs
            for i in range(0, total_emails, BATCH_SIZE):
                batch = emails_to_send[i:i+BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                total_batchs = (total_emails + BATCH_SIZE - 1) // BATCH_SIZE
                
                print(f"[BATCH {batch_num}/{total_batchs}] Envoi de {len(batch)} emails...")
                
                for email_data in batch:
                    try:
                        msg = MailMessage(
                            subject=f"Nouvelle Opportunité - {demande.genre_recherche} à {demande.lieu_ville}",
                            recipients=[email_data['email']]
                        )
                        msg.html = email_data['body_html']
                        current_app.mail.send(msg)
                        success_count += 1
                        print(f"[DEBUG] ✅ Email envoyé à {email_data['email']} ({success_count}/{total_emails})")
                    except Exception as e:
                        error_msg = str(e)
                        error_count += 1
                        errors_detail.append(f"{email_data['email']}: {error_msg[:100]}")
                        print(f"[MAIL] ❌ Erreur envoi à {email_data['email']}: {error_msg}")
                
                # Pause entre les batchs (sauf pour le dernier)
                if i + BATCH_SIZE < total_emails:
                    print(f"[BATCH] Pause de {PAUSE_SECONDS}s avant le prochain batch...")
                    time.sleep(PAUSE_SECONDS)
            
            # === PHASE 3 : ENVOYER COPIE ADMIN ===
            # L'admin reçoit TOUJOURS une copie récapitulative, même si son email était dans les destinataires
            admin_email = current_user().email if current_user() and current_user().email else None
            if not admin_email:
                admin_email = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
            if admin_email:
                try:
                    admin_body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .logo {{ text-align: center; margin: 20px 0; }}
        .logo img {{ max-width: 200px; height: auto; }}
        .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 8px; }}
        h2 {{ color: #1b2a4e; margin-top: 0; }}
        .admin-notice {{ background: linear-gradient(135deg, #1b2a4e 0%, #355c7d 100%); color: white; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; font-weight: bold; }}
        .opportunity-box {{ background: #e8f5e9; border: 1px solid #a5d6a7; color: #1b5e20; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .opportunity-box h3 {{ margin-top: 0; color: white; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
        .info-item {{ background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; }}
        .info-label {{ font-weight: bold; font-size: 0.9em; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="logo">
        <img src="https://www.spectacleanimation.fr/static/img/logo_spectaclement_votre.png" alt="Spectacle'ment Vôtre">
    </div>
    <div class="content">
        <div class="admin-notice">
            📋 COPIE ADMIN - Appel d'offre envoyé à {success_count} compagnie(s)
        </div>
        <p style="font-size:0.95em; color:#444; margin:0 0 16px 0;"><strong>Appel d'offre :</strong> {demande.intitule or 'Demande d\'animation'}</p>
        
        <div class="opportunity-box">
            <h3>📋 {demande.genre_recherche} à {demande.lieu_ville}</h3>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">📍 Lieu</div>
                    {demande.lieu_ville}
                </div>
                <div class="info-item">
                    <div class="info-label">📅 Date(s)</div>
                    {demande.dates_horaires}
                </div>
                <div class="info-item">
                    <div class="info-label">Type recherché</div>
                    {demande.genre_recherche}
                </div>
                <div class="info-item">
                    <div class="info-label">🎭 Spécialités</div>
                    {demande.specialites_recherchees.replace(',', ', ') if demande.specialites_recherchees else 'Non précisées'}
                </div>
                <div class="info-item">
                    <div class="info-label">👥 Jauge</div>
                    {demande.jauge}
                </div>
                <div class="info-item">
                    <div class="info-label">💰 Budget</div>
                    {demande.budget} €
                </div>
                <div class="info-item">
                    <div class="info-label">👶 Public</div>
                    {demande.age_range}
                </div>
            </div>
            <p><strong>🏢 Type d'espace :</strong> {demande.type_espace}</p>
            <p style="color: #333;"><strong>📝 Intitulé de la mission :</strong> {demande.intitule or 'Non précisé'}</p>
            <p><strong>♿ Accessibilité :</strong> {demande.accessibilite or 'Non précisée'}</p>
        </div>
        
        <p><strong>Structure :</strong> {demande.structure}<br>
        <strong>Contact :</strong> {demande.nom}<br>
        <strong>Email :</strong> {demande.contact_email}<br>
        <strong>Téléphone :</strong> {demande.telephone}</p>
        
        <div class="footer">
            <p><strong>L'équipe Spectacle'ment Vôtre</strong></p>
        </div>
    </div>
</body>
</html>
"""
                    admin_msg = MailMessage(
                        subject=f"[ADMIN] Appel d'offre envoyé : {demande.genre_recherche} à {demande.lieu_ville}",
                        recipients=[admin_email]
                    )
                    admin_msg.html = admin_body_html
                    current_app.mail.send(admin_msg)
                    print(f"[DEBUG] ✅ Copie admin envoyée à {admin_email}")
                except Exception as e:
                    print(f"[MAIL] ⚠️ Erreur envoi copie admin à {admin_email}: {e}")
            else:
                print(f"[WARNING] Aucun email admin configuré - pas de copie envoyée")

            # === RÉCAP ORGANISATEUR ===
            # Envoi auto d'un récap court à l'organisateur avec les liens des fiches contactées
            if success_count > 0:
                shows_recap = [e['show'] for e in emails_to_send if e.get('type') == 'spectacle' and e.get('show')]
                _send_recap_to_organisateur(demande, shows_recap)

            print(f"[DEBUG] Envoi terminé - Succès: {success_count}, Erreurs: {error_count}")
            if success_count > 0:
                copie_msg = f" + copie admin envoyée à {admin_email}" if admin_email else ""
                flash(f"✅ Demande envoyée à {success_count} utilisateur(s){copie_msg} !", "success")
            if error_count > 0:
                flash(f"⚠️ {error_count} email(s) n'ont pas pu être envoyé(s) (domaines invalides ou boîtes pleines).", "warning")
                # Logger les détails des erreurs sans crasher
                for err_detail in errors_detail[:5]:  # Limiter à 5 pour ne pas surcharger les logs
                    print(f"[MAIL ERROR DETAIL] {err_detail}")
            
            if success_count == 0 and error_count == 0:
                flash("⚠️ Aucun email n'a été envoyé. Aucun spectacle correspondant trouvé.", "warning")
            
            # Retourner à la page admin des demandes
            return redirect(url_for("admin_demandes_animation"))
        
        # GET : afficher le formulaire de sélection
        # Auto-matching basé sur les nouveaux champs
        from utils.matching import find_matching_shows
        all_approved = Show.query.filter(Show.approved.is_(True)).all()
        matched = find_matching_shows(demande, all_approved, min_score=10)

        # Pré-sélection automatique basée sur les critères de la demande
        pre_specialites = [s.strip() for s in (demande.specialites_recherchees or "").split(",") if s.strip()]
        pre_evenements = [e.strip() for e in (demande.evenements_contexte or "").split(",") if e.strip()]
        pre_lieux = [l.strip() for l in (demande.lieux_souhaites or "").split(",") if l.strip()]
        pre_regions = [demande.region] if demande.region else []

        return render_template(
            "admin_envoyer_demande.html", 
            demande=demande, 
            specialites_data=SPECIALITES,
            evenements_data=EVENEMENTS,
            lieux_data=LIEUX,
            regions_list=REGIONS_FRANCE,
            pre_specialites=pre_specialites,
            pre_evenements=pre_evenements,
            pre_lieux=pre_lieux,
            pre_regions=pre_regions,
            matched_shows=matched,
            user=current_user()
        )

    # ----------------------------
    # Routes SEO pour les villes
    # ----------------------------
    @app.route("/spectacles-<city_slug>")
    def city_spectacles(city_slug):
            """Page SEO dédiée pour chaque ville française avec spectacles locaux"""
            # Récupérer les données de la ville
            city = get_city_by_slug(city_slug)
            
            # 404 si la ville n'existe pas dans notre liste
            if not city:
                abort(404)
            
            # Récupérer les filtres optionnels
            category = request.args.get("category", "", type=str).strip()
            public_categorie = request.args.get("public_categorie", "", type=str).strip()
            page = request.args.get("page", 1, type=int)
            
            # Construire la requête de base (spectacles approuvés uniquement)
            shows = Show.query.filter(Show.approved == True)
            
            # Filtrer par ville (on cherche dans location et region)
            # La colonne location peut contenir plusieurs villes séparées par des virgules
            city_name = city['name']
            shows = shows.filter(
                or_(
                    Show.location.ilike(f"%{city_name}%"),
                    Show.region.ilike(f"%{city['region']}%")
                )
            )
            
            # Filtrer par catégorie si spécifiée
            if category:
                shows = shows.filter(Show.category.ilike(f"%{category}%"))
            
            # Filtrer par catégorie de Public Cible v2 (CSV stricte)
            if public_categorie:
                c = public_categorie
                shows = shows.filter(
                    Show.public_categories.isnot(None),
                    Show.public_categories != "",
                    or_(
                        Show.public_categories == c,
                        Show.public_categories.ilike(f"{c},%"),
                        Show.public_categories.ilike(f"%,{c}"),
                        Show.public_categories.ilike(f"%,{c},%"),
                    )
                )
            
            # Trier par ordre d'affichage puis date
            shows = shows.order_by(Show.display_order.asc(), Show.created_at.desc())
            
            # Pagination (12 spectacles par page)
            per_page = 12
            shows_paginated = shows.paginate(page=page, per_page=per_page, error_out=False)
            
            # Compter le nombre de spectacles pour cette ville
            total_shows = shows.count()
            
            # Générer les méta-données SEO
            meta_title = f"Spectacles à {city_name} ({city['department']}) - Artistes et Compagnies"
            meta_description = f"Découvrez {total_shows} spectacles, animations et artistes disponibles à {city_name} en {city['region']}. Théâtre, cirque, magie, clown, concerts pour tous les âges."
            
            # Mots-clés SEO pour cette ville
            meta_keywords = f"spectacle {city_name.lower()}, animation {city_name.lower()}, artiste {city_name.lower()}, compagnie {city_name.lower()}, théâtre {city_name.lower()}, cirque {city_name.lower()}, {city['region'].lower()}"
            
            return render_template(
                "city_spectacles.html",
                user=current_user(),
                city=city,
                shows=shows_paginated.items,
                pagination=shows_paginated,
                total_shows=total_shows,
                category=category,
                public_categorie=public_categorie,
                meta_title=meta_title,
                meta_description=meta_description,
                meta_keywords=meta_keywords,
                neighbor_cities=get_neighbor_cities(city),
                city_seo=get_city_seo_data(city),
                seo_top_categories=SEO_TOP_CATEGORIES,
                seo_category_labels=SEO_CATEGORY_LABELS,
            )

    # ----------------------------
    # Routes SEO par catégorie
    # ----------------------------
    @app.get("/<category_slug>/")
    def seo_category(category_slug):
        if category_slug not in SEO_CATEGORIES:
            abort(404)
        return redirect(url_for("catalogue", specialite=SEO_CATEGORIES[category_slug]), code=301)

    # Catégories SEO avec labels lisibles pour les pages ville×catégorie
    SEO_CATEGORY_LABELS = {
        "marionnette": "Marionnettes",
        "magie": "Magie",
        "clown": "Clowns",
        "theatre": "Théâtre",
        "danse": "Danse",
        "spectacle-enfant": "Spectacles Enfants",
        "enfant": "Spectacles Enfants",
        "atelier": "Ateliers",
        "concert": "Concerts",
        "cirque": "Cirque",
        "spectacle-de-rue": "Spectacles de Rue",
        "orchestre": "Orchestre",
        "arbre-de-noel": "Arbres de Noël",
        "animation-ecole": "Animations École",
        # Nouveaux thèmes longue traîne
        "conte": "Contes",
        "conteur": "Conteurs",
        "mentaliste": "Mentalistes",
        "humoriste": "Humoristes",
        "ventriloque": "Ventriloques",
        "mascotte": "Mascottes",
        "pere-noel": "Pères Noël",
        "echassier": "Échassiers",
        "sculpteur-ballons": "Sculpteurs sur Ballons",
        "caricaturiste": "Caricaturistes",
        "maquillage": "Maquillage Enfant",
        "one-man-show": "One-Man-Shows",
        "comedie-musicale": "Comédies Musicales",
        "chorale-gospel": "Chorales & Gospel",
        "fanfare": "Fanfares & Batucadas",
        "dj-orchestre": "DJ & Orchestres",
        "jazz": "Jazz",
        "musique-classique": "Musique Classique",
        "chanson-francaise": "Chanson Française",
        "spectacle-medieval": "Spectacles Médiévaux",
        "spectacle-animalier": "Spectacles Animaliers",
        "cabaret": "Cabaret",
        "fete-de-village": "Fêtes de Village",
    }

    # Top catégories pour les pages ville×catégorie (les plus recherchées)
    SEO_TOP_CATEGORIES = [
        "magie", "marionnette", "clown", "theatre", "cirque",
        "spectacle-enfant", "arbre-de-noel", "animation-ecole",
        "conte", "mentaliste", "humoriste", "mascotte",
        "pere-noel", "sculpteur-ballons", "maquillage",
        "dj-orchestre", "chorale-gospel", "jazz",
    ]

    @app.get("/<category_slug>/<city_slug>/")
    def seo_category_city(category_slug, city_slug):
        """Page SEO ville×catégorie avec contenu unique pour la longue traîne"""
        if category_slug not in SEO_CATEGORIES:
            abort(404)
        
        city = get_city_by_slug(city_slug)
        if not city:
            # Fallback : rediriger vers catalogue si ville inconnue
            return redirect(
                url_for("catalogue", category=SEO_CATEGORIES[category_slug], location=city_slug),
                code=301
            )
        
        category_filter = SEO_CATEGORIES[category_slug]
        category_label = SEO_CATEGORY_LABELS.get(category_slug, category_slug.replace("-", " ").title())
        city_name = city['name']
        
        # Requête des spectacles
        shows = Show.query.filter(
            Show.approved == True,
            Show.category.ilike(f"%{category_filter}%"),
            or_(
                Show.location.ilike(f"%{city_name}%"),
                Show.region.ilike(f"%{city['region']}%")
            )
        ).order_by(Show.display_order.asc(), Show.created_at.desc())
        
        page = request.args.get("page", 1, type=int)
        pagination = shows.paginate(page=page, per_page=12, error_out=False)
        total_shows = shows.count()
        
        # Meta SEO longue traîne
        meta_title = f"{category_label} à {city_name} ({city['department']}) - Artistes Professionnels"
        meta_description = (
            f"Trouvez {total_shows} spectacles de {category_label.lower()} à {city_name} "
            f"en {city['region']}. Artistes professionnels pour écoles, mairies, CSE et "
            f"particuliers. Devis gratuit sous 3h."
        )
        meta_keywords = (
            f"{category_label.lower()} {city_name.lower()}, "
            f"spectacle {category_label.lower()} {city_name.lower()}, "
            f"artiste {category_label.lower()} {city['region'].lower()}, "
            f"{category_label.lower()} {city['department']}"
        )
        
        return render_template(
            "city_category.html",
            user=current_user(),
            city=city,
            category_slug=category_slug,
            category_label=category_label,
            shows=pagination.items,
            pagination=pagination,
            total_shows=total_shows,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            seo_top_categories=SEO_TOP_CATEGORIES,
            seo_category_labels=SEO_CATEGORY_LABELS,
            neighbor_cities=get_neighbor_cities(city),
            city_seo=get_city_seo_data(city),
            category_seo=get_category_seo_data(category_slug),
        )


# -----------------------------------------------------
# Entrée
# -----------------------------------------------------

print("🏗️  Création de l'application Flask...")
app = create_app()
print("✅ Application Flask créée avec succès!")
print(f"   App name: {app.name}")
print(f"   Debug: {app.debug}")
print("=" * 70)

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

# === GESTION DES UTILISATEURS ===
@app.route("/admin/delete-bots", methods=["POST"])
@login_required
@admin_required
def admin_delete_bots():
    """Supprime en masse les faux comptes bots (téléphone +1-, 0 spectacle, non admin)."""
    bots = User.query.filter(
        User.is_admin == False,
        User.telephone.like("+1-%")
    ).all()
    count = 0
    for user in bots:
        nb_shows = len(user.shows) if hasattr(user, 'shows') else 0
        if nb_shows == 0:
            db.session.delete(user)
            count += 1
    db.session.commit()
    flash(f"✅ {count} faux compte(s) supprimé(s).", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    """Affiche la liste de tous les utilisateurs pour gestion admin."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users)

@app.route("/admin/users/<int:user_id>/localisation", methods=["POST"])
@login_required
@admin_required
def admin_update_user_localisation(user_id):
    """Met a jour CP / ville / region d'un utilisateur (utilise pour le matching geographique)."""
    user = User.query.get_or_404(user_id)
    cp = (request.form.get("code_postal", "") or "").strip()
    ville = (request.form.get("ville", "") or "").strip()
    region = fix_mojibake((request.form.get("region", "") or "").strip())
    try:
        user.code_postal = cp or None
        user.ville = ville or None
        user.region = region or None
        db.session.commit()
        flash(f"Localisation de « {user.username} » mise a jour.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur : {e}", "danger")
        current_app.logger.error(f"[ADMIN] Erreur maj localisation user {user_id}: {e}")
    next_url = request.form.get("next") or request.referrer
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("admin_users"))

@app.route("/admin/shows/<int:show_id>/reassign", methods=["POST"])
@login_required
@admin_required
def admin_reassign_show(show_id):
    """Reattribue un spectacle a un utilisateur (notamment quand user_id IS NULL)."""
    from models.models import Show
    show = Show.query.get_or_404(show_id)
    new_user_id = request.form.get("new_user_id", "").strip()
    if not new_user_id or not new_user_id.isdigit():
        flash("Utilisateur invalide.", "danger")
        return redirect(request.referrer or url_for("admin_dashboard"))
    new_user = User.query.get(int(new_user_id))
    if not new_user:
        flash("Utilisateur introuvable.", "danger")
        return redirect(request.referrer or url_for("admin_dashboard"))
    try:
        show.user_id = new_user.id
        db.session.commit()
        flash(f"Spectacle « {show.title} » rattache a « {new_user.username} ».", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur : {e}", "danger")
        current_app.logger.error(f"[ADMIN] Erreur reassign show {show_id}: {e}")
    next_url = request.form.get("next") or request.referrer
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/shows/<int:show_id>/localisation", methods=["POST"])
@login_required
@admin_required
def admin_update_show_localisation(show_id):
    """Met a jour la localisation d'un spectacle (utile pour les spectacles orphelins
    sans user_id, afin que le matching geographique fonctionne quand meme).
    Met a jour show.location (ville) et show.region.
    """
    from models.models import Show
    show = Show.query.get_or_404(show_id)
    ville = (request.form.get("ville", "") or "").strip()
    region = fix_mojibake((request.form.get("region", "") or "").strip())
    try:
        if ville:
            show.location = ville
        if region:
            show.region = region
        db.session.commit()
        flash(f"Localisation du spectacle « {show.title} » mise a jour.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur : {e}", "danger")
        current_app.logger.error(f"[ADMIN] Erreur maj localisation show {show_id}: {e}")
    next_url = request.form.get("next") or request.referrer
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Suppression d'utilisateur avec préavis 7j si inactif.

    Comportement :
    - Compte avec au moins 1 spectacle approuvé → suppression immédiate (sans email).
    - Compte sans spectacle approuvé, jamais prévenu → mail de préavis + date enregistrée (J+7).
    - Compte sans spectacle approuvé, déjà en préavis (date dépassée OU forcer=1) → suppression définitive + mail final.
    """
    from datetime import timedelta
    user = User.query.get_or_404(user_id)

    # Empêcher la suppression d'un admin
    if user.is_admin:
        flash("Impossible de supprimer un compte administrateur.", "danger")
        return redirect(url_for("admin_users"))

    # Empêcher l'auto-suppression
    if user.id == current_user().id:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for("admin_users"))

    username = user.username
    user_email = user.email
    nb_shows = len(user.shows) if hasattr(user, 'shows') else 0
    nb_approved = sum(1 for s in user.shows if getattr(s, 'approved', False)) if hasattr(user, 'shows') else 0
    forcer = request.form.get("forcer") == "1"
    pending = getattr(user, 'pending_deletion_at', None)

    # ─── CAS 1 : compte inactif jamais prévenu → enregistrer préavis + mail ───
    if nb_approved == 0 and not pending and not forcer:
        try:
            user.pending_deletion_at = datetime.utcnow() + timedelta(days=7)
            db.session.commit()
            current_app.logger.info(f"[ADMIN] Préavis 7j posé sur {username} (ID: {user_id}) par {current_user().username}")
            if user_email and getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
                deadline_str = user.pending_deletion_at.strftime('%d/%m/%Y')
                body_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#ff9800,#f57c00);color:#fff;padding:24px;text-align:center;">
      <h2 style="margin:0;">⏳ Préavis de suppression</h2>
    </div>
    <div style="padding:28px;color:#333;line-height:1.6;">
      <p>Bonjour <strong>{username}</strong>,</p>
      <p>Nous avons remarqué qu'<strong>aucun spectacle n'a encore été publié</strong> sur votre compte Spectacle'ment VØtre.</p>
      <p>Sans publication de votre part, votre compte sera <strong>automatiquement supprimé le {deadline_str}</strong> (dans 7 jours).</p>
      <div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="margin:0;"><strong>✅ Comment conserver votre compte ?</strong></p>
        <p style="margin:8px 0 0 0;">Connectez-vous et publiez votre premier spectacle. C'est <strong>gratuit</strong> et cela prend quelques minutes.</p>
        <p style="text-align:center;margin:16px 0 0 0;">
          <a href="https://www.spectacleanimation.fr/login" style="display:inline-block;padding:12px 26px;background:#1b5e20;color:#fff;text-decoration:none;border-radius:6px;font-weight:700;">👉 Me connecter et publier</a>
        </p>
      </div>
      <div style="background:#f3e5f5;border-left:4px solid #6a1b9a;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="margin:0 0 8px 0;"><strong>💚 Pourquoi c'est gratuit ?</strong></p>
        <p style="margin:0 0 8px 0;font-size:14px;line-height:1.6;">Spectacle'ment VØtre fonctionne comme un <strong>annuaire national de référence</strong> : plus il y a de spectacles publiés, plus les <strong>mairies, écoles, CSE, agences et organisateurs</strong> prennent l'habitude d'y chercher leurs animations &mdash; et d'y déposer leurs <strong>appels d'offres</strong>.</p>
        <p style="margin:0 0 8px 0;font-size:14px;line-height:1.6;">📍 <strong>Au niveau local</strong>, votre département gagne en visibilité à mesure que des compagnies de la région s'y inscrivent : les acteurs culturels de chez vous tombent alors sur <strong>votre profil en priorité</strong>.</p>
        <p style="margin:0 0 8px 0;font-size:14px;line-height:1.6;">🇫🇷 <strong>Au niveau national</strong>, vous recevrez aussi <strong>gratuitement</strong> des appels d'offres venant de <strong>toute la France</strong> &mdash; un complément précieux à votre démarche commerciale régionale, qui vous ouvre des dates et des territoires que vous n'auriez pas prospectés seul.</p>
        <p style="margin:0 0 8px 0;font-size:14px;line-height:1.6;">C'est cette dynamique collective qui nous permet de maintenir la plateforme <strong>100 % gratuite</strong> pour les compagnies.</p>
        <p style="margin:0;font-size:13px;color:#555;font-style:italic;line-height:1.6;">C'est en accompagnant les compagnies qui le souhaitent sur le volet administratif (URSSAF, DSN, contrats de cession…) que nous pérennisons ce modèle.</p>
      </div>
      <p style="font-size:0.9em;color:#666;">Si vous publiez un spectacle avant cette date, votre compte sera conservé automatiquement.</p>
      <p style="margin-top:24px;">Cordialement,<br><strong>L'équipe Spectacle'ment VØtre</strong><br>contact@spectacleanimation.fr</p>
    </div>
  </div>
</body></html>"""
                try:
                    msg = MailMessage(subject="⏳ Votre compte Spectacle'ment VØtre sera supprimé dans 7 jours", recipients=[user_email])  # type: ignore[arg-type]
                    msg.html = body_html  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                    current_app.logger.info(f"[MAIL] ✓ Préavis 7j envoyé à {user_email}")
                except Exception as e:
                    current_app.logger.error(f"[MAIL] ✗ Préavis 7j non envoyé: {e}")
            flash(f"⏳ Préavis de 7 jours posé sur « {username} ». Suppression automatique le {user.pending_deletion_at.strftime('%d/%m/%Y')} si aucun spectacle n'est publié.", "warning")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Erreur préavis : {str(e)}", "danger")
            current_app.logger.error(f"[ADMIN] Erreur préavis user {user_id}: {e}")
        return redirect(url_for("admin_users"))

    # ─── CAS 2 : compte avec spectacles publiés OU déjà en préavis OU forcer ───
    # → suppression immédiate
    send_inactivity_email = (nb_approved == 0) and bool(user_email)

    try:
        # Supprimer les enregistrements liés à chaque spectacle
        from models.models import ShowView, Review, Conversation, Message, Notification
        if hasattr(user, 'shows'):
            for show in user.shows:
                ShowView.query.filter_by(show_id=show.id).delete()
                Review.query.filter_by(show_id=show.id).delete()
                for conv in Conversation.query.filter_by(show_id=show.id).all():
                    Message.query.filter_by(conversation_id=conv.id).delete()
                    db.session.delete(conv)
                db.session.delete(show)
        # Supprimer conversations/messages/notifications de l'utilisateur
        for conv in Conversation.query.filter((Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)).all():
            Message.query.filter_by(conversation_id=conv.id).delete()
            db.session.delete(conv)
        Notification.query.filter_by(user_id=user.id).delete()
        Review.query.filter_by(user_id=user.id).delete()

        # Supprimer l'utilisateur
        db.session.delete(user)
        db.session.commit()

        flash(f"✅ L'utilisateur « {username} » et ses {nb_shows} spectacle(s) ont été supprimés.", "success")
        current_app.logger.info(f"[ADMIN] Utilisateur {username} (ID: {user_id}) supprimé par {current_user().username}")

        # ── Email final de suppression pour inactivité ──
        if send_inactivity_email:
            try:
                if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
                    body_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#7c4dff,#536dfe);color:#fff;padding:24px;text-align:center;">
      <h2 style="margin:0;">Spectacle'ment VØtre</h2>
    </div>
    <div style="padding:28px;color:#333;line-height:1.6;">
      <p>Bonjour <strong>{username}</strong>,</p>
      <p>Nous vous informons que votre compte sur <strong>Spectacle'ment VØtre</strong> a été <strong>supprimé pour inactivité</strong>.</p>
      <p>Aucun spectacle n'avait été publié sur votre compte. Pour conserver une plateforme à jour pour les organisateurs (mairies, écoles, CSE…), nous faisons régulièrement le ménage des comptes restés sans spectacle approuvé.</p>
      <div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="margin:0;"><strong>💡 Vous souhaitez revenir ?</strong></p>
        <p style="margin:8px 0 0 0;">L'inscription est toujours <strong>100 % gratuite</strong>. Vous pouvez recréer un compte et publier votre premier spectacle en quelques minutes :</p>
        <p style="text-align:center;margin:16px 0 0 0;">
          <a href="https://www.spectacleanimation.fr/register" style="display:inline-block;padding:12px 26px;background:#1b5e20;color:#fff;text-decoration:none;border-radius:6px;font-weight:700;">👉 Créer un nouveau compte</a>
        </p>
      </div>
      <p>Merci de l'intérêt que vous avez porté à notre plateforme.</p>
      <p style="margin-top:24px;">À très bientôt peut-être,<br><strong>L'équipe Spectacle'ment VØtre</strong><br>contact@spectacleanimation.fr</p>
    </div>
  </div>
</body></html>"""
                    msg = MailMessage(subject="Suppression de votre compte Spectacle'ment VØtre (inactivité)", recipients=[user_email])  # type: ignore[arg-type]
                    msg.html = body_html  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                    current_app.logger.info(f"[MAIL] ✓ Email suppression inactivité envoyé à {user_email}")
            except Exception as e:
                current_app.logger.error(f"[MAIL] ✗ Envoi email suppression inactivité impossible: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Erreur lors de la suppression : {str(e)}", "danger")
        current_app.logger.error(f"[ADMIN] Erreur suppression utilisateur {user_id}: {e}")

    return redirect(url_for("admin_users"))


@app.route("/admin/cancel-deletion/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def admin_cancel_deletion(user_id):
    """Annule manuellement le préavis de suppression d'un utilisateur."""
    user = User.query.get_or_404(user_id)
    if getattr(user, 'pending_deletion_at', None):
        user.pending_deletion_at = None
        db.session.commit()
        flash(f"✅ Préavis de suppression annulé pour « {user.username} ».", "success")
        current_app.logger.info(f"[ADMIN] Préavis annulé pour {user.username} par {current_user().username}")
    return redirect(url_for("admin_users"))

# === SUPPRESSION DE PHOTO INDIVIDUELLE ===
@app.route("/admin/shows/<int:show_id>/delete-photo/<photo_field>", methods=["POST"])
@login_required
def admin_delete_photo(show_id, photo_field):
    """Supprime une photo spécifique d'un spectacle (file_name, file_name2 ou file_name3).
    Accessible aux admins ET aux propriétaires du spectacle."""
    show = Show.query.get_or_404(show_id)
    user = current_user()
    
    # Vérifier que l'utilisateur a le droit de supprimer (admin OU propriétaire)
    if not user.is_admin and show.user_id != user.id:
        flash("❌ Vous n'avez pas la permission de modifier ce spectacle.", "danger")
        return redirect(url_for("home"))
    
    # Valider que photo_field est bien autorisé
    if photo_field not in ['file_name', 'file_name2', 'file_name3']:
        flash("❌ Champ de photo invalide.", "danger")
        # Rediriger selon le contexte
        if user.is_admin:
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("show_edit_self", show_id=show_id))
    
    # Récupérer le nom du fichier à supprimer
    file_to_delete = getattr(show, photo_field, None)
    
    if file_to_delete:
        try:
            # Supprimer le fichier du système (si stockage local)
            file_path = Path(current_app.config["UPLOAD_FOLDER"]) / file_to_delete
            if file_path.exists():
                file_path.unlink()
                current_app.logger.info(f"[ADMIN] Fichier {file_to_delete} supprimé du disque")
            
            # Supprimer la référence dans la base de données
            setattr(show, photo_field, None)
            if photo_field == 'file_name':
                # Si c'est la photo principale, supprimer aussi le mimetype
                show.file_mimetype = None
            elif photo_field == 'file_name2':
                show.file_mimetype2 = None
            elif photo_field == 'file_name3':
                show.file_mimetype3 = None
            
            db.session.commit()
            
            photo_num = photo_field.replace('file_name', '').replace('_', '') or '1'
            flash(f"✅ Photo {photo_num} supprimée avec succès.", "success")
            current_app.logger.info(f"[DELETE PHOTO] Photo {photo_field} supprimée du spectacle {show_id} par {user.username}")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Erreur lors de la suppression : {str(e)}", "danger")
            current_app.logger.error(f"[DELETE PHOTO] Erreur suppression photo {photo_field} du spectacle {show_id}: {e}")
    else:
        flash("⚠️ Aucune photo à supprimer.", "warning")
    
    # Rediriger selon le contexte
    if user.is_admin:
        return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for("show_edit_self", show_id=show_id))

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
        region = fix_mojibake(request.form.get("region", "").strip())
        
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
        if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"):
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
                msg = MailMessage(subject=f"Nouvelle demande école - {theme_label}", recipients=[to_addr])
                msg.body = body
                current_app.mail.send(msg)
                current_app.logger.info(f"[MAIL] ✓ Email envoyé à l'admin pour demande école: {nom_ecole}")
            except Exception as e:
                current_app.logger.error(f"[MAIL] ✗ Envoi impossible (demande école): {e}")
                print("[MAIL] envoi impossible:", e)
        else:
            if not getattr(current_app, "mail", None):
                current_app.logger.warning("[MAIL] ⚠ Flask-Mail non initialisé - Email demande école non envoyé")
            elif not current_app.config.get("MAIL_USERNAME"):
                current_app.logger.warning("[MAIL] ⚠ MAIL_USERNAME non défini")
            elif not current_app.config.get("MAIL_PASSWORD"):
                current_app.logger.warning("[MAIL] ⚠ MAIL_PASSWORD non défini")
        
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

# =====================================================================
# Phase 5 : Fonctionnalités Avancées
# =====================================================================

# ── 5.1  Système de notation / avis ─────────────────────────────────

@app.route("/show/<int:show_id>/review", methods=["POST"])
def submit_review(show_id):
    """Soumettre un avis sur un spectacle."""
    show = Show.query.get_or_404(show_id)
    if not show.approved:
        abort(404)

    author = request.form.get("author_name", "").strip()
    rating_str = request.form.get("rating", "")
    comment = request.form.get("comment", "").strip()

    # Validation
    if not author or len(author) < 2:
        flash("Merci d'indiquer votre nom (2 caractères minimum).", "warning")
        return redirect(url_for("show_detail", show_id=show_id))
    if not rating_str.isdigit() or not (1 <= int(rating_str) <= 5):
        flash("Merci de sélectionner une note entre 1 et 5 étoiles.", "warning")
        return redirect(url_for("show_detail", show_id=show_id))

    # Limiter le commentaire
    if len(comment) > 1000:
        comment = comment[:1000]

    u = current_user()
    review = Review(
        show_id=show_id,
        user_id=u.id if u else None,
        author_name=author,
        rating=int(rating_str),
        comment=comment or None,
        approved=False,  # Modération admin requise
    )
    db.session.add(review)
    db.session.commit()

    # Notification au propriétaire du spectacle
    if show.user_id:
        notif = Notification(
            user_id=show.user_id,
            type="review",
            title="Nouvel avis sur votre spectacle",
            body=f"{author} a laissé un avis {int(rating_str)}★ sur « {show.title} » (en attente de modération).",
            link=url_for("show_detail", show_id=show_id),
        )
        db.session.add(notif)
        db.session.commit()

    flash("Merci pour votre avis ! Il sera visible après validation par notre équipe.", "success")
    return redirect(url_for("show_detail", show_id=show_id))


@app.route("/admin/reviews")
@login_required
@admin_required
def admin_reviews():
    """Gestion des avis (modération)."""
    pending = Review.query.filter_by(approved=False).order_by(Review.created_at.desc()).all()
    approved = Review.query.filter_by(approved=True).order_by(Review.created_at.desc()).limit(50).all()
    return render_template("admin_reviews.html", user=current_user(), pending=pending, approved=approved)


@app.route("/admin/reviews/<int:review_id>/approve", methods=["POST"])
@login_required
@admin_required
def admin_approve_review(review_id):
    """Approuver un avis."""
    review = Review.query.get_or_404(review_id)
    review.approved = True
    db.session.commit()
    flash("Avis approuvé et publié.", "success")
    return redirect(url_for("admin_reviews"))


@app.route("/admin/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_review(review_id):
    """Supprimer un avis."""
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Avis supprimé.", "success")
    return redirect(url_for("admin_reviews"))


# ── 5.2  Messagerie interne ─────────────────────────────────────────

@app.route("/messages")
@login_required
def messages_inbox():
    """Boîte de réception — toutes les conversations de l'utilisateur."""
    u = current_user()
    conversations = Conversation.query.filter(
        db.or_(Conversation.user1_id == u.id, Conversation.user2_id == u.id)
    ).order_by(Conversation.updated_at.desc()).all()

    # Enrichir chaque conversation avec le dernier message et le compteur de non-lus
    conv_data = []
    for c in conversations:
        other = c.user2 if c.user1_id == u.id else c.user1
        last_msg = Message.query.filter_by(conversation_id=c.id).order_by(Message.created_at.desc()).first()
        unread = Message.query.filter(
            Message.conversation_id == c.id,
            Message.sender_id != u.id,
            Message.read_at.is_(None),
        ).count()
        conv_data.append({"conv": c, "other": other, "last_msg": last_msg, "unread": unread})

    return render_template("messages_inbox.html", user=u, conversations=conv_data)


@app.route("/messages/<int:conv_id>", methods=["GET", "POST"])
@login_required
def messages_thread(conv_id):
    """Afficher / envoyer un message dans une conversation."""
    u = current_user()
    conv = Conversation.query.get_or_404(conv_id)

    # Sécurité : seuls les deux participants
    if u.id not in (conv.user1_id, conv.user2_id):
        abort(403)

    other = conv.user2 if conv.user1_id == u.id else conv.user1

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content and len(content) <= 2000:
            msg = Message(conversation_id=conv.id, sender_id=u.id, content=content)
            db.session.add(msg)
            conv.updated_at = datetime.utcnow()
            # Notification pour le destinataire
            notif = Notification(
                user_id=other.id,
                type="message",
                title=f"Nouveau message de {u.raison_sociale or u.username}",
                body=content[:100] + ("…" if len(content) > 100 else ""),
                link=url_for("messages_thread", conv_id=conv.id),
            )
            db.session.add(notif)
            db.session.commit()
        return redirect(url_for("messages_thread", conv_id=conv.id))

    # Marquer les messages reçus comme lus
    Message.query.filter(
        Message.conversation_id == conv.id,
        Message.sender_id != u.id,
        Message.read_at.is_(None),
    ).update({"read_at": datetime.utcnow()})
    db.session.commit()

    messages_list = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.asc()).all()
    return render_template("messages_thread.html", user=u, conv=conv, other=other, messages=messages_list)


@app.route("/messages/new/<int:recipient_id>", methods=["GET", "POST"])
@login_required
def messages_new(recipient_id):
    """Créer ou reprendre une conversation avec un utilisateur."""
    u = current_user()
    recipient = User.query.get_or_404(recipient_id)

    if u.id == recipient.id:
        flash("Vous ne pouvez pas vous envoyer un message.", "warning")
        return redirect(url_for("messages_inbox"))

    # Vérifier s'il existe déjà une conversation entre ces deux utilisateurs
    existing = Conversation.query.filter(
        db.or_(
            db.and_(Conversation.user1_id == u.id, Conversation.user2_id == recipient.id),
            db.and_(Conversation.user1_id == recipient.id, Conversation.user2_id == u.id),
        )
    ).first()

    if existing:
        if request.method == "POST":
            content = request.form.get("content", "").strip()
            if content and len(content) <= 2000:
                msg = Message(conversation_id=existing.id, sender_id=u.id, content=content)
                db.session.add(msg)
                existing.updated_at = datetime.utcnow()
                db.session.add(Notification(user_id=recipient.id, type="message",
                    title=f"Nouveau message de {u.raison_sociale or u.username}",
                    body=content[:100], link=url_for("messages_thread", conv_id=existing.id)))
                db.session.commit()
            return redirect(url_for("messages_thread", conv_id=existing.id))
        return redirect(url_for("messages_thread", conv_id=existing.id))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        subject = request.form.get("subject", "").strip() or None
        show_id = request.args.get("show_id", type=int)
        if content and len(content) <= 2000:
            conv = Conversation(user1_id=u.id, user2_id=recipient.id, show_id=show_id, subject=subject)
            db.session.add(conv)
            db.session.flush()
            msg = Message(conversation_id=conv.id, sender_id=u.id, content=content)
            db.session.add(msg)
            db.session.add(Notification(user_id=recipient.id, type="message",
                title=f"Nouveau message de {u.raison_sociale or u.username}",
                body=content[:100], link=url_for("messages_thread", conv_id=conv.id)))
            db.session.commit()
            return redirect(url_for("messages_thread", conv_id=conv.id))

    show_id = request.args.get("show_id", type=int)
    show = Show.query.get(show_id) if show_id else None
    return render_template("messages_new.html", user=u, recipient=recipient, show=show)


# ── 5.3  Analytics avancé ───────────────────────────────────────────

@app.route("/admin/fix-encoding")
@login_required
@admin_required
def admin_fix_encoding():
    """Corrige le mojibake (Île-de-France etc.) dans la base de données."""
    from models.models import DemandeAnimation
    fixed = 0
    for d in DemandeAnimation.query.all():
        for field in ['lieu_ville', 'region']:
            val = getattr(d, field, None)
            if not val:
                continue
            new_val = val
            # Cas: premier caractère est chr(0xce) = 'Î' stocké sans le 'I' (latin-1 tronqué)
            if new_val and ord(new_val[0]) == 0xce and not new_val.startswith('I'):
                new_val = 'Î' + new_val[1:]
            # Cas: mojibake classique (UTF-8 lu comme Latin-1)
            if new_val and ('Ã' in new_val or 'Â' in new_val):
                try:
                    new_val = new_val.encode('latin-1').decode('utf-8')
                except Exception:
                    pass
            # Cas: lieu_ville contient "Ville · Région" (autocomplete navigateur)
            if field == 'lieu_ville' and new_val and '·' in new_val:
                new_val = new_val.split('·')[0].strip()
            if new_val != val:
                setattr(d, field, new_val)
                fixed += 1
    db.session.commit()
    flash(f"✅ {fixed} champ(s) corrigé(s) dans la base.", "success")
    return redirect(url_for("admin_demandes_animation"))

@app.route("/admin/analytics")
@login_required
@admin_required
def admin_analytics():
    """Dashboard analytics business."""
    from sqlalchemy import func

    u = current_user()
    today = datetime.utcnow().date()

    # KPIs
    total_users = User.query.count()
    total_shows = Show.query.filter_by(approved=True).count()
    total_demandes = DemandeAnimation.query.count()
    total_reviews = Review.query.filter_by(approved=True).count()
    total_messages = Message.query.count()

    # Vues des 30 derniers jours
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    total_views_30d = ShowView.query.filter(ShowView.created_at >= thirty_days_ago).count()

    # Top 10 spectacles les plus vus
    top_shows = db.session.query(
        Show.id, Show.title, Show.raison_sociale,
        func.count(ShowView.id).label("views")
    ).join(ShowView, ShowView.show_id == Show.id).group_by(
        Show.id, Show.title, Show.raison_sociale
    ).order_by(func.count(ShowView.id).desc()).limit(10).all()

    # Top spectacles par note moyenne
    top_rated = db.session.query(
        Show.id, Show.title,
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).join(Review, Review.show_id == Show.id).filter(
        Review.approved.is_(True)
    ).group_by(Show.id, Show.title).having(
        func.count(Review.id) >= 1
    ).order_by(func.avg(Review.rating).desc()).limit(10).all()

    # Inscriptions par mois (6 derniers mois)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_users = db.session.query(
        func.date_trunc('month', User.created_at).label("month"),
        func.count(User.id)
    ).filter(User.created_at >= six_months_ago).group_by("month").order_by("month").all()

    return render_template("admin_analytics.html", user=u,
        total_users=total_users, total_shows=total_shows,
        total_demandes=total_demandes, total_reviews=total_reviews,
        total_messages=total_messages, total_views_30d=total_views_30d,
        top_shows=top_shows, top_rated=top_rated, monthly_users=monthly_users)


@app.route("/my-analytics")
@login_required
def my_analytics():
    """Analytics pour une compagnie (ses propres spectacles)."""
    from sqlalchemy import func

    u = current_user()
    my_shows = Show.query.filter_by(user_id=u.id).all()
    show_ids = [s.id for s in my_shows]

    if not show_ids:
        return render_template("my_analytics.html", user=u, my_shows=[], stats={})

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    # Vues par spectacle (30j)
    views_by_show = dict(db.session.query(
        ShowView.show_id, func.count(ShowView.id)
    ).filter(ShowView.show_id.in_(show_ids), ShowView.created_at >= thirty_days_ago
    ).group_by(ShowView.show_id).all())

    # Avis par spectacle
    reviews_by_show = dict(db.session.query(
        Review.show_id, func.count(Review.id)
    ).filter(Review.show_id.in_(show_ids), Review.approved.is_(True)
    ).group_by(Review.show_id).all())

    # Note moyenne par spectacle
    avg_by_show = dict(db.session.query(
        Review.show_id, func.avg(Review.rating)
    ).filter(Review.show_id.in_(show_ids), Review.approved.is_(True)
    ).group_by(Review.show_id).all())

    stats = {}
    for s in my_shows:
        stats[s.id] = {
            "views_30d": views_by_show.get(s.id, 0),
            "reviews": reviews_by_show.get(s.id, 0),
            "avg_rating": round(float(avg_by_show.get(s.id, 0)), 1),
        }

    total_views = sum(v for v in views_by_show.values())
    total_reviews = sum(v for v in reviews_by_show.values())

    return render_template("my_analytics.html", user=u, my_shows=my_shows, stats=stats,
                           total_views=total_views, total_reviews=total_reviews)


# ── 5.4  Notifications ──────────────────────────────────────────────

@app.route("/notifications")
@login_required
def notifications_page():
    """Page de toutes les notifications."""
    u = current_user()
    notifs = Notification.query.filter_by(user_id=u.id).order_by(Notification.created_at.desc()).limit(50).all()
    # Marquer comme lues
    Notification.query.filter_by(user_id=u.id, read=False).update({"read": True})
    db.session.commit()
    return render_template("notifications.html", user=u, notifications=notifs)


@app.route("/api/notifications/count")
def notifications_count():
    """API JSON — nombre de notifications non lues (pour le badge header)."""
    u = current_user()
    if not u:
        return {"unread": 0}
    count = Notification.query.filter_by(user_id=u.id, read=False).count()
    return {"unread": count}


@app.route("/api/notifications/unread-messages")
def unread_messages_count():
    """API JSON — nombre de messages non lus."""
    u = current_user()
    if not u:
        return {"unread": 0}
    count = Message.query.join(Conversation).filter(
        db.or_(Conversation.user1_id == u.id, Conversation.user2_id == u.id),
        Message.sender_id != u.id,
        Message.read_at.is_(None),
    ).count()
    return {"unread": count}

# -----------------------------------------------------
# Point d'entrée pour le serveur de développement local
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
