"""Configuration Gunicorn pour le déploiement en production"""
import os
import multiprocessing

# Bind sur l'interface publique avec le port fourni par Render/Heroku
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Nombre de workers — 1 par défaut sur petite instance pour limiter la RAM.
# Peut être augmenté via GUNICORN_WORKERS si l'instance est dimensionnée.
workers = int(os.environ.get('GUNICORN_WORKERS', 1))
workers = max(1, min(workers, 2))

# Type de worker
worker_class = 'sync'

# Timeout pour les requêtes longues (upload de fichiers et envoi emails massifs)
timeout = 300  # 5 minutes pour permettre l'envoi de nombreux emails
keepalive = 5

# Logging
accesslog = '-'  # Log vers stdout
errorlog = '-'   # Log vers stderr
loglevel = 'debug'  # Level debug pour voir toutes les erreurs

# Preload désactivé pour mieux voir les erreurs au démarrage
preload_app = False

# Recycler les workers souvent pour éviter les fuites mémoire (512MB)
max_requests = 200
max_requests_jitter = 50

# Configuration des connexions
backlog = 2048

# Redémarrage gracieux
graceful_timeout = 30

print(f"""
═══════════════════════════════════════════════════════════
CONFIGURATION GUNICORN
═══════════════════════════════════════════════════════════
Bind: {bind}
Workers: {workers}
Timeout: {timeout}s
Log Level: {loglevel}
Preload: {preload_app}
═══════════════════════════════════════════════════════════
""")
