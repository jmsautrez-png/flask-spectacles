# 🧪 Guide de Test en Local - Appels d'Offre

## 📋 Prérequis

Votre fichier `.env` est déjà configuré avec l'email OVH. **Deux options** pour les tests :

### Option A : Recevoir les emails sur VOTRE adresse Gmail

Modifiez `.env` temporairement :
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=VOTRE-EMAIL@gmail.com
MAIL_PASSWORD=VOTRE-MOT-DE-PASSE-APPLICATION
MAIL_DEFAULT_SENDER=VOTRE-EMAIL@gmail.com
```

> **Note** : Pour créer un mot de passe d'application Gmail :
> 1. https://myaccount.google.com/security
> 2. Activez la validation en 2 étapes
> 3. "Mots de passe des applications" → Mail → Windows
> 4. Copiez le mot de passe généré

### Option B : Garder l'email OVH (par défaut)

Utilisez directement contact@spectacleanimation.fr (déjà configuré)

---

## 🚀 Procédure de Test Complète

### 1️⃣ Créer un utilisateur test

```bash
python test_simulation_utilisateur.py VOTRE-EMAIL@gmail.com
```

**Ce script va :**
- Créer un utilisateur avec votre email
- Créer un spectacle "Magie" approuvé dans la région "Île-de-France"
- Afficher les stats

### 2️⃣ Créer un appel d'offre de test

```bash
python test_creer_appel_offre.py
```

**Ce script va :**
- Créer un appel d'offre public et approuvé
- Genre : "Magie"
- Région : "Île-de-France"

### 3️⃣ Lancer l'application

```bash
python app.py
```

Ouvrez votre navigateur : http://localhost:5000

### 4️⃣ Tester en tant qu'ADMIN

**Connexion :**
- URL : http://localhost:5000/login
- Username : `admin`
- Password : `Mael,2012` (défini dans votre .env)

**Actions admin :**

1. **Voir tous les appels d'offre**
   - Menu : Admin > Appels d'offre
   - URL : http://localhost:5000/admin/demandes-animation

2. **Envoyer un appel d'offre**
   - Cliquez sur "📧 Envoyer" à côté d'un appel
   - Sélectionnez catégories : "Magie"
   - Sélectionnez régions : "Île-de-France"
   - Cliquez "Prévisualiser les destinataires"

3. **Prévisualiser les destinataires**
   - Vous verrez la liste des utilisateurs qui vont recevoir l'email
   - Votre utilisateur test doit apparaître
   - Décochez ceux que vous ne voulez pas
   - Cliquez "Envoyer définitivement (X emails)"

4. **Vérifier votre boîte email**
   - L'email devrait arriver sur VOTRE-EMAIL@gmail.com
   - Ou sur contact@spectacleanimation.fr si vous utilisez l'Option B

### 5️⃣ Tester en tant qu'UTILISATEUR

**Connexion en tant qu'utilisateur test :**
- Username : `test_XXXXXX` (affiché par le script)
- Password : `test123`

**Actions utilisateur :**

1. **Voir les appels d'offre**
   - URL : http://localhost:5000/mes-appels-offres
   - ✅ Avec spectacle approuvé → Accès complet
   - ❌ Sans spectacle approuvé → Redirigé avec message

2. **Page publique avec masquage**
   - URL : http://localhost:5000/demandes-animation
   - Déconnectez-vous
   - Ville et carte doivent être masquées/floutées
   - Contact masqué avec lien "Publier votre manifestation..."

---

## 🧪 Tests de Sécurité à Valider

### Test 1 : Utilisateur SANS spectacle ne reçoit PAS d'email

```bash
# Supprimer le spectacle de l'utilisateur test
python -c "from app import create_app; from models.models import db, Show, User; app = create_app(); app.app_context().push(); user = User.query.filter_by(email='VOTRE-EMAIL@gmail.com').first(); Show.query.filter_by(user_id=user.id).delete(); db.session.commit(); print('✅ Spectacle supprimé')"

# Envoyer un appel d'offre depuis l'interface admin
# → L'utilisateur ne doit PAS apparaître dans la prévisualisation
```

### Test 2 : Utilisateur SANS spectacle ne peut PAS voir /mes-appels-offres

```bash
# Connectez-vous avec le compte test (sans spectacle)
# Allez sur http://localhost:5000/mes-appels-offres
# → Doit rediriger vers /espace-perso avec message d'erreur
```

### Test 3 : Visiteur non connecté voit infos masquées

```bash
# Déconnectez-vous
# Allez sur http://localhost:5000/demandes-animation
# → Ville masquée avec lien "Publier votre manifestation..."
# → Carte floutée avec message "Localisation disponible après publication"
# → Contact masqué
```

---

## 📊 Vérifier la Configuration Email

```bash
python test_email_config.py
```

**Ce script affiche :**
- Configuration Flask-Mail
- Email admin configuré
- Statistiques appels d'offre

---

## 🔄 Réinitialiser les Données de Test

```bash
# Supprimer tous les utilisateurs test
python -c "from app import create_app; from models.models import db, User; app = create_app(); app.app_context().push(); User.query.filter(User.username.like('test_%')).delete(); db.session.commit(); print('✅ Utilisateurs test supprimés')"

# Supprimer tous les appels d'offre
python -c "from app import create_app; from models.models import db, DemandeAnimation; app = create_app(); app.app_context().push(); DemandeAnimation.query.delete(); db.session.commit(); print('✅ Appels d\\'offre supprimés')"
```

---

## 📝 Résumé des Protections Implémentées

### ✅ Protection Email (app.py ligne 3936)
```python
additional_users = UserModel.query.join(Show).filter(
    UserModel.email.isnot(None),
    or_(*user_region_filters),
    Show.approved.is_(True)  # REQUIS : spectacle approuvé
).distinct().all()
```

### ✅ Protection Page Web (app.py ligne 3470)
```python
has_approved_show = Show.query.filter(
    Show.user_id == user.id,
    Show.approved.is_(True)
).count() > 0

if not has_approved_show and not user.is_admin:
    flash("Vous devez avoir un spectacle approuvé...", "warning")
    return redirect(url_for("espace_perso"))
```

### ✅ Protection Affichage Public (templates/demandes_animation.html)
- Ville masquée pour non-connectés
- Carte floutée + message overlay
- Contact masqué avec lien inscription

---

## 🐛 Dépannage

### Les emails n'arrivent pas ?

1. Vérifiez `.env` : MAIL_USERNAME et MAIL_PASSWORD corrects
2. Gmail : Vérifiez que vous utilisez un mot de passe d'application
3. OVH : Vérifiez que le compte est actif

### L'utilisateur test n'apparaît pas dans la prévisualisation ?

1. Vérifiez que le spectacle est approuvé : `Show.approved = True`
2. Vérifiez que la catégorie correspond : "Magie" dans les deux
3. Vérifiez que la région correspond : "Île-de-France"

### Erreur "Aucun spectacle approuvé" ?

C'est normal ! La protection fonctionne. Créez un spectacle avec :
```bash
python test_simulation_utilisateur.py VOTRE-EMAIL@gmail.com
```

---

## 📞 Commits Récents

- `dd7fbdb` : Fix email - Seuls utilisateurs avec spectacle approuvé reçoivent emails
- `f9ceba5` : Fix page web - Bloquer accès /mes-appels-offres sans spectacle
- `50fdbee` : Fix template - Masquer ville et carte pour non-connectés

**Statut** : ✅ Tous les tests de sécurité passent
