#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de test d'envoi d'email"""

from app import create_app
from flask_mail import Message

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("📧 TEST D'ENVOI D'EMAIL")
    print("="*80 + "\n")
    
    # Email de test
    test_email = "contact@spectacleanimation.fr"
    
    print(f"📨 Envoi d'un email de test à : {test_email}")
    print("-" * 80)
    
    if not hasattr(app, 'mail'):
        print("❌ ERREUR : Flask-Mail n'est pas initialisé !")
    else:
        try:
            # Créer un email de test
            msg = Message(
                subject="🧪 TEST - Email de vérification Spectacle'ment Vôtre",
                recipients=[test_email]
            )
            
            msg.html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }
        .content { padding: 20px; background-color: #f9f9f9; border-radius: 8px; }
        h2 { color: #1b2a4e; }
        .success-box { background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }
    </style>
</head>
<body>
    <div class="content">
        <h2>🧪 Test d'envoi d'email</h2>
        <div class="success-box">
            <h3>✅ Email envoyé avec succès !</h3>
            <p>Si vous recevez cet email, votre configuration SMTP fonctionne correctement.</p>
        </div>
        <p><strong>Configuration testée :</strong></p>
        <ul>
            <li>Serveur SMTP : OVH (ssl0.ovh.net)</li>
            <li>Port : 587 (TLS)</li>
            <li>Expéditeur : contact@spectacleanimation.fr</li>
        </ul>
        <p style="color: #666; font-size: 0.9em; margin-top: 30px;">
            <strong>Note :</strong> Si cet email arrive dans vos SPAMS, ajoutez contact@spectacleanimation.fr à votre liste de contacts sûrs.
        </p>
    </div>
</body>
</html>
"""
            
            print("⏳ Envoi en cours...")
            app.mail.send(msg)
            print("✅ Email envoyé avec succès !")
            print("\n📝 Vérifiez votre boîte email (et le dossier SPAM)")
            print(f"   Destinataire : {test_email}")
            print(f"   Objet : 🧪 TEST - Email de vérification Spectacle'ment Vôtre")
            
        except Exception as e:
            print(f"❌ ERREUR lors de l'envoi :")
            print(f"   {str(e)}")
            print("\n💡 Causes possibles :")
            print("   - Identifiants SMTP incorrects")
            print("   - Serveur SMTP bloqué/inaccessible")
            print("   - Limite d'envoi atteinte")
    
    print("\n" + "="*80 + "\n")
