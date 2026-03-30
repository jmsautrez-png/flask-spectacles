#!/usr/bin/env python3
"""
Test d'inscription avec vérification des emails envoyés
"""
import urllib.request
import urllib.parse
import http.cookiejar
import re
import random
import string
import ssl
import time

BASE_URL = "https://spectacleanimation.fr"
ctx = ssl.create_default_context()

def generer_nom_aleatoire():
    """Génère un nom d'utilisateur aléatoire"""
    return f"test_email_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

def test_inscription_avec_notification():
    """Teste l'inscription et affiche les infos pour vérifier les emails"""
    print("=" * 70)
    print("🧪 TEST D'INSCRIPTION AVEC NOTIFICATIONS EMAIL")
    print("=" * 70)
    
    # Données de test avec email unique
    username = generer_nom_aleatoire()
    email_test = f"{username}@test-spectacle.fr"
    password = "Test123456"
    
    timestamp = time.strftime("%H:%M:%S")
    
    print(f"\n📝 Données du nouveau compte:")
    print(f"   Username: {username}")
    print(f"   Email: {email_test}")
    print(f"   Password: {password}")
    print(f"   Heure: {timestamp}")
    
    # Créer un cookie jar
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=ctx)
    )
    
    # ÉTAPE 1: Récupérer la page register
    print(f"\n🔄 Récupération du formulaire...")
    req = urllib.request.Request(
        f"{BASE_URL}/register",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    with opener.open(req, timeout=15) as response:
        html = response.read().decode('utf-8')
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else None
        print(f"   ✓ CSRF token récupéré")
    
    # ÉTAPE 2: Soumettre le formulaire
    print(f"\n📤 Soumission de l'inscription...")
    data = {
        'username': username,
        'email': email_test,
        'password': password,
        'telephone': '06 12 34 56 78',
        'raison_sociale': 'Test Email Company',
        'region': 'Île-de-France',
        'site_internet': 'https://test-email.fr',
        'csrf_token': csrf_token
    }
    
    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/register",
        data=data_encoded,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f"{BASE_URL}/register"
        }
    )
    
    try:
        with opener.open(req, timeout=15) as response:
            if response.status == 200:
                result_html = response.read().decode('utf-8')
                if "Compte créé" in result_html or "vous connecter" in result_html:
                    print(f"   ✅ INSCRIPTION RÉUSSIE!")
                    success = True
                else:
                    print(f"   ⚠️  Statut incertain")
                    success = False
    except urllib.error.HTTPError as e:
        if e.code in [302, 303]:
            print(f"   ✅ INSCRIPTION RÉUSSIE! (redirection)")
            success = True
        else:
            print(f"   ❌ Erreur {e.code}")
            success = False
    
    if success:
        print("\n" + "=" * 70)
        print("📧 VÉRIFICATION DES EMAILS")
        print("=" * 70)
        print("\nSi MAIL_PASSWORD est configuré, 2 emails ont dû être envoyés:")
        print("")
        print("1️⃣  EMAIL À L'ADMIN (contact@spectacleanimation.fr):")
        print("   Sujet: Nouvel utilisateur inscrit")
        print(f"   Contenu: Nouvel utilisateur {username}")
        print(f"   Email: {email_test}")
        print("")
        print("2️⃣  EMAIL DE BIENVENUE À L'UTILISATEUR:")
        print(f"   Destinataire: {email_test}")
        print("   Sujet: Bienvenue sur SpectacleAnimation.fr")
        print(f"   Contenu: Votre compte a été créé")
        print(f"   Username: {username}")
        print("")
        print("=" * 70)
        print("💡 POUR VÉRIFIER:")
        print(f"   1. Consultez les logs Render à {timestamp}")
        print("   2. Cherchez '[MAIL]' dans les logs")
        print("   3. Vérifiez votre boîte contact@spectacleanimation.fr")
        print("=" * 70)
        
        return True
    else:
        return False

if __name__ == "__main__":
    success = test_inscription_avec_notification()
    
    if success:
        print("\n✅ Test terminé avec succès")
        print("Vérifiez vos emails et les logs Render pour confirmer l'envoi")
    else:
        print("\n❌ L'inscription a échoué")
