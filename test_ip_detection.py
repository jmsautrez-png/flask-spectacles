"""
Script de diagnostic pour vérifier la récupération des IPs
"""
from app import app
from flask import request

@app.route('/test-ip')
def test_ip():
    """Route de test pour diagnostiquer la récupération d'IP"""
    
    info = {
        'remote_addr': request.remote_addr,
        'X-Forwarded-For': request.headers.get('X-Forwarded-For'),
        'X-Real-IP': request.headers.get('X-Real-IP'),
        'CF-Connecting-IP': request.headers.get('CF-Connecting-IP'),  # Cloudflare
        'True-Client-IP': request.headers.get('True-Client-IP'),
        'X-Client-IP': request.headers.get('X-Client-IP'),
    }
    
    # Déterminer quelle IP serait utilisée
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        detected_ip = forwarded_for.split(',')[0].strip()
    else:
        detected_ip = request.remote_addr or '0.0.0.0'
    
    # Anonymiser comme dans le code réel
    ip_parts = detected_ip.split('.')
    if len(ip_parts) == 4:
        ip_anonymized = f"{ip_parts[0]}.{ip_parts[1]}.0.0"
    else:
        ip_anonymized = "0.0.0.0"
    
    html = f"""
    <html>
    <head><title>Test IP Detection</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h1>🔍 Diagnostic IP Visiteur</h1>
        
        <h2>Headers Reçus:</h2>
        <ul>
            <li><strong>request.remote_addr:</strong> {info['remote_addr']}</li>
            <li><strong>X-Forwarded-For:</strong> {info['X-Forwarded-For'] or 'Non présent'}</li>
            <li><strong>X-Real-IP:</strong> {info['X-Real-IP'] or 'Non présent'}</li>
            <li><strong>CF-Connecting-IP:</strong> {info['CF-Connecting-IP'] or 'Non présent'}</li>
            <li><strong>True-Client-IP:</strong> {info['True-Client-IP'] or 'Non présent'}</li>
            <li><strong>X-Client-IP:</strong> {info['X-Client-IP'] or 'Non présent'}</li>
        </ul>
        
        <h2>IP Détectée par le Code:</h2>
        <p style="background: #f0f0f0; padding: 10px; font-size: 18px;">
            <strong>IP Brute:</strong> {detected_ip}<br>
            <strong>IP Anonymisée (stockée):</strong> {ip_anonymized}
        </p>
        
        <h2>Analyse:</h2>
        <p>
            {'✅ IP publique détectée' if not detected_ip.startswith('10.') and not detected_ip.startswith('192.168.') and not detected_ip.startswith('172.') 
             else '❌ IP privée - Le header X-Forwarded-For ne contient pas d\'IP publique'}
        </p>
        
        <hr>
        <p><a href="/admin/statistiques">← Retour aux statistiques</a></p>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    print("=" * 70)
    print("🧪 SERVEUR DE TEST - Diagnostic IP")
    print("=" * 70)
    print("\n1. Démarrer le serveur Flask...")
    print("2. Ouvrir : http://127.0.0.1:5000/test-ip")
    print("3. Vérifier les headers reçus")
    print("\n" + "=" * 70)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
