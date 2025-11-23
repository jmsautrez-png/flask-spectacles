# AnimatoSpectacle — Pack complet (Windows)

## Lancer
1) Double‑cliquez **start.bat** (Windows).
2) La 1re fois, ça installe automatiquement l’environnement puis les dépendances.
3) Le site s’ouvre sur http://127.0.0.1:5000

Identifiants admin par défaut (modifiable via variables d’environnement) :
- USER : admin
- PASS : admin

## Scripts utiles
- **start.bat** : lance (et installe au besoin) puis démarre le site
- **reset_db.bat** : réinitialise la base `instance\app.db` (supprime puis se recrée au prochain lancement)

## Email automatique (facultatif)
Si vous voulez recevoir un email à chaque annonce :
1. Activez un **mot de passe d’application Gmail**
2. Ouvrez PowerShell (normal), puis :
   setx MAIL_USERNAME "votre@gmail.com"
   setx MAIL_PASSWORD "MOT_DE_PASSE_APPLICATION"
   setx MAIL_DEFAULT_SENDER "votre@gmail.com"
3. Relancez `start.bat`.

Bon usage !
