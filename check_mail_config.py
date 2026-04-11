#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script pour vérifier la configuration email et l'utilisateur admin"""

from app import create_app
from models.models import User
import os

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC CONFIGURATION EMAIL")
    print("="*80 + "\n")
    
    # 1. Vérifier la configuration Flask-Mail
    print("📧 Configuration Flask-Mail :")
    print("-" * 80)
    
    has_mail = hasattr(app, 'mail')
    print(f"   Flask-Mail initialisé : {'✅ OUI' if has_mail else '❌ NON'}")
    
    mail_server = app.config.get('MAIL_SERVER', 'Non configuré')
    mail_port = app.config.get('MAIL_PORT', 'Non configuré')
    mail_username = app.config.get('MAIL_USERNAME', 'Non configuré')
    mail_password = '***' if app.config.get('MAIL_PASSWORD') else 'Non configuré'
    mail_use_tls = app.config.get('MAIL_USE_TLS', False)
    mail_use_ssl = app.config.get('MAIL_USE_SSL', False)
    mail_default_sender = app.config.get('MAIL_DEFAULT_SENDER', 'Non configuré')
    
    print(f"   MAIL_SERVER : {mail_server}")
    print(f"   MAIL_PORT : {mail_port}")
    print(f"   MAIL_USERNAME : {mail_username}")
    print(f"   MAIL_PASSWORD : {mail_password}")
    print(f"   MAIL_USE_TLS : {mail_use_tls}")
    print(f"   MAIL_USE_SSL : {mail_use_ssl}")
    print(f"   MAIL_DEFAULT_SENDER : {mail_default_sender}")
    
    # 2. Vérifier les utilisateurs admin
    print("\n👤 Utilisateurs Administrateurs :")
    print("-" * 80)
    
    admins = User.query.filter_by(is_admin=True).all()
    
    if admins:
        for admin in admins:
            print(f"\n   Admin : {admin.username}")
            print(f"   ├─ Email : {admin.email if admin.email else '❌ AUCUN EMAIL CONFIGURÉ'}")
            print(f"   ├─ Raison sociale : {admin.raison_sociale or 'Non renseignée'}")
            print(f"   ├─ Région : {admin.region or 'Non renseignée'}")
            print(f"   ├─ Téléphone : {admin.telephone or 'Non renseigné'}")
            
            # Vérifier si l'admin a des spectacles
            nb_spectacles = len(admin.shows) if hasattr(admin, 'shows') else 0
            print(f"   └─ Nombre de spectacles : {nb_spectacles}")
    else:
        print("   ❌ Aucun utilisateur administrateur trouvé !")
    
    # 3. Vérifier les variables d'environnement
    print("\n🔐 Variables d'environnement EMAIL :")
    print("-" * 80)
    
    env_vars = [
        'MAIL_SERVER',
        'MAIL_PORT',
        'MAIL_USERNAME', 
        'MAIL_PASSWORD',
        'MAIL_USE_TLS',
        'MAIL_USE_SSL',
        'MAIL_DEFAULT_SENDER'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'Non défini')
        if 'PASSWORD' in var and value != 'Non défini':
            value = '***'
        print(f"   {var} : {value}")
    
    # 4. Recommandations
    print("\n" + "="*80)
    print("💡 DIAGNOSTIC")
    print("="*80)
    
    issues = []
    
    if not has_mail:
        issues.append("❌ Flask-Mail n'est pas initialisé - les emails ne peuvent pas être envoyés")
    
    if not app.config.get('MAIL_USERNAME'):
        issues.append("❌ MAIL_USERNAME non configuré")
    
    if not app.config.get('MAIL_PASSWORD'):
        issues.append("❌ MAIL_PASSWORD non configuré")
    
    if not admins:
        issues.append("❌ Aucun utilisateur admin trouvé")
    else:
        for admin in admins:
            if not admin.email:
                issues.append(f"❌ L'admin '{admin.username}' n'a pas d'email configuré")
    
    if issues:
        print("\n⚠️  PROBLÈMES DÉTECTÉS :\n")
        for issue in issues:
            print(f"   {issue}")
        print("\n📝 SOLUTION :")
        print("   1. Vérifiez que les variables d'environnement sont bien définies dans .env")
        print("   2. Ajoutez un email à votre compte admin via l'interface")
        print("   3. Redémarrez l'application après modification")
    else:
        print("\n✅ Configuration email semble correcte !")
        print("\n📝 Si les emails ne partent toujours pas :")
        print("   1. Vérifiez les logs de l'application")
        print("   2. Vérifiez votre dossier SPAM")
        print("   3. Testez l'envoi avec un script de test")
    
    print("\n" + "="*80 + "\n")
