#!/usr/bin/env python3
"""
Script de test pour simuler une inscription sur le site en production
Usage: python test_inscription.py
"""
import urllib.request
import urllib.parse
import json
import random
import string
import ssl

# URL de production
BASE_URL = "https://spectacleanimation.fr"
# BASE_URL = "http://127.0.0.1:5000"  # Test en local

# Créer un contexte SSL qui ne vérifie pas les certificats (pour les tests)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def generer_nom_aleatoire():
    """Génère un nom d'utilisateur aléatoire"""
    return f"test_user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"

def test_inscription():
    """Teste l'inscription d'un nouvel utilisateur"""
    print("=" * 60)
    print("🧪 TEST D'INSCRIPTION")
    print("=" * 60)
    
    # Données de test
    username = generer_nom_aleatoire()
    email = f"{username}@test-spectacle.fr"
    password = "Test123456"
    
    print(f"\n📝 Données de test:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   Téléphone: 06 12 34 56 78")
    print(f"   Raison sociale: Compagnie Test")
    print(f"   Région: Île-de-France")
    print(f"   Site internet: https://test.fr")
    
    # Test d'inscription avec urllib
    print(f"\n🔄 Tentative d'inscription sur {BASE_URL}/register...")
    
    try:
        # Préparer les données POST
        data = {
            'username': username,
            'email': email,
            'password': password,
            'telephone': '06 12 34 56 78',
            'raison_sociale': 'Compagnie Test',
            'region': 'Île-de-France',
            'site_internet': 'https://test.fr'
        }
        
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        
        # Créer la requête
        req = urllib.request.Request(
            f"{BASE_URL}/register",
            data=data_encoded,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Test Script)'
            }
        )
        
        # Envoyer la requête
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                status_code = response.status
                response_text = response.read().decode('utf-8')
                
                print(f"   Status: {status_code}")
                
                if status_code == 200:
                    # Succès - vérifier le contenu
                    if "Compte créé" in response_text or "vous connecter" in response_text.lower():
                        print(f"   ✅ INSCRIPTION RÉUSSIE!")
                        return True
                    else:
                        print(f"   ⚠️  Réponse reçue mais message de succès non détecté")
                        # Afficher un extrait
                        if "Ce nom d'utilisateur existe déjà" in response_text:
                            print(f"   ℹ️  Le nom d'utilisateur existe déjà (normal si test répété)")
                        return False
                else:
                    print(f"   ❌ Status inattendu: {status_code}")
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 302:  # Redirection = succès normalement
                print(f"   ✅ INSCRIPTION RÉUSSIE! (redirection {e.code})")
                location = e.headers.get('Location', '')
                print(f"   Redirection vers: {location}")
                return True
            elif e.code == 500:
                print(f"   ❌ ERREUR 500: Erreur serveur!")
                print(f"   Le bug 'site_internet' persiste!")
                return False
            else:
                print(f"   ❌ Erreur HTTP {e.code}: {e.reason}")
                return False
                
    except urllib.error.URLError as e:
        print(f"   ❌ Erreur de connexion: {e.reason}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_inscription()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST RÉUSSI - L'inscription fonctionne!")
        print("=" * 60)
        print("\n💡 Julie peut maintenant créer son compte sans erreur 500")
    else:
        print("❌ TEST ÉCHOUÉ - L'inscription ne fonctionne pas")
        print("=" * 60)
        print("\n💡 Vérifiez les logs Render pour plus de détails")
