#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test SMTP direct sans Flask pour diagnostiquer les problèmes d'authentification
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print("\n" + "="*80)
print("🧪 TEST SMTP DIRECT - DIAGNOSTIC")
print("="*80 + "\n")

# Récupérer les paramètres depuis .env
SMTP_SERVER = os.getenv("MAIL_SERVER", "ssl0.ovh.net")
SMTP_PORT = int(os.getenv("MAIL_PORT", "587"))
USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
USERNAME = os.getenv("MAIL_USERNAME", "")
PASSWORD = os.getenv("MAIL_PASSWORD", "")
SENDER = os.getenv("MAIL_DEFAULT_SENDER", USERNAME)

print("📋 Configuration détectée :")
print("-" * 80)
print(f"   Serveur SMTP : {SMTP_SERVER}")
print(f"   Port : {SMTP_PORT}")
print(f"   TLS : {USE_TLS}")
print(f"   SSL : {USE_SSL}")
print(f"   Username : {USERNAME}")
print(f"   Password : {'***' if PASSWORD else '❌ VIDE'}")
print(f"   Sender : {SENDER}")
print()

if not USERNAME or not PASSWORD:
    print("❌ ERREUR : MAIL_USERNAME ou MAIL_PASSWORD non défini dans .env")
    print("\n💡 Vérifiez votre fichier .env")
    exit(1)

# Test de connexion
print("🔍 Étapes de test :")
print("-" * 80)

try:
    print(f"\n1️⃣ Connexion au serveur {SMTP_SERVER}:{SMTP_PORT}...")
    
    if USE_SSL:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        print("   ✅ Connexion SSL établie")
    else:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print("   ✅ Connexion établie")
        
        if USE_TLS:
            print("\n2️⃣ Activation de TLS...")
            server.starttls()
            print("   ✅ TLS activé")
    
    print(f"\n3️⃣ Authentification avec {USERNAME}...")
    server.login(USERNAME, PASSWORD)
    print("   ✅ AUTHENTIFICATION RÉUSSIE !")
    
    print("\n4️⃣ Test d'envoi d'email...")
    
    # Créer un email de test
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "🧪 Test SMTP - Spectacle'ment Vôtre"
    msg['From'] = SENDER
    msg['To'] = USERNAME  # S'envoyer à soi-même
    
    html = """
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2 style="color: #1b2a4e;">✅ Test SMTP Réussi !</h2>
            <p>Votre configuration SMTP fonctionne correctement.</p>
            <ul>
                <li>Serveur : {server}</li>
                <li>Port : {port}</li>
                <li>Authentification : OK</li>
            </ul>
            <p style="color: #666; font-size: 0.9em;">
                Cet email a été envoyé par le script de test SMTP.
            </p>
        </body>
    </html>
    """.format(server=SMTP_SERVER, port=SMTP_PORT)
    
    msg.attach(MIMEText(html, 'html'))
    
    server.send_message(msg)
    print(f"   ✅ Email de test envoyé à {USERNAME}")
    
    print("\n5️⃣ Fermeture de la connexion...")
    server.quit()
    print("   ✅ Connexion fermée proprement")
    
    print("\n" + "="*80)
    print("🎉 SUCCÈS TOTAL !")
    print("="*80)
    print("\n✅ Votre configuration SMTP est correcte et fonctionnelle !")
    print(f"✅ Un email de test a été envoyé à {USERNAME}")
    print("✅ Vérifiez votre boîte de réception (et le dossier SPAM)")
    print("\n💡 Vous pouvez maintenant envoyer des appels d'offre sans problème.")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ ERREUR D'AUTHENTIFICATION : {e}")
    print("\n💡 Solutions possibles :")
    print("   1. Vérifiez que le mot de passe dans .env est correct")
    print("   2. Connectez-vous au webmail OVH pour confirmer le mot de passe")
    print("   3. Vérifiez que SMTP est activé dans Manager OVH")
    print("   4. Essayez de créer un mot de passe d'application OVH")
    print("\n📚 Voir le guide complet : FIX_SMTP_OVH.md")
    
except smtplib.SMTPConnectError as e:
    print(f"\n❌ ERREUR DE CONNEXION : {e}")
    print("\n💡 Solutions possibles :")
    print("   1. Vérifiez le serveur SMTP (ssl0.ovh.net ou pro1.mail.ovh.net)")
    print("   2. Vérifiez le port (587 pour TLS, 465 pour SSL)")
    print("   3. Vérifiez votre connexion Internet")
    
except smtplib.SMTPException as e:
    print(f"\n❌ ERREUR SMTP : {e}")
    print("\n💡 Consultez le guide : FIX_SMTP_OVH.md")
    
except Exception as e:
    print(f"\n❌ ERREUR INATTENDUE : {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")
