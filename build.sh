#!/usr/bin/env bash
# Script de démarrage pour Render

# Nettoyer le cache Python pour forcer le rechargement du code
echo "🧹 Nettoyage du cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Créer le dossier uploads s'il n'existe pas
mkdir -p static/uploads

# Exécuter les migrations de base de données
echo "🔄 Exécution des migrations..."
if [ -f "migrate_production_postgres.py" ]; then
    python migrate_production_postgres.py || echo "⚠️  Avertissement: La migration a échoué mais on continue..."
fi

# Lancer l'application
echo "🚀 Démarrage de l'application..."
exec gunicorn app:app
