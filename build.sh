#!/usr/bin/env bash
# Script de démarrage pour Render

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
