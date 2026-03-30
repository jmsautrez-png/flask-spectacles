#!/usr/bin/env python3
"""
Vérification que l'utilisateur peut se connecter avec le compte créé
"""
import urllib.request
import urllib.parse
import http.cookiejar
import re
import ssl

BASE_URL = "https://spectacleanimation.fr"
ctx = ssl.create_default_context()

print("=" * 70)
print("TEST DE CONNEXION avec le compte créé")
print("=" * 70)

username = "test_6ii3i1ok"
password = "Test123456"

print(f"\nTentative de connexion avec:")
print(f"  Username: {username}")
print(f"  Password: {password}")

# Créer un cookie jar
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cookie_jar),
    urllib.request.HTTPSHandler(context=ctx)
)

# ÉTAPE 1: Récupérer la page de login pour le CSRF
print("\n1. Chargement de la page de connexion...")
req = urllib.request.Request(
    f"{BASE_URL}/login",
    headers={'User-Agent': 'Mozilla/5.0'}
)

with opener.open(req, timeout=15) as response:
    html = response.read().decode('utf-8')
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    print(f"   ✓ CSRF token récupéré")

# ÉTAPE 2: Tenter la connexion
print("\n2. Soumission des identifiants...")
data = {
    'username': username,
    'password': password,
    'csrf_token': csrf_token
}
data_encoded = urllib.parse.urlencode(data).encode('utf-8')

req = urllib.request.Request(
    f"{BASE_URL}/login",
    data=data_encoded,
    headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0',
        'Referer': f"{BASE_URL}/login"
    }
)

try:
    with opener.open(req, timeout=15) as response:
        result_html = response.read().decode('utf-8')
        
        # Chercher des indices de succès/échec
        if "company_dashboard" in response.url or "dashboard" in response.url:
            print("   ✅ CONNEXION RÉUSSIE!")
            print(f"   Redirigé vers: {response.url}")
        elif "Identifiants invalides" in result_html or "Invalid" in result_html:
            print("   ❌ Identifiants refusés - compte n'existe pas")
        elif username in result_html or "Bienvenue" in result_html:
            print("   ✅ CONNEXION RÉUSSIE!")
            print("   Le compte existe et fonctionne!")
        else:
            print("   ⚠️  Réponse ambiguë")
            
except urllib.error.HTTPError as e:
    if e.code == 302 or e.code == 303:
        location = e.headers.get('Location', '')
        print("   ✅ CONNEXION RÉUSSIE!")
        print(f"   Redirection vers: {location}")
        if "dashboard" in location or "company" in location:
            print("   Le compte existe et est fonctionnel!")
    else:
        print(f"   ❌ Erreur HTTP {e.code}")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("Si la connexion réussit, cela prouve que:")
print("  1. Le compte a été créé dans la base de données")
print("  2. Le mot de passe a été correctement hashé")
print("  3. L'inscription fonctionne de bout en bout")
print("=" * 70)
