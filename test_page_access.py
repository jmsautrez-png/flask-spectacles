"""Test direct de la page des statistiques"""
import requests
from requests.auth import HTTPBasicAuth

try:
    # Test sans authentification d'abord
    print("🔍 Test d'accès à la page des statistiques...")
    response = requests.get('http://127.0.0.1:5000/admin/statistiques', timeout=5)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page accessible!")
        # Vérifier si Chart.js est présent
        if 'Chart' in response.text:
            print("✅ Chart.js trouvé dans la page")
        if 'visitsChart' in response.text:
            print("✅ Code du graphique trouvé")
        if 'Horaires' in response.text or 'horaires' in response.text:
            print("✅ Mention 'Horaires' trouvée")
        if 'strftime' in response.text:
            print("⚠️  strftime visible dans le HTML (ne devrait pas)")
    elif response.status_code == 302 or response.status_code == 401:
        print("⚠️  Redirection (login requis)")
        print(f"   Location: {response.headers.get('Location', 'N/A')}")
    elif response.status_code == 500:
        print("❌ Erreur serveur 500")
        if 'text/html' in response.headers.get('Content-Type', ''):
            print("\n📄 Début du contenu HTML:")
            print(response.text[:1000])
    else:
        print(f"❌ Code inattendu: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Impossible de se connecter au serveur")
    print("   Le serveur Flask n'est peut-être pas démarré?")
except Exception as e:
    print(f"❌ Erreur: {e}")
