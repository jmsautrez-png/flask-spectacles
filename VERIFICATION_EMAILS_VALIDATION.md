# VÉRIFICATION DES EMAILS DE VALIDATION

## 🔍 Pour savoir si l'utilisatrice a reçu l'email :

### Option 1 : Vérifier les logs Render
1. Allez sur https://dashboard.render.com
2. Cliquez sur votre service `flask-spectacles`
3. Onglet **Logs**
4. Cherchez `[MAIL]` dans les logs récents
5. Si vous voyez :
   - `[MAIL] ✓ Email envoyé à...` → Email bien envoyé ✅
   - `[MAIL] ✗ Envoi impossible` → Erreur d'envoi ❌
   - `[MAIL] ⚠ MAIL_PASSWORD non défini` → MAIL_PASSWORD manquant ⚠️

### Option 2 : Vérifier la configuration MAIL_PASSWORD
1. Dashboard Render → Service `flask-spectacles`
2. Onglet **Environment**
3. Cherchez la variable `MAIL_PASSWORD`
4. Si elle n'existe pas : **les emails ne sont pas envoyés**

## ✅ Si MAIL_PASSWORD est bien configuré

L'email a été envoyé à l'adresse email de la compagnie avec :
- **Sujet :** "Votre spectacle est validé sur Spectacle'ment VØtre !"
- **Contenu :** Lien vers le spectacle + détails + présentation des services

## 🔧 Si MAIL_PASSWORD n'est PAS configuré

### Étapes pour activer les emails :

1. **Récupérez le mot de passe** de votre compte email OVH (contact@spectacleanimation.fr)

2. **Sur Render Dashboard :**
   - Settings → Environment
   - Add Environment Variable
   - Key: `MAIL_PASSWORD`
   - Value: [Votre mot de passe email OVH]
   - Save Changes

3. **Redémarrer le service** (automatique après Save Changes)

4. **Les prochaines validations** enverront automatiquement les emails

## 📧 Pour renvoyer l'email manuellement

Si l'utilisatrice n'a pas reçu l'email, vous pouvez :
1. Dé-valider le spectacle (cliquez à nouveau sur le bouton de validation)
2. Re-valider le spectacle
3. L'email sera renvoyé automatiquement

---

**Résumé :** Le code fonctionne, il suffit que MAIL_PASSWORD soit configuré sur Render.
