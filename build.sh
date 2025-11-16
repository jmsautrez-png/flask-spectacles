#!/usr/bin/env bash
# Script de démarrage pour Render

# Créer le dossier uploads s'il n'existe pas
mkdir -p static/uploads

# Lancer l'application
exec gunicorn app:app
