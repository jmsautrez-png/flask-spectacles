# 📧 Configuration des emails pour recevoir les notifications

## ❌ Problème
L'admin ne reçoit pas d'email lors de :
- L'inscription d'un nouvel utilisateur
- La publication d'un nouveau spectacle

## 🔍 Diagnostic

Les logs de l'application montrent maintenant pourquoi les emails ne sont pas envoyés :
- `[MAIL] ⚠ Flask-Mail non initialisé`
- `[MAIL] ⚠ MAIL_USERNAME non défini`
- `[MAIL] ⚠ MAIL_PASSWORD non défini`

## ✅ Solution : Configurer les variables d'environnement sur Render

### Étape 1 : Accéder aux variables d'environnement

1. Aller sur https://dashboard.render.com
2. Sélectionner votre service web
3. Cliquer sur **"Environment"** dans le menu de gauche

### Étape 2 : Ajouter les variables d'environnement email

Ajouter les variables suivantes (cliquer sur "Add Environment Variable" pour chacune) :

```
MAIL_SERVER=ssl0.ovh.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=contact@spectacleanimation.fr
MAIL_PASSWORD=votre_mot_de_passe_email_ici
MAIL_DEFAULT_SENDER=contact@spectacleanimation.fr
```

**⚠️ Important :** 
- Remplacez `votre_mot_de_passe_email_ici` par le vrai mot de passe de votre compte email OVH
- Ne partagez JAMAIS ce mot de passe publiquement
- Le mot de passe doit être celui du compte `contact@spectacleanimation.fr`

### Étape 3 : Redémarrer le service

Après avoir ajouté toutes les variables :
1. Cliquer sur "Save Changes" en haut de la page
2. Le service va automatiquement redémarrer
3. Les emails devraient maintenant fonctionner

## 📊 Vérification

Une fois configuré, vous pouvez vérifier dans les logs Render :

✅ **Succès** :
```
[MAIL] ✓ Email envoyé à l'admin pour inscription de nom_utilisateur
[MAIL] ✓ Email de bienvenue envoyé à email@example.com
[MAIL] ✓ Email envoyé à l'admin pour nouvelle annonce: Titre du spectacle
```

❌ **Échec** (si les variables ne sont pas configurées) :
```
[MAIL] ⚠ MAIL_PASSWORD non défini
[MAIL] ⚠ Flask-Mail non initialisé
```

## 🔐 Sécurité

Les variables d'environnement sur Render sont :
- ✅ Chiffrées et sécurisées
- ✅ Non visibles dans le code source
- ✅ Non commitées dans Git
- ✅ Accessibles uniquement par l'application en production

## 📧 Emails envoyés automatiquement

Une fois configuré, l'admin recevra un email à `contact@spectacleanimation.fr` pour :

1. **Inscription d'un nouvel utilisateur**
   - Sujet : "Nouvelle inscription utilisateur"
   - Contenu : Nom, email, téléphone, raison sociale, région, site internet

2. **Publication d'un nouveau spectacle**
   - Sujet : "🎭 Nouvelle annonce à valider"
   - Contenu : Compagnie, titre, lieu, catégorie, date, email, téléphone

3. **Utilisateur inscrit** (email de bienvenue)
   - Sujet : "Bienvenue sur Spectacle'ment VØtre !"
   - Envoyé à l'email de l'utilisateur qui vient de s'inscrire

## 🧪 Test en local

Pour tester en local, créez un fichier `.env` à la racine du projet :

```env
MAIL_SERVER=ssl0.ovh.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=contact@spectacleanimation.fr
MAIL_PASSWORD=votre_mot_de_passe_ici
MAIL_DEFAULT_SENDER=contact@spectacleanimation.fr
```

⚠️ **Important** : Le fichier `.env` est dans `.gitignore` et ne sera jamais commité.

## 🆘 Problèmes courants

### 1. "Authentication failed" dans les logs
- ❌ Le mot de passe est incorrect
- ✅ Vérifier le mot de passe du compte email OVH

### 2. "Connection refused"
- ❌ Le serveur SMTP ou le port est incorrect
- ✅ Vérifier MAIL_SERVER=ssl0.ovh.net et MAIL_PORT=587

### 3. Les emails ne partent toujours pas
- ❌ MAIL_PASSWORD n'est pas défini dans Render
- ✅ Vérifier que TOUTES les variables sont bien ajoutées
- ✅ Redémarrer le service après modification

## 📝 Logs améliorés

J'ai ajouté des logs détaillés pour faciliter le diagnostic :
- ✅ Confirmation d'envoi avec le nom du destinataire
- ⚠️ Avertissement si une variable manque (quelle variable)
- ❌ Message d'erreur détaillé en cas de problème SMTP

Consultez les logs Render pour voir exactement ce qui se passe !
