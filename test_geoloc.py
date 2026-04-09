"""Test de géolocalisation IP"""
import requests

def test_geo(ip):
    """Test direct de l'API ip-api.com"""
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "city,regionName,country,isp,status"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
    except Exception as e:
        return {"error": str(e)}
    
    return {"error": "Request failed"}

# Test avec IP Starlink
test_ip = "150.228.19.147"

print(f"Test géolocalisation pour: {test_ip}")
print("="*80)

result = test_geo(test_ip)

print(f"Résultat complet: {result}")
print()

if "error" not in result:
    print(f"Status: {result.get('status', 'N/A')}")
    print(f"ISP: {result.get('isp', 'N/A')}")
    print(f"City: {result.get('city', 'N/A')}")
    print(f"Region: {result.get('regionName', 'N/A')}")
    print(f"Country: {result.get('country', 'N/A')}")
else:
    print(f"ERREUR: {result['error']}")
