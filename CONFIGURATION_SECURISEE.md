# 🔐 GUIDE DE CONFIGURATION SÉCURISÉE

## ⚠️ VARIABLES D'ENVIRONNEMENT OBLIGATOIRES

Après les corrections de sécurité du 3 janvier 2026, ces variables sont **OBLIGATOIRES** :

### 1. SECRET_KEY (CRITIQUE)
```bash
# Générer une clé secrète forte
python -c "import secrets; print(secrets.token_hex(32))"

# Dans .env ou Render
SECRET_KEY=votre_cle_generee_ici
```

### 2. ADMIN_PASSWORD (CRITIQUE)
```bash
# Mot de passe admin FORT (12+ caractères, majuscules, chiffres, symboles)
ADMIN_PASSWORD=VotreMotDePasseSecurise123!
```

### 3. MAIL_PASSWORD (CRITIQUE)
```bash
# Mot de passe du compte email
MAIL_PASSWORD=votre_mot_de_passe_email
```

---

## 📋 CONFIGURATION COMPLÈTE

### Fichier .env (Développement local)

Créer un fichier `.env` à la racine :

```bash
# === SÉCURITÉ (OBLIGATOIRE) ===
SECRET_KEY=<générer avec la commande ci-dessus>
ADMIN_PASSWORD=<mot de passe fort>

# === EMAIL (OBLIGATOIRE) ===
MAIL_SERVER=ssl0.ovh.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=contact@spectacleanimation.fr
MAIL_PASSWORD=<votre mot de passe email>
MAIL_DEFAULT_SENDER=contact@spectacleanimation.fr

# === ADMIN ===
ADMIN_USERNAME=admin

# === ENVIRONNEMENT ===
FLASK_ENV=development

# === BASE DE DONNÉES (optionnel en dev) ===
# DATABASE_URL=postgresql://user:password@localhost/dbname
```

### Variables Render (Production)

Dans le tableau de bord Render > Environment :

```
SECRET_KEY = <votre clé secrète>
ADMIN_PASSWORD = <votre mot de passe admin>
MAIL_PASSWORD = <votre mot de passe email>
FLASK_ENV = production

# Automatiquement fourni par Render :
DATABASE_URL = <fourni automatiquement>
PORT = <fourni automatiquement>
```

---

## 🚀 INSTALLATION

### 1. Cloner et installer les dépendances

```bash
cd flask-spectacles
pip install -r requirements.txt
```

### 2. Créer le fichier .env

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 3. Générer SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Copier le résultat dans .env
```

### 4. Lancer l'application

```bash
python app.py
```

---

## ✅ VÉRIFICATIONS

### L'application devrait :
- ✅ Démarrer sans erreur
- ✅ Afficher "Protection CSRF activée" dans les logs
- ✅ Afficher "Rate limiting activé" dans les logs
- ✅ Refuser de démarrer en production sans SECRET_KEY/ADMIN_PASSWORD

### Tester la protection CSRF :
1. Ouvrir un formulaire (ex: /login)
2. Inspecter le code source
3. Vérifier la présence de : `<input type="hidden" name="csrf_token" value="...">`

---

## 🔒 CHECKLIST SÉCURITÉ

Avant de déployer en production :

- [ ] SECRET_KEY définie et forte (64+ caractères hexadécimaux)
- [ ] ADMIN_PASSWORD défini et fort (12+ caractères variés)
- [ ] MAIL_PASSWORD défini
- [ ] Tous les formulaires ont un token CSRF
- [ ] Rate limiting activé
- [ ] FLASK_ENV=production sur Render
- [ ] HTTPS activé (automatique sur Render)
- [ ] Fichier .env dans .gitignore (ne JAMAIS commit)

---

## ⚠️ ERREURS COURANTES

### "SECRET_KEY is not set"
**Solution :** Définir SECRET_KEY dans .env ou variables d'environnement

### "ADMIN_PASSWORD is not set"
**Solution :** Définir ADMIN_PASSWORD dans .env

### "Validation errors. Vérifiez la configuration"
**Solution :** Vérifier les logs pour voir quelle variable manque

### "CSRF token missing"
**Solution :** Vider le cache du navigateur ou se déconnecter/reconnecter

---

## 📞 SUPPORT

En cas de problème :
1. Vérifier les logs : `logs/flask-spectacles.log`
2. Vérifier la console de démarrage
3. S'assurer que toutes les variables obligatoires sont définies

---

**Dernière mise à jour : 3 janvier 2026**
