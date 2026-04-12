# 🤖 Guide d'Analyse avec Claude Opus 4 - Spectacle'ment Vôtre

## 📋 Table des matières

1. [Phase 1 : Sécurité & Performance (PRIORITAIRE)](#phase-1--sécurité--performance-prioritaire)
2. [Phase 2 : SEO & Référencement](#phase-2--seo--référencement)
3. [Phase 3 : UX/UI & Conversion](#phase-3--uxui--conversion)
4. [Phase 4 : Architecture & Code Quality](#phase-4--architecture--code-quality)
5. [Contexte du projet](#contexte-du-projet)

---

## Phase 1 : Sécurité & Performance (PRIORITAIRE)

### 🔒 Question 1 : Audit de Sécurité

**Fichiers à fournir :**
- `app.py` (lignes 1-500, puis 500-1000, etc.)
- `config.py`
- `models/models.py`

**Prompt à utiliser :**

```
Tu es un expert en sécurité web. Analyse ce code Flask et identifie :

1. VULNÉRABILITÉS CRITIQUES :
   - SQL Injection potentielles
   - XSS (Cross-Site Scripting)
   - CSRF mal configuré
   - Upload de fichiers non sécurisés
   - Exposition de données sensibles

2. AUTHENTIFICATION & SESSIONS :
   - Gestion des mots de passe
   - Sécurité des sessions
   - Protection des routes admin

3. RECOMMANDATIONS :
   - Corrections immédiates (code prêt à l'emploi)
   - Améliorations à moyen terme
   - Best practices à adopter

Contexte : Application Flask en production avec ~200 utilisateurs
PostgreSQL, hébergée sur Render.com
```

---

### ⚡ Question 2 : Optimisation des Performances

**Fichiers à fournir :**
- `app.py` (routes catalogue, recherche, home)
- `templates/catalogue.html`
- `templates/home.html`

**Prompt à utiliser :**

```
Tu es un expert en optimisation de performances web. Analyse cette application Flask :

1. REQUÊTES SQL :
   - Identifie les requêtes N+1
   - Suggère des optimisations avec jointures/eager loading
   - Propose des index manquants

2. CACHE :
   - Opportunités de mise en cache
   - Stratégie Redis recommandée
   - Cache de templates/fragments

3. FRONTEND :
   - Images non optimisées
   - CSS/JS non minifiés
   - Lazy loading manquant

4. CODE PYTHON :
   - Fonctions lentes
   - Boucles inefficaces
   - Imports inutiles

Objectif : Réduire le temps de chargement de 3s à < 1s
Fournis du code prêt à implémenter.
```

---

## Phase 2 : SEO & Référencement

### 📈 Question 3 : Audit SEO Complet

**Fichiers à fournir :**
- `templates/base.html`
- `templates/catalogue.html`
- `templates/show.html`
- `seo_cities.py`

**Prompt à utiliser :**

```
Tu es un expert SEO spécialisé dans les sites Python/Flask. Analyse cette application :

1. META TAGS & STRUCTURE :
   - Qualité des meta descriptions
   - Optimisation des titres H1/H2/H3
   - Open Graph et Twitter Cards
   - Balises canoniques

2. DONNÉES STRUCTURÉES :
   - Implémentation Schema.org manquante
   - JSON-LD pour les spectacles (Event, Offer)
   - Breadcrumbs structurés
   - Local Business pour les compagnies

3. URLS & NAVIGATION :
   - Structure des URLs SEO-friendly
   - Sitemap.xml automatique
   - Robots.txt optimisé
   - Pagination correcte

4. CONTENU :
   - Densité de mots-clés
   - Duplicate content
   - Rich snippets opportunités

5. TECHNIQUE :
   - Core Web Vitals (LCP, FID, CLS)
   - Mobile-first responsive
   - AMP nécessaire ?

Fournis le code complet pour Schema.org et sitemap.xml
```

---

### 🎯 Question 4 : Stratégie de Contenu SEO

**Contexte à fournir :**
- Liste des catégories : Magie, Marionnette, Clown, Père Noël, Concert, DJ, etc.
- 250+ villes françaises de `seo_cities.py`

**Prompt à utiliser :**

```
Expert SEO, propose une stratégie de contenu pour ce site de spectacles :

1. PAGES À CRÉER :
   - Pages ville x catégorie (ex: "Spectacle magie Paris")
   - Pages événements (anniversaire, école, mairie, CSE)
   - Blog articles (top 10, guides)

2. CONTENUS DYNAMIQUES :
   - Génération automatique de descriptions uniques
   - Templates évitant le duplicate content
   - Variables contextuelles (ville, catégorie, saison)

3. MAILLAGE INTERNE :
   - Structure de liens
   - Fil d'Ariane optimisé
   - Liens contextuels

4. MOTS-CLÉS LONGUE TRAÎNE :
   - Liste 50 requêtes à cibler
   - Recherche vocale (Google Assistant)

Donne 5 exemples de pages complètes avec code HTML/Jinja.
```

---

## Phase 3 : UX/UI & Conversion

### 🎨 Question 5 : Optimisation UX/UI

**Fichiers à fournir :**
- `templates/demande_animation.html`
- `templates/publish.html`
- `templates/catalogue.html`

**Prompt à utiliser :**

```
Tu es un expert UX/UI spécialisé en optimisation de conversion. Analyse ces formulaires :

1. FORMULAIRE APPEL D'OFFRE :
   - Trop de champs ? Lesquels supprimer/fusionner ?
   - Ordre logique des champs
   - Messages d'aide contextuels
   - Validation en temps réel
   - Progression visuelle (étapes)

2. FORMULAIRE PUBLICATION SPECTACLE :
   - Upload de photos : drag & drop, aperçu immédiat
   - Auto-complétion intelligente
   - Suggestions SEO en temps réel (IA déjà implémentée)
   - Preview avant publication

3. CATALOGUE :
   - Filtres UX (facettes, sliders)
   - Tri pertinent
   - Grille vs Liste
   - Infinite scroll vs pagination

4. MOBILE :
   - Formulaires adaptés (input types)
   - Boutons accessibles (44px minimum)
   - Navigation simplifiée

Fournis le code HTML/CSS/JS pour chaque amélioration.
Objectif : +50% de taux de conversion
```

---

### 📊 Question 6 : Analyse du Parcours Utilisateur

**Contexte à fournir :**
- Structure complète du site (sitemap)
- Fichier `app.py` avec toutes les routes

**Prompt à utiliser :**

```
Expert en psychologie cognitive et UX, analyse le parcours utilisateur :

1. PERSONA 1 : Mairie cherchant un spectacle de Noël
   - Point d'entrée probable
   - Parcours idéal vs parcours actuel
   - Points de friction
   - Call-to-action optimaux

2. PERSONA 2 : Compagnie voulant publier un spectacle
   - Onboarding
   - Première publication
   - Gestion du profil
   - Réception des demandes

3. PERSONA 3 : École recherchant une animation pédagogique
   - Découverte des spectacles
   - Comparaison
   - Prise de contact

Pour chaque persona :
- Cartographie du parcours (user journey map)
- Points de douleur identifiés
- Solutions concrètes avec code

4. MICRO-INTERACTIONS :
   - Feedback visuel manquant
   - Animations de chargement
   - Messages de succès/erreur
   - Tooltips et hints
```

---

## Phase 4 : Architecture & Code Quality

### 🏗️ Question 7 : Refactoring & Architecture

**Fichiers à fournir :**
- `app.py` (tout le fichier, par sections)
- `models/models.py`

**Prompt à utiliser :**

```
Architecte logiciel senior Python, analyse cette application Flask :

1. STRUCTURE ACTUELLE :
   - Tout dans app.py (4600+ lignes) : problème ?
   - Découpage en blueprints recommandé ?
   - Separation of concerns

2. PATTERNS À IMPLÉMENTER :
   - Repository pattern pour les requêtes
   - Service layer pour la logique métier
   - Dependency injection
   - Factory pattern

3. DUPLICATIONS DE CODE :
   - Identifie les fonctions répétées
   - Propose des utilitaires réutilisables
   - DRY (Don't Repeat Yourself)

4. GESTION D'ERREURS :
   - Try/except trop larges
   - Logging insuffisant
   - Custom exceptions

5. TESTS :
   - Stratégie de tests unitaires
   - Tests d'intégration prioritaires
   - Coverage cible : 80%

Propose une nouvelle structure de dossiers et le code de migration.
```

---

### 🧪 Question 8 : Tests & CI/CD

**Contexte à fournir :**
- `app.py`
- `.github/workflows/` (si existe)

**Prompt à utiliser :**

```
Expert DevOps Python, propose une stratégie de tests et CI/CD :

1. TESTS UNITAIRES :
   - Framework : pytest
   - 10 tests critiques à créer en priorité
   - Fixtures et mocks

2. TESTS D'INTÉGRATION :
   - Routes à tester avec Flask-Testing
   - Base de données de test
   - Upload de fichiers

3. CI/CD :
   - GitHub Actions workflow complet
   - Linting (flake8, black, mypy)
   - Tests automatiques
   - Déploiement automatique sur Render

4. MONITORING :
   - Sentry pour les erreurs
   - Uptime monitoring
   - Logs structurés
   - Alertes critiques

Fournis tous les fichiers de configuration prêts à l'emploi.
```

---

## Phase 5 : Fonctionnalités Avancées

### ✨ Question 9 : Nouvelles Fonctionnalités

**Prompt à utiliser :**

```
Product Manager technique, propose 10 fonctionnalités à forte valeur ajoutée :

1. SYSTÈME DE NOTATION :
   - Avis clients sur les spectacles
   - Modération automatique/manuelle
   - Affichage étoiles + verbatims

2. MESSAGERIE INTERNE :
   - Chat organisateur ↔ artiste
   - Notifications emails
   - Historique des échanges

3. CALENDRIER DE DISPONIBILITÉS :
   - Agenda des compagnies
   - Réservation de créneaux
   - Synchronisation Google Calendar

4. SYSTÈME DE DEVIS :
   - Génération automatique PDF
   - Signature électronique
   - Suivi des devis (envoyé, accepté, refusé)

5. DASHBOARD ANALYTICS :
   - Vues par spectacle
   - Taux de conversion
   - Demandes par région/catégorie
   - Export CSV

6. PROGRAMME DE FIDÉLITÉ :
   - Points pour les compagnies actives
   - Badges (vérifié, star, premium)
   - Visibilité augmentée

7. RECOMMANDATIONS IA :
   - "Spectacles similaires"
   - Matching intelligent demande ↔ spectacles
   - Prédiction du succès d'un spectacle

8. MULTI-LANGUES :
   - Français/Anglais
   - Flask-Babel
   - SEO international

9. PAIEMENT EN LIGNE :
   - Stripe integration
   - Acompte à la réservation
   - Commission plateforme

10. BLOG / CMS :
    - Articles SEO
    - Actualités secteur
    - Guides pratiques

Pour chaque fonctionnalité :
- Valeur business estimée
- Complexité technique (1-5)
- Code de base pour démarrer
```

---

## Contexte du Projet

### 📊 Informations à fournir systématiquement

```
STACK TECHNIQUE :
- Python 3.13 / Flask 3.x
- PostgreSQL (production) / SQLite (dev)
- SQLAlchemy ORM
- Jinja2 templates
- Flask-WTF (CSRF, forms)
- Flask-Mail (OVH SMTP)
- Hébergement : Render.com

STATISTIQUES :
- ~200 utilisateurs (compagnies)
- ~150 spectacles publiés
- ~50 appels d'offre/mois
- Traffic : ~1000 visiteurs/mois

OBJECTIFS BUSINESS :
1. Augmenter conversions +50%
2. SEO : Top 3 Google pour "spectacle + ville"
3. Réduire temps chargement < 1s
4. Atteindre 500 compagnies inscrites

CONTRAINTES :
- Budget limité (pas de services payants lourds)
- Équipe technique : 1 développeur
- Déploiement : Render (gratuit/starter plan)
```

---

## 📝 Méthodologie d'Utilisation

### Étape 1 : Prioriser
Commencez par les questions **Phase 1 et 2** (sécurité, performance, SEO).

### Étape 2 : Découper
Pour `app.py` (4600 lignes), soumettez par sections :
- Lignes 1-800 (imports, config, helpers)
- Lignes 800-1600 (auth, user management)
- Lignes 1600-2400 (spectacles, catalogue)
- Lignes 2400-3200 (appels d'offre)
- Lignes 3200-4000 (admin)
- Lignes 4000-4600 (routes SEO, utils)

### Étape 3 : Implémenter progressivement
Ne tentez pas tout en une fois. Ordre recommandé :
1. Sécurité critiques
2. Performance quick wins
3. SEO (Schema.org, sitemap)
4. UX formulaires
5. Refactoring
6. Nouvelles fonctionnalités

### Étape 4 : Tester
Après chaque modification :
```bash
python -m pytest
git commit -m "feat: [description]"
git push
```

---

## 🎯 Exemples de Questions de Suivi

Après la première analyse de Claude Opus 4, posez des questions plus précises :

```
"Tu as suggéré d'utiliser Redis pour le cache. 
Peux-tu me donner le code complet pour :
1. Configuration Flask-Caching
2. Décorateurs @cache sur les routes critiques
3. Invalidation du cache lors de modifications
4. Setup sur Render.com (Redis gratuit)"
```

```
"Tu as identifié une vulnérabilité XSS dans le formulaire d'upload.
Montre-moi exactement comment la corriger avec :
1. Validation côté serveur
2. Sanitization du contenu
3. Tests pour vérifier la correction"
```

---

## 📈 Suivi des Améliorations

Créez un tableau de bord pour suivre les implémentations :

| Phase | Question | Statut | Impact Mesuré | Date |
|-------|----------|--------|---------------|------|
| 1 | Sécurité | ✅ Fait | 0 vulnérabilité | 2026-04-13 |
| 1 | Performance | 🔄 En cours | -40% temps chargement | 2026-04-14 |
| 2 | SEO Audit | ⏳ À faire | - | - |
| 2 | Schema.org | ⏳ À faire | - | - |
| 3 | UX Formulaires | ⏳ À faire | - | - |

---

## 💡 Astuces pour Optimiser les Réponses

1. **Soyez précis** : "Analyse la sécurité de la route /submit" plutôt que "Analyse la sécurité"

2. **Donnez des contraintes** : "Code compatible Python 3.13, sans dépendances externes"

3. **Demandez du code** : "Fournis le code complet, pas seulement l'explication"

4. **Context first** : Toujours rappeler que c'est une app Flask en production

5. **Demandez des tests** : "Inclus aussi les tests unitaires pour cette fonction"

---

## 🚀 Résultat Attendu

Après avoir suivi ce guide avec Claude Opus 4, vous aurez :

✅ Une application **sécurisée** (0 vulnérabilité critique)  
✅ Des performances **optimales** (< 1s de chargement)  
✅ Un **SEO excellent** (Schema.org, sitemap, meta parfaits)  
✅ Une **UX fluide** (+50% conversion)  
✅ Du code **maintenable** (patterns, tests, documentation)  
✅ Une **roadmap** de fonctionnalités avancées

---

## 📞 Besoin d'Aide ?

- **GitHub Issues** : Pour bugs et features
- **Documentation Flask** : https://flask.palletsprojects.com/
- **SQLAlchemy** : https://docs.sqlalchemy.org/
- **SEO** : https://developers.google.com/search/docs

---

**Bonne analyse ! 🎉**

_Document créé le 12 avril 2026 pour Spectacle'ment Vôtre_
