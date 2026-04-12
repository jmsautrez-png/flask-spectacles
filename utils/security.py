"""Security utilities: bot detection, suspicious request detection, auth decorators."""
from typing import Optional
from functools import wraps

from flask import session, redirect, url_for, flash, request

from models.models import User


def current_user() -> Optional[User]:
    username = session.get("username")
    if not username:
        return None
    return User.query.filter_by(username=username).first()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("username"):
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("Accès réservé à l'administrateur.", "danger")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapper


def generate_password(n: int = 10) -> str:
    import string, secrets
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def is_suspicious_request() -> bool:
    user_agent = request.headers.get('User-Agent', '').lower()
    suspicious_agents = [
        'sqlmap', 'nikto', 'nmap', 'masscan', 'netsparker',
        'acunetix', 'burp', 'havij', 'scrapy', 'curl/7',
    ]
    for agent in suspicious_agents:
        if agent in user_agent:
            return True
    if not user_agent or user_agent == 'none':
        return True
    return False


def is_bot_visitor(user_agent: str, isp: str = None) -> bool:
    if not user_agent:
        return False
    user_agent_lower = user_agent.lower()
    bot_patterns = [
        'bot', 'crawler', 'spider', 'scraper', 'slurp', 'mediapartners',
        'googlebot', 'bingbot', 'yandexbot', 'baiduspider', 'facebookexternalhit',
        'twitterbot', 'linkedinbot', 'whatsapp', 'telegrambot', 'discordbot',
        'slackbot', 'pinterestbot', 'applebot', 'duckduckbot', 'ahrefsbot',
        'semrushbot', 'mj12bot', 'dotbot', 'rogerbot', 'exabot', 'sogou',
        'archive.org', 'wget', 'curl', 'python-requests', 'java/', 'go-http',
        'phantom', 'headless', 'selenium', 'webdriver', 'prerender'
    ]
    for pattern in bot_patterns:
        if pattern in user_agent_lower:
            return True
    if isp:
        isp_lower = isp.lower()
        french_residential_isps = [
            'orange', 'free', 'sfr', 'bouygues', 'red by sfr', 'sosh',
            'b&you', 'la poste mobile', 'numericable', 'nrj mobile',
            'coriolis', 'lycamobile', 'yourice', 'prixtel',
            'starlink', 'spacex', 'nordnet', 'sat2way',
            'virgin mobile', 'joe mobile', 'syma mobile',
        ]
        is_residential = any(f in isp_lower for f in french_residential_isps)
        if is_residential:
            return False
        hosting_patterns = [
            'amazon', 'aws', 'google cloud', 'microsoft', 'azure',
            'digitalocean', 'ovh', 'hetzner', 'linode', 'vultr',
            'cloudflare', 'akamai', 'fastly', 'scaleway', 'contabo',
        ]
        is_hosting = any(h in isp_lower for h in hosting_patterns)
        if is_hosting:
            return True
    return False
