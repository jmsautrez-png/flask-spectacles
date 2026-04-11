## 🔧 RÉSOLUTION ERREUR SMTP OVH - Authentication Failed

### Erreur rencontrée :
```
(535, b'5.7.1 Authentication failed')
```

### 🎯 Solutions à essayer dans l'ordre :

---

## Solution 1️⃣ : Vérifier les paramètres SMTP OVH

OVH utilise des serveurs SMTP différents selon le type de compte :

**Pour OVH Mail (MX Plan) :**
```env
MAIL_SERVER=ssl0.ovh.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=contact@spectacleanimation.fr
MAIL_PASSWORD=votre_mot_de_passe
```

**OU pour certains comptes OVH :**
```env
MAIL_SERVER=pro1.mail.ovh.net
MAIL_PORT=587
MAIL_USE_TLS=True
```

**OU en SSL :**
```env
MAIL_SERVER=ssl0.ovh.net
MAIL_PORT=465
MAIL_USE_TLS=False
MAIL_USE_SSL=True
```

---

## Solution 2️⃣ : Vérifier le mot de passe

1. **Connectez-vous au Webmail OVH** : https://www.ovh.com/fr/mail/
   - Email : contact@spectacleanimation.fr
   - Mot de passe : (votre mot de passe actuel)

2. **Si la connexion fonctionne**, le mot de passe est correct
3. **Si la connexion échoue**, réinitialisez le mot de passe :
   - Allez sur Manager OVH : https://www.ovh.com/manager/
   - Section "E-mails" → Sélectionner le compte
   - "Modifier le mot de passe"

---

## Solution 3️⃣ : Activer l'authentification SMTP dans OVH

1. Connectez-vous au **Manager OVH**
2. Allez dans **Web Cloud** → **E-mails**
3. Sélectionnez votre domaine **spectacleanimation.fr**
4. Cliquez sur le compte **contact@spectacleanimation.fr**
5. Vérifiez que **SMTP** est bien activé

---

## Solution 4️⃣ : Créer un mot de passe d'application (si activé)

Si OVH a activé la double authentification :

1. Manager OVH → Compte email
2. Créer un "mot de passe d'application" spécifique pour SMTP
3. Utiliser ce mot de passe dans `.env` au lieu du mot de passe principal

---

## Solution 5️⃣ : Tester avec un autre serveur SMTP

**Option Gmail (pour test) :**
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=votre.email@gmail.com
MAIL_PASSWORD=mot_de_passe_application_gmail
```

**Note Gmail :** Nécessite un "mot de passe d'application" si 2FA activé

---

## 🧪 Test rapide de configuration SMTP

### Vérification 1 : Fichier .env

Vérifiez que votre fichier `.env` contient :
```env
MAIL_SERVER=ssl0.ovh.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=contact@spectacleanimation.fr
MAIL_PASSWORD=VOTRE_VRAI_MOT_DE_PASSE_ICI
MAIL_DEFAULT_SENDER=contact@spectacleanimation.fr
```

⚠️ **ATTENTION** : 
- Pas d'espace autour du `=`
- Pas de guillemets autour des valeurs
- Mot de passe sans espaces

### Vérification 2 : Test manuel Python

Créez un fichier `test_smtp_direct.py` :

```python
import smtplib
from email.mime.text import MIMEText

# Paramètres à tester
SMTP_SERVER = "ssl0.ovh.net"
SMTP_PORT = 587
USERNAME = "contact@spectacleanimation.fr"
PASSWORD = "VOTRE_MOT_DE_PASSE"

try:
    print(f"Connexion à {SMTP_SERVER}:{SMTP_PORT}...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    print("TLS activé...")
    
    print(f"Authentification avec {USERNAME}...")
    server.login(USERNAME, PASSWORD)
    print("✅ AUTHENTIFICATION RÉUSSIE !")
    
    server.quit()
except Exception as e:
    print(f"❌ ERREUR : {e}")
```

---

## 📞 Contact Support OVH

Si rien ne fonctionne :
- Support OVH : https://www.ovh.com/fr/support/
- Téléphone : 1007 (depuis la France)
- Demandez pourquoi l'authentification SMTP échoue pour contact@spectacleanimation.fr

---

## 🔄 Après correction

1. Mettez à jour le fichier `.env` avec les bons paramètres
2. Redémarrez l'application
3. Testez à nouveau avec : `python test_send_email.py`
