# 🤖 Correction Détection des Bots - Instructions Production

## ⚠️ Problème identifié

Les bots sophistiqués (Google LLC, Microsoft Corporation, Facebook Inc., Tencent) contournaient la détection en incluant "Chrome" ou "Safari" dans leur User-Agent.

**Résultat** : 60+ crawlers de datacenters étaient classés comme "Humains" dans les statistiques.

**Problème supplémentaire** : Même avec Starlink (whitelist), certains bots visitaient 100+ pages par session.

## ✅ Solutions implémentées

### 1. Fonction de détection stricte - LISTE BLANCHE (`app.py` lignes 320-395)

**APPROCHE INVERSÉE** : Au lieu de bloquer les bots, on autorise UNIQUEMENT les FAI français :

**Liste blanche des FAI résidentiels français** :
- Orange, Free/Proxad, SFR, Bouygues, Numericable
- Opérateurs secondaires : La Poste Mobile, NRJ Mobile, Lycamobile, etc.
- FAI régionaux : Alsatis, Auchan Telecom, etc.
- Internet satellite : Starlink

**Tout le reste = BOT automatiquement** :
- Google LLC, Microsoft, Facebook → BOT
- Datacenters (Hivelocity, Oracle, OVH) → BOT
- IPs non résolues (144.217.0.0) → BOT
- ISP étrangers → BOT

### 2. Détection comportementale - Limite de pages (`app.py` ligne 505)

**RÈGLE** : **Plus de 10 pages visitées en une session = BOT**

Un humain normal visite rarement plus de 10 pages en une session. Au-delà = scraper/crawler.

**Fonctionnement** :
- À chaque visite, on compte combien de pages cette `session_id` a déjà visitées
- Si ≥ 10 pages → Marqué automatiquement comme BOT
- S'applique même aux FAI français (bloque les crawlers Starlink 129 pages)

**Exemple** :
```
Session ABC123... visite 1-10 pages → Humain ✅
Session ABC123... visite page 11+ → Bot automatique 🚫
```

### 3. Script de reclassification amélioré

`reclassify_bots.py` : Retraite TOUS les logs existants avec :
1. Détection par ISP/User-Agent (liste blanche)
2. Détection par nombre de pages (>10 = bot)

## 🚀 Déploiement sur Render

### Étape 1 : Déployer le nouveau code

Le code est déjà pushé sur GitHub (branche `test_3`). Render va redéployer automatiquement.

### Étape 2 : Exécuter la reclassification en production

Une fois le déploiement terminé, connectez-vous au **Shell Web Render** et exécutez :

```bash
echo "oui" | python reclassify_bots.py
```

### Étape 3 : Vérifier les résultats

Le script affichera :

```
📊 Analyse des sessions (limite: 10 pages max pour humains)...
   Sessions suspectes (>10 pages): XX
      - Session XXX: 129 pages  ← Starlink crawler détecté
      - Session YYY: 88 pages   ← Autre scraper

📈 AVANT reclassification:
   Bots: 9912 (78.9%)
   Humains: 2652 (21.1%)

📈 APRÈS reclassification:
   Bots: XXXX (XX%)  ← Encore plus de bots détectés
   Humains: XXXX (XX%)

📊 CHANGEMENTS:
   Humain → Bot (ISP/User-Agent): XX
   Humain → Bot (>10 pages): XX  ← Nouveaux bots détectés
   Humain → Bot (TOTAL): XXX
```

## 📊 Résultats attendus

**Sessions Starlink 129 pages** : Seront reclassées en BOT

**Attendez-vous à voir** :
- 50-60+ visiteurs reclassés de "Humain" → "Bot" (ISP datacenter)
- 20-30+ sessions reclassées en "Bot" (>10 pages)
- **Total bots : probablement 85-90%** du trafic

## ⚡ Impact sur les statistiques

Après la reclassification :
- ✅ Graphique "Visiteurs uniques" : **Données ultra-précises** (humains français uniquement, <10 pages)
- ✅ Tableau journalier : Comptes réalistes
- ✅ Derniers visiteurs : Plus de crawlers Google/Microsoft/Starlink 129 pages

## 🔍 Vérification en temps réel

**Nouvelles visites** : Automatiquement détectées avec les 2 règles :
1. ISP non français → BOT immédiat
2. 11ème page visitée → BOT automatique

**Log automatique** : Quand une session atteint 10 pages, vous verrez dans les logs :
```
[TRACKING] Session abc123... marquée BOT - 11 pages visitées
```

## 📝 Notes importantes

### Performance
La détection par nombre de pages fait un `COUNT(*)` à chaque visite. Cela peut ralentir légèrement le site sur gros trafic. Si nécessaire, on pourra optimiser avec un cache Redis.

### Faux positifs
Un vrai visiteur humain qui visite >10 pages sera marqué bot. C'est un compromis pour bloquer les scrapers. Vous pouvez ajuster la limite (actuellement 10) dans :
- `app.py` ligne ~508 : `if page_count >= 10:`
- `reclassify_bots.py` ligne ~97 : `if count > 10:`

### Visiteurs étrangers
Avec la liste blanche française, tous les visiteurs étrangers (USA, UK, etc.) sont marqués bots. Si vous avez un public international légitime, il faudra élargir la whitelist.

---

**Commit déployé** : `874e57d` - "🚫 Détection comportementale: >10 pages = bot"
**Branche** : `test_3`
**Date** : 2026-04-06
