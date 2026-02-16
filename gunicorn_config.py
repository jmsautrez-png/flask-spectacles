"""Configuration Gunicorn pour le déploiement en production"""
import os
import multiprocessing

# Bind sur l'interface publique avec le port fourni par Render/Heroku
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Nombre de workers (2-4 x nombre de CPU cores)
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
# Limite à 4 workers pour le plan gratuit de Render
workers = min(workers, 4)

# Type de worker
worker_class = 'sync'

# Timeout pour les requêtes longues (upload de fichiers)
timeout = 120
keepalive = 5

# Logging
accesslog = '-'  # Log vers stdout
errorlog = '-'   # Log vers stderr
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Preload désactivé pour mieux voir les erreurs au démarrage
preload_app = False

# Nombre de requêtes par worker avant redémarrage (évite les fuites mémoire)
max_requests = 1000
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
