_!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test post-déploiement
Vérifie que l'application répond correctement en production
Usage: python test_deployment.py [URL]
Exemple: python test_deployment.py https://spectacleanimation.fr
"""
import sys
import requests
from urllib.parse import urljoin

def test_endpoint(base_url, endpoint, expected_status=200, description=""):
    """Teste un endpoint et affiche le résultat"""
    url = urljoin(base_url, endpoint)
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        
        if response.status_code == expected_status:
            print(f"   ✓ {endpoint} → {response.status_code} OK")
            return True
        else:
            print(f"   ✗ {endpoint} → {response.status_code} (attendu: {expected_status})")
            return False
    except requests.exceptions.Timeout:
        print(f"   ✗ {endpoint} → TIMEOUT")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   ✗ {endpoint} → CONNEXION IMPOSSIBLE")
        return False
    except Exception as e:
        print(f"   ✗ {endpoint} → ERREUR: {e}")
        return False

def test_health_json(base_url, endpoint):
    """Teste un endpoint health et vérifie le JSON"""
    url = urljoin(base_url, endpoint)
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"   ✗ {endpoint} → {response.status_code}")
            return False
        
        data = response.json()
        status = data.get('status')
        
        if status in ['healthy', 'ok']:
            print(f"   ✓ {endpoint} → {status}")
            if 'database' in data:
                db_status = data.get('database')
                print(f"      Database: {db_status}")
            return True
        else:
            print(f"   ⚠️  {endpoint} → status: {status}")
            return False
            
    except Exception as e:
        print(f"   ✗ {endpoint} → ERREUR: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://spectacleanimation.fr"
    
    # Supprimer le trailing slash
    base_url = base_url.rstrip('/')
    
    print("=" * 70)
    print(f"TEST POST-DÉPLOIEMENT - {base_url}")
    print("=" * 70)
    
    results = []
    
    # Tests Health Checks
    print("\n🏥 Health Checks:")
    results.append(test_health_json(base_url, "/health"))
    results.append(test_health_json(base_url, "/health/full"))
    results.append(test_health_json(base_url, "/health/s3"))
    
    # Tests Pages Publiques
    print("\n🌐 Pages Publiques:")
    results.append(test_endpoint(base_url, "/", 200, "Page d'accueil"))
    results.append(test_endpoint(base_url, "/catalogue", 200, "Catalogue"))
    results.append(test_endpoint(base_url, "/about", 200, "Qui sommes-nous"))
    results.append(test_endpoint(base_url, "/contact", 200, "Contact"))
    results.append(test_endpoint(base_url, "/legal", 200, "Mentions légales"))
    
    # Tests Pages Thématiques (SEO)
    print("\n🎭 Pages Thématiques:")
    results.append(test_endpoint(base_url, "/magiciens", 200))
    results.append(test_endpoint(base_url, "/clowns", 200))
    results.append(test_endpoint(base_url, "/marionnettes", 200))
    results.append(test_endpoint(base_url, "/spectacles-enfants", 200))
    results.append(test_endpoint(base_url, "/animations-entreprises", 200))
    results.append(test_endpoint(base_url, "/animations-enfants", 200))
    results.append(test_endpoint(base_url, "/animations-anniversaire", 200))
    results.append(test_endpoint(base_url, "/spectacles-noel", 200))
    
    # Tests Authentification
    print("\n🔐 Authentification:")
    results.append(test_endpoint(base_url, "/login", 200))
    results.append(test_endpoint(base_url, "/register", 200))
    results.append(test_endpoint(base_url, "/forgot", 200))
    
    # Tests Formulaires
    print("\n📝 Formulaires:")
    results.append(test_endpoint(base_url, "/demande-animation", 200))
    results.append(test_endpoint(base_url, "/demande-ecole", 200))
    results.append(test_endpoint(base_url, "/demandes-animation", 200))
    results.append(test_endpoint(base_url, "/submit", 200))
    
    # Tests Pages Info
    print("\n📄 Pages Complémentaires:")
    results.append(test_endpoint(base_url, "/abonnement-compagnie", 200))
    results.append(test_endpoint(base_url, "/ecoles-themes", 200))
    results.append(test_endpoint(base_url, "/evenements", 200))
    
    # Tests SEO
    print("\n🔍 SEO:")
    results.append(test_endpoint(base_url, "/robots.txt", 200))
    results.append(test_endpoint(base_url, "/sitemap.xml", 200))
    
    # Tests Admin (doivent rediriger vers login)
    print("\n🛡️  Admin (protection):")
    results.append(test_endpoint(base_url, "/admin", 302, "Redirige vers login si non connecté"))
    results.append(test_endpoint(base_url, "/dashboard", 302, "Redirige vers login si non connecté"))
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    
    total = len(results)
    success = sum(results)
    failed = total - success
    success_rate = (success / total * 100) if total > 0 else 0
    
    print(f"\n✅ Réussis: {success}/{total} ({success_rate:.1f}%)")
    if failed > 0:
        print(f"❌ Échoué: {failed}/{total}")
    
    print("\n" + "=" * 70)
    
    if success_rate >= 90:
        print("✅ DÉPLOIEMENT RÉUSSI - Application opérationnelle")
        return 0
    elif success_rate >= 70:
        print("⚠️  DÉPLOIEMENT PARTIEL - Certaines fonctionnalités sont inaccessibles")
        return 1
    else:
        print("❌ DÉPLOIEMENT ÉCHOUÉ - Application non opérationnelle")
        return 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrompu par l'utilisateur")
        sys.exit(130)
