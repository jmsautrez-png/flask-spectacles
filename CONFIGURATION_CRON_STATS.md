# Configuration du Cron Job pour l'agrégation quotidienne

## Objectif
Exécuter automatiquement le script `aggregate_daily_stats.py` chaque jour pour sauvegarder les statistiques quotidiennes dans la table `daily_stats`.

## Solution 1 : Cron Job Render (Recommandé)

### Créer un service Cron Job dans Render

1. **Aller dans le Dashboard Render** : https://dashboard.render.com
2. **Cliquer sur "New +"** → **"Cron Job"**
3. **Configurer** :
   - **Name** : `spectacle-stats-aggregation`
   - **Environment** : `Python 3`
   - **Repository** : Sélectionner votre repo GitHub
   - **Branch** : `test_3` (ou votre branche de production)
   - **Build Command** : `pip install -r requirements.txt`
   - **Command** : `python aggregate_daily_stats.py`
   - **Schedule** : `0 1 * * *` (tous les jours à 1h00 UTC = 2h00/3h00 heure de Paris selon DST)

4. **Variables d'environnement** :
   - Copier **TOUTES** les variables d'environnement de votre service Web principal
   - En particulier : `DATABASE_URL`, `SECRET_KEY`, etc.

5. **Créer** le Cron Job

### Avantages
- ✅ Gratuit sur le plan Render Free
- ✅ Automatique, aucune maintenance
- ✅ Logs consultables dans le Dashboard
- ✅ Même environnement que l'application principale

## Solution 2 : Script Shell Render (Alternative)

Si vous ne voulez pas créer un nouveau service, utilisez le Shell Render :

### Créer un script d'agrégation avec délai

```bash
# Dans le Shell Render
cat > /opt/render/project/src/daily_aggregate_loop.sh << 'EOF'
#!/bin/bash
while true; do
    echo "$(date): Agrégation quotidienne..."
    python aggregate_daily_stats.py
    echo "$(date): Prochaine agrégation dans 24h"
    sleep 86400  # 24 heures
done
EOF

chmod +x /opt/render/project/src/daily_aggregate_loop.sh
nohup /opt/render/project/src/daily_aggregate_loop.sh > /tmp/aggregate.log 2>&1 &
```

**⚠️ Inconvénient** : Se termine au redémarrage du service (déploiement, maintenance Render)

## Solution 3 : Déclencheur externe (UptimeRobot, EasyCron)

### Créer une route Flask déclencheur

Ajouter dans `app.py` :

```python
@app.route("/cron/aggregate-stats", methods=["POST"])
def cron_aggregate_stats():
    """Route protégée pour déclencher l'agrégation (à appeler par un cron externe)"""
    # Vérifier un secret partagé
    secret = request.headers.get("X-Cron-Secret") or request.args.get("secret")
    if secret != os.getenv("CRON_SECRET", "change-me"):
        return jsonify({"error": "Unauthorized"}), 403
    
    from aggregate_daily_stats import aggregate_yesterday_stats
    try:
        aggregate_yesterday_stats()
        return jsonify({"status": "success", "message": "Stats agregated"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

Puis configurer un service externe (gratuit) :
- **EasyCron** : https://www.easycron.com (gratuit jusqu'à 5 jobs)
- **cron-job.org** : https://cron-job.org (gratuit)

Configurer pour appeler chaque jour :
```
POST https://spectacleanimation.fr/cron/aggregate-stats?secret=VOTRE_SECRET
```

## Solution Finale Recommandée

**🎯 Cron Job Render** (Solution 1) est la meilleure option :
- Gratuit
- Fiable
- Logs disponibles
- Intégré à votre infrastructure

## Commandes de test

### Test local
```bash
python aggregate_daily_stats.py
```

### Test en production (Shell Render)
```bash
python aggregate_daily_stats.py
```

### Test avec force update
```bash
python aggregate_daily_stats.py --force
```

## Vérification

Après l'exécution quotidienne, vérifier les données :

```bash
python -c "
from app import app, db
from sqlalchemy import text

with app.app_context():
    stats = db.session.execute(text('''
        SELECT stat_date, total_visitors, total_page_views 
        FROM daily_stats 
        ORDER BY stat_date DESC 
        LIMIT 7
    ''')).fetchall()
    
    print('📊 Dernières statistiques :')
    for date, visitors, pages in stats:
        print(f'  {date}: {visitors} visiteurs, {pages} pages')
"
```

## Nettoyage des données brutes (optionnel)

Une fois les données agrégées, vous pouvez nettoyer les données `visitor_log` de plus de 90 jours :

```bash
# Ajouter dans le cron job si souhaité
python clean_visitor_logs.py
```

Cela libère de l'espace tout en conservant les statistiques historiques dans `daily_stats`.
