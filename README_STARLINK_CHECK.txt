#!/bin/bash
# Commande pour exécuter le script sur Render via SSH
# Remplace <SERVICE_ID> par ton ID de service Render

echo "Pour exécuter sur Render:"
echo ""
echo "Option 1: Via le Dashboard Render"
echo "  1. Ouvre https://dashboard.render.com"
echo "  2. Clique sur 'flask-spectacles'"
echo "  3. Clique sur 'Shell' en haut à droite"
echo "  4. Exécute: python check_starlink_production.py"
echo ""
echo "Option 2: Via commande directe (nécessite identifiants Render)"
echo "  Contacte le shell depuis ton terminal local si configuré"
echo ""
echo "Le script va afficher TOUTES tes visites Starlink des 48 dernières heures"
echo "avec le statut BOT ou HUMAIN et le nombre de pages visitées."
