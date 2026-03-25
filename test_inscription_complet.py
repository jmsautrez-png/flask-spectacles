#!/usr/bin/env python3
"""
Test d'inscription complet avec gestion du CSRF token
Simule un vrai navigateur pour tester l'inscription sur spectacleanimation.fr
"""
import urllib.request
import urllib.parse
import http.cookiejar
import re
import random
import string
import ssl

# URL de production
BASE_URL = "https://spectacleanimation.fr"

# Créer un contexte SSL
ctx = ssl.create_default_context()

def generer_nom_aleatoire():
    """Génère un nom d'utilisateur aléatoire"""
    return f"test_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"

def test_inscription_complet():
    """Teste l'inscription avec gestion complète des cookies et CSRF"""
    print("=" * 70)
    print("🧪 TEST D'INSCRIPTION COMPLET (avec CSRF)")
    print("=" * 70)
    
    # Données de test
    username = generer_nom_aleatoire()
    email = f"{username}@test-spectacle.fr"
    password = "Test123456"
    
    print(f"\n📝 Données de test:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    
    # Créer un cookie jar pour maintenir la session
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=ctx)
    )
    
    # ÉTAPE 1: Récupérer la page register pour obtenir le CSRF token
    print(f"\n🔄 Étape 1: Récupération du formulaire d'inscription...")
    print(f"   URL: {BASE_URL}/register")
    
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/register",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        with opener.open(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            print(f"   ✓ Page chargée ({len(html)} caractères)")
            
            # Extraire le CSRF token avec une regex
            csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"   ✓ CSRF token trouvé: {csrf_token[:20]}...")
            else:
                print(f"   ⚠️  Aucun CSRF token trouvé dans le HTML")
                csrf_token = None
            
            # Afficher les cookies reçus
            print(f"   ✓ Cookies de session: {len(cookie_jar)} cookie(s)")
            for cookie in cookie_jar:
                print(f"      - {cookie.name}: {cookie.value[:20]}...")
    
    except Exception as e:
        print(f"   ❌ Erreur lors du chargement: {e}")
        return False
    
    # ÉTAPE 2: Soumettre le formulaire avec le CSRF token
    print(f"\n🔄 Étape 2: Soumission du formulaire d'inscription...")
    
    # Préparer les données
    data = {
        'username': username,
        'email': email,
        'password': password,
        'telephone': '06 12 34 56 78',
        'raison_sociale': 'Compagnie Test',
        'region': 'Île-de-France',
        'site_internet': 'https://test.fr'
    }
    
    if csrf_token:
        data['csrf_token'] = csrf_token
    
    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/register",
            data=data_encoded,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': f"{BASE_URL}/register"
            }
        )
        
        # Ne pas suivre automatiquement les redirections
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl):
                return None
        
        opener.add_handler(NoRedirect())
        
        try:
            with opener.open(req, timeout=15) as response:
                status_code = response.status
                response_text = response.read().decode('utf-8')
                
                print(f"   Status: {status_code}")
                
                if status_code == 200:
                    # Page rechargée - chercher les messages
                    if "Compte créé" in response_text or "vous connecter" in response_text:
                        print(f"   ✅ INSCRIPTION RÉUSSIE!")
                        print(f"   Message de succès détecté dans la réponse")
                        return True
                    elif "existe déjà" in response_text:
                        print(f"   ⚠️  Le nom d'utilisateur ou l'email existe déjà")
                        print(f"   (Normal si le test a déjà été exécuté)")
                        return False
                    elif "Erreur lors de la création" in response_text:
                        print(f"   ❌ Erreur lors de la création du compte")
                        # Chercher plus de détails
                        if "site_internet" in response_text.lower():
                            print(f"   💡 Problème lié à 'site_internet' détecté")
                        return False
                    else:
                        print(f"   ⚠️  Réponse reçue sans message clair")
                        # Afficher un extrait
                        extract = response_text[response_text.find('<body'):response_text.find('</body')][:500] if '<body' in response_text else response_text[:500]
                        print(f"   Extrait: {extract[:200]}...")
                        return False
                else:
                    print(f"   ❌ Status inattendu: {status_code}")
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 302 or e.code == 303:
                # Redirection = succès!
                location = e.headers.get('Location', '')
                print(f"   ✅ INSCRIPTION RÉUSSIE!")
                print(f"   Redirection ({e.code}) vers: {location}")
                return True
            elif e.code == 500:
                print(f"   ❌ ERREUR 500: Erreur serveur!")
                try:
                    error_text = e.read().decode('utf-8')
                    if "site_internet" in error_text:
                        print(f"   💡 Le problème est lié à la colonne 'site_internet'")
                    # Chercher le message d'erreur
                    if "Traceback" in error_text or "Error" in error_text:
                        lines = error_text.split('\n')
                        for line in lines:
                            if 'Error' in line or 'Exception' in line:
                                print(f"   📋 {line.strip()}")
                except:
                    pass
                return False
            else:
                print(f"   ❌ Erreur HTTP {e.code}: {e.reason}")
                return False
                
    except Exception as e:
        print(f"   ❌ Erreur lors de la soumission: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_inscription_complet()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ TEST RÉUSSI - L'inscription fonctionne!")
        print("=" * 70)
        print("\n💡 Julie peut maintenant créer son compte sans problème")
    else:
        print("❌ TEST ÉCHOUÉ")
        print("=" * 70)
        print("\n💡 Consultez les logs Render pour plus de détails")
    
    print("\n📊 Résumé:")
    print(f"   URL testée: {BASE_URL}/register")
    print(f"   Résultat: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
