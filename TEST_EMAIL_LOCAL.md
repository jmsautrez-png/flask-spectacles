# Test des Emails en Local

## Problème
En environnement local, les emails ne sont pas envoyés car `MAIL_PASSWORD` n'est pas configuré.

## Solutions pour tester

### Option 1 : Utiliser Mailtrap (Recommandé pour le développement)

1. Créez un compte gratuit sur https://mailtrap.io
2. Créez un fichier `.env` à la racine du projet avec :

```bash
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=votre_username_mailtrap
MAIL_PASSWORD=votre_password_mailtrap
MAIL_DEFAULT_SENDER=contact@spectacleanimation.fr
```

3. Les emails seront capturés par Mailtrap et visibles dans leur interface

### Option 2 : Serveur SMTP Local (Simple)

Lancez un serveur SMTP de debug Python :

```bash
python -m smtpd -n -c DebuggingServer localhost:1025
```

Puis dans `.env` :
```bash
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USE_SSL=False
MAIL_USERNAME=""
MAIL_PASSWORD=""
MAIL_DEFAULT_SENDER=contact@spectacleanimation.fr
```

Les emails s'afficheront dans le terminal du serveur SMTP.

### Option 3 : Créer un fichier .env

Créez dans le dossier `flask-spectacles` un fichier `.env` :

```bash
# Configuration Email pour tests locaux
MAIL_SERVER=ssl0.ovh.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=contact@spectacleanimation.fr
MAIL_PASSWORD=votre_mot_de_passe_email
MAIL_DEFAULT_SENDER=contact@spectacleanimation.fr
```

⚠️ **IMPORTANT** : N'oubliez pas d'ajouter `.env` dans `.gitignore` !

## Vérification

Après configuration, visitez : http://127.0.0.1:5000/test-mail

Vous devriez voir un message de succès et recevoir un email de test.

## Logs à vérifier

Dans le terminal de Flask, cherchez :
- `[MAIL] ✓ Email envoyé...` = succès
- `[MAIL] ✗ Envoi impossible` = échec
- `[MAIL] ⚠ Flask-Mail non initialisé` = configuration manquante
