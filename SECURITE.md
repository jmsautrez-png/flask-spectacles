# 🔒 PROTECTIONS DE SÉCURITÉ - Flask Spectacles

## ✅ Protections implémentées

### 1. 🛡️ Protection contre les attaques par force brute

#### Rate Limiting (Flask-Limiter)
- **Limite globale** : 200 requêtes/jour, 50 requêtes/heure par IP
- **Protection** : Empêche les attaques automatisées (bots, scrapers)
- **Routes protégées** : Toutes les routes de l'application

**Configuration :**
```python
Limiter(
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
```

---

### 2. 🔐 Protection des sessions et cookies

#### Sécurité des sessions
- ✅ `SESSION_COOKIE_HTTPONLY = True` - Cookies non accessibles en JavaScript (XSS)
- ✅ `SESSION_COOKIE_SAMESITE = "Lax"` - Protection CSRF
- ✅ `SESSION_COOKIE_SECURE = True` (production) - HTTPS obligatoire
- ✅ `PERMANENT_SESSION_LIFETIME = 3600` - Session expire après 1 heure

**Protection contre :**
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Vol de session

---

### 3. 🌐 Headers de sécurité HTTP (Flask-Talisman)

#### En production uniquement
- ✅ **HTTPS forcé** - Toutes les requêtes redirigées vers HTTPS
- ✅ **HSTS** (Strict-Transport-Security) - Force HTTPS dans le navigateur
- ✅ **Content Security Policy** - Limite les sources de contenu
- ✅ **X-Frame-Options** - Empêche le clickjacking
- ✅ **X-Content-Type-Options** - Empêche le MIME sniffing

**CSP configuré :**
```python
{
    'default-src': "'self'",
    'img-src': ["'self'", "data:"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'script-src': ["'self'", "'unsafe-inline'"],
}
```

---

### 4. 🤖 Détection et blocage des bots malveillants

#### User-Agent Analysis
Détection automatique des bots malveillants :
- ❌ SQLMap, Nikto, Nmap, Masscan
- ❌ Acunetix, Burp Suite, Havij
- ❌ Scrapy, curl (certaines versions)
- ❌ Requêtes sans User-Agent

**Action :** Redirection vers la page d'accueil avec message d'erreur

---

### 5. 🔒 Validation des entrées utilisateur

#### Mots de passe
- ✅ Minimum 6 caractères (configurable)
- ✅ Hashage avec Werkzeug (PBKDF2)
- ✅ Pas de stockage en clair

#### Noms d'utilisateur
- ✅ Protection injection SQL (caractères spéciaux : `'`, `"`, `;`, `--`, `/*`)
- ✅ Vérification unicité
- ✅ SQLAlchemy protège nativement

#### Uploads de fichiers
- ✅ Limite de taille : 5 MB
- ✅ Types autorisés : `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.pdf`
- ✅ Validation MIME type
- ✅ Noms de fichiers sécurisés (timestamp unique)

---

### 6. 🗄️ Sécurité de la base de données

#### SQLAlchemy
- ✅ **Requêtes paramétrées** - Protection native contre SQL injection
- ✅ **Pas de SQL brut** - Utilisation de l'ORM uniquement
- ✅ **Transactions** - Rollback automatique en cas d'erreur

#### Gestion des erreurs
- ✅ Logs d'erreurs sans exposer les détails sensibles
- ✅ Messages génériques pour l'utilisateur

---

### 7. 🚫 Protection contre les attaques communes

#### Cross-Site Scripting (XSS)
- ✅ Jinja2 échappe automatiquement les variables
- ✅ Headers CSP configurés
- ✅ Session cookies HTTPONLY

#### Cross-Site Request Forgery (CSRF)
- ✅ SameSite cookies ("Lax")
- ✅ Validation d'origine
- ⚠️ **À ajouter** : CSRF tokens Flask-WTF (recommandé)

#### SQL Injection
- ✅ SQLAlchemy ORM (requêtes paramétrées)
- ✅ Validation des caractères spéciaux
- ✅ Pas de SQL brut

#### Path Traversal
- ✅ Validation des noms de fichiers
- ✅ Uploads dans dossier dédié
- ✅ Pas d'accès direct aux fichiers système

#### Clickjacking
- ✅ X-Frame-Options header
- ✅ CSP frame-ancestors

---

## 🔧 Configuration recommandée pour la production

### Variables d'environnement obligatoires

```bash
# Sécurité
SECRET_KEY=xxx  # Générer : python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV=production
FLASK_DEBUG=False

# Base de données (PostgreSQL recommandé)
DATABASE_URL=postgresql://user:pass@host/db

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=xxx  # Mot de passe fort (12+ caractères, majuscules, chiffres, symboles)
```

### Recommandations supplémentaires

1. **HTTPS obligatoire** (Let's Encrypt gratuit)
2. **Firewall** : Bloquer ports non utilisés
3. **Rate limiting avancé** : Redis pour le stockage (production)
4. **Monitoring** : Sentry pour les erreurs
5. **Logs sécurisés** : Ne pas logger les mots de passe
6. **Backups réguliers** : Base de données + uploads
7. **Mises à jour** : Flask, SQLAlchemy, dépendances

---

## 🚨 Limites actuelles et améliorations futures

### ⚠️ À améliorer

1. **CSRF Tokens** : Ajouter Flask-WTF pour tokens CSRF
   ```bash
   pip install Flask-WTF
   ```

2. **Captcha** : Ajouter reCAPTCHA sur login/register
   ```bash
   pip install Flask-ReCaptcha
   ```

3. **2FA** : Authentification à deux facteurs (optionnel)
   ```bash
   pip install pyotp qrcode
   ```

4. **Audit logs** : Logger les actions sensibles (connexions, modifications)

5. **IP Whitelisting** : Pour le dashboard admin

6. **Stockage sécurisé uploads** : AWS S3 avec buckets privés

---

## 🧪 Tests de sécurité

### Tests manuels recommandés

```bash
# 1. Tester le rate limiting
for i in {1..60}; do curl http://localhost:5000/ ; done

# 2. Tester les injections SQL (doit échouer)
curl -X POST http://localhost:5000/login \
  -d "username=admin' OR '1'='1&password=test"

# 3. Tester upload de fichier trop gros (doit échouer)
# Créer un fichier de 10 MB et tenter l'upload

# 4. Tester les headers de sécurité (production)
curl -I https://votre-site.com
```

### Outils de scan automatisés

- **OWASP ZAP** : Scanner de vulnérabilités
- **Nikto** : Scanner serveur web
- **SQLMap** : Test injection SQL (doit échouer)
- **Burp Suite** : Test complet de sécurité

---

## 📊 Niveaux de sécurité par environnement

### Développement (local)
- ✅ Rate limiting activé
- ✅ Validation des entrées
- ❌ HTTPS (pas nécessaire)
- ❌ Talisman (désactivé)

### Staging
- ✅ Rate limiting activé
- ✅ Validation des entrées
- ✅ HTTPS recommandé
- ✅ Talisman activé

### Production
- ✅ Rate limiting activé (Redis)
- ✅ Validation des entrées
- ✅ HTTPS OBLIGATOIRE
- ✅ Talisman activé
- ✅ Monitoring actif
- ✅ Backups automatiques

---

## 🆘 En cas d'attaque détectée

1. **Identifier la source** : Vérifier les logs
2. **Bloquer l'IP** : Firewall ou Cloudflare
3. **Vérifier l'intégrité** : Base de données, fichiers
4. **Changer les secrets** : SECRET_KEY, mots de passe
5. **Notifier** : Utilisateurs si données compromises
6. **Audit** : Vérifier toutes les vulnérabilités

---

## 📚 Ressources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/latest/core/security.html)

---

**🔒 La sécurité est un processus continu, pas un état final !**
