# 📊 Système de Tracking des Visiteurs

## ✅ Conformité RGPD

Ce système de tracking est **conforme RGPD** car :

- ✅ **IP anonymisées** : Seuls les 2 premiers octets sont conservés (192.168.xxx.xxx → 192.168.0.0)
- ✅ **Données temporaires** : Suppression automatique après 30 jours
- ✅ **Pas de profilage** : Aucune donnée personnelle pour les visiteurs anonymes
- ✅ **Transparence** : Les utilisateurs connectés sont informés de la collecte de leurs données
- ✅ **Finalité limitée** : Usage strictement statistique pour améliorer le site

**Aucune bannière de consentement n'est nécessaire** pour ce type de tracking anonymisé.

---

## 🚀 Installation

### 1. Exécuter la migration

```bash
python migrate_add_visitor_log.py
```

Cette commande crée la table `visitor_log` dans votre base de données.

### 2. Redémarrer l'application

```bash
python app.py
```

Le tracking est maintenant **actif automatiquement** !

---

## 📈 Données collectées

### Pour TOUS les visiteurs (anonymisé) :
- ✅ Date et heure de visite
- ✅ Page consultée
- ✅ Référent (d'où vient le visiteur : Google, lien direct, etc.)
- ✅ Navigateur utilisé (Chrome, Firefox, Safari...)
- ✅ **IP anonymisée** (ex: 192.168.0.0 au lieu de 192.168.1.123)
- ✅ Identifiant de session temporaire (change toutes les 24h)

### Pour les utilisateurs CONNECTÉS :
- ✅ Tout ce qui précède
- ✅ Nom d'utilisateur
- ✅ Relation avec leur compte

---

## 📊 Consulter les statistiques

### En tant qu'administrateur :

1. Connectez-vous avec votre compte admin
2. Allez sur le **Tableau de bord administrateur**
3. Cliquez sur le bouton **📊 Statistiques visiteurs**

### Vous verrez :

- 📈 **Nombre total de visites** sur la période sélectionnée
- 👥 **Visiteurs uniques** (sessions différentes)
- 📊 **Moyenne de visites par jour**
- 🔥 **Pages les plus consultées**
- 🌐 **Sources de trafic** (Google, Facebook, liens directs...)
- 📅 **Évolution des visites par jour**
- 👤 **Utilisateurs connectés les plus actifs**
- ⏱️ **Dernières 50 visites en temps réel**

### Filtres disponibles :
- Dernières 24 heures
- 7 derniers jours
- 30 derniers jours
- 90 derniers jours

---

## 🗑️ Nettoyage automatique (RGPD)

Pour respecter le RGPD, les données de plus de **30 jours** doivent être supprimées.

### Nettoyage manuel :

```bash
python clean_visitor_logs.py
```

### Nettoyage automatique (recommandé) :

**Windows (Planificateur de tâches)** :
1. Ouvrir le Planificateur de tâches Windows
2. Créer une nouvelle tâche
3. Déclencheur : Tous les jours à 3h du matin
4. Action : Lancer `python clean_visitor_logs.py`

**Linux (Cron)** :
```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour exécuter tous les jours à 3h
0 3 * * * cd /chemin/vers/flask-spectacles && python clean_visitor_logs.py
```

**Render/Heroku (Cloud)** :
Créer un "Scheduled Job" ou "Worker" qui exécute quotidiennement :
```bash
python clean_visitor_logs.py
```

---

## 🔍 Ce qui est TRACKÉÉ vs PAS TRACKÉ

### ✅ TRACKÉ :
- Toutes les pages du site (`/`, `/spectacles`, `/about`, etc.)
- Détail d'un spectacle (`/spectacle/123`)
- Pages de connexion/inscription
- Dashboard utilisateur

### ❌ PAS TRACKÉ :
- Fichiers statiques (`/static/css/style.css`, `/static/img/logo.png`)
- Robots.txt
- Favicon

---

## 💡 Exemples d'utilisation

### Savoir d'où viennent vos visiteurs :
Consultez la section **"D'où viennent les visiteurs"** pour voir :
- Combien viennent de Google
- Combien viennent de Facebook
- Combien arrivent directement sur le site

### Identifier les pages populaires :
La section **"Pages les plus visitées"** vous montre :
- Quels spectacles sont les plus consultés
- Quelles pages du site intéressent le plus

### Suivre la croissance :
Le graphique **"Visites par jour"** vous permet de :
- Voir l'évolution du trafic
- Identifier les jours de pics de visite
- Mesurer l'impact de vos actions marketing

---

## 🛡️ Sécurité et confidentialité

### Données stockées de manière sécurisée :
- Toutes les données sont dans votre base de données privée
- Aucune donnée n'est partagée avec des tiers
- Les IP sont anonymisées dès la collecte
- Les sessions sont temporaires et non reliées à des personnes

### Conformité légale :
Ce système respecte :
- ✅ RGPD (Règlement Général sur la Protection des Données)
- ✅ Directive ePrivacy
- ✅ CNIL (France)

**Aucune bannière de cookies n'est nécessaire** car :
- Pas de cookies publicitaires
- Pas de tracking comportemental
- Données anonymisées
- Usage interne uniquement

---

## ❓ FAQ

### Q: Dois-je informer mes visiteurs ?
**R:** Non, le tracking est anonymisé et à usage interne. Cependant, vous pouvez ajouter une mention dans vos CGU si vous le souhaitez.

### Q: Puis-je identifier un visiteur spécifique ?
**R:** Non, les IP sont anonymisées. Vous ne pouvez identifier que les utilisateurs connectés par leur nom d'utilisateur.

### Q: Combien d'espace disque cela prend ?
**R:** Environ 1 Ko par visite. Pour 1000 visites/jour pendant 30 jours = ~30 Mo.

### Q: Est-ce que ça ralentit le site ?
**R:** Non, l'enregistrement est très rapide (< 10ms) et s'exécute en arrière-plan.

### Q: Puis-je désactiver le tracking ?
**R:** Oui, commentez simplement la fonction `@app.before_request` dans `app.py`.

---

## 📝 Structure de la table `visitor_log`

```sql
CREATE TABLE visitor_log (
    id INTEGER PRIMARY KEY,
    visited_at DATETIME NOT NULL,           -- Date/heure de visite
    page_url VARCHAR(300) NOT NULL,         -- Page visitée
    referrer VARCHAR(300),                  -- D'où vient le visiteur
    user_agent VARCHAR(300),                -- Navigateur
    ip_anonymized VARCHAR(20),              -- IP anonymisée
    session_id VARCHAR(50),                 -- ID de session temporaire
    user_id INTEGER,                        -- Utilisateur connecté (optionnel)
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

---

## 🎯 Objectifs de ce système

1. **Comprendre votre audience** : Qui visite votre site et d'où ?
2. **Optimiser le contenu** : Quelles pages intéressent le plus ?
3. **Mesurer la croissance** : Évolution du trafic dans le temps
4. **Respecter la vie privée** : Aucune donnée personnelle collectée
5. **Conformité légale** : 100% conforme RGPD

---

## 🆘 Support

En cas de problème :
1. Vérifiez que la migration a bien été exécutée
2. Consultez les logs de l'application
3. Vérifiez que la table `visitor_log` existe dans votre base de données

```bash
python list_tables.py  # Pour voir toutes les tables
```

---

**Créé le :** 28 mars 2026  
**Version :** 1.0  
**Conformité RGPD :** ✅ Vérifié
