#!/usr/bin/env python3
"""Script de diagnostic pour vérifier la configuration email"""

from app import create_app
from models.models import db

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("DIAGNOSTIC CONFIGURATION EMAIL")
    print("="*60)
    
    # 1. Vérifier Flask-Mail
    print("\n1️⃣ Configuration Flask-Mail:")
    if hasattr(app, 'mail'):
        print("   ✅ Flask-Mail est configuré")
        print(f"   - MAIL_SERVER: {app.config.get('MAIL_SERVER', 'NON DÉFINI')}")
        print(f"   - MAIL_PORT: {app.config.get('MAIL_PORT', 'NON DÉFINI')}")
        print(f"   - MAIL_USERNAME: {app.config.get('MAIL_USERNAME', 'NON DÉFINI')}")
        print(f"   - MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS', 'NON DÉFINI')}")
    else:
        print("   ❌ Flask-Mail N'EST PAS configuré")
    
    # 2. Vérifier l'utilisateur admin
    print("\n2️⃣ Vérification utilisateur admin:")
    try:
        from models.models import User
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"   ✅ Admin trouvé: {admin.username}")
            if hasattr(admin, 'email') and admin.email:
                print(f"   ✅ Email admin: {admin.email}")
            else:
                print("   ❌ Admin n'a PAS d'email configuré")
        else:
            print("   ❌ Aucun admin trouvé")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 3. Vérifier les demandes d'animation
    print("\n3️⃣ Demandes d'animation:")
    try:
        from models.models import DemandeAnimation
        total = DemandeAnimation.query.count()
        publiques = DemandeAnimation.query.filter_by(is_private=False).count()
        privees = DemandeAnimation.query.filter_by(is_private=True).count()
        approuvees = DemandeAnimation.query.filter_by(approved=True).count()
        
        print(f"   📊 Total: {total}")
        print(f"   📢 Publiques: {publiques}")
        print(f"   🔒 Privées: {privees}")
        print(f"   ✅ Approuvées: {approuvees}")
        print(f"   ⏳ En attente: {publiques - approuvees}")
        
        # Afficher les 5 dernières
        print("\n   📋 5 dernières demandes:")
        derniers = DemandeAnimation.query.order_by(DemandeAnimation.created_at.desc()).limit(5).all()
        for d in derniers:
            statut = "🔒 PRIVÉE" if d.is_private else ("✅ APPROUVÉE" if d.approved else "⏳ EN ATTENTE")
            print(f"      - ID {d.id}: {d.intitule or d.genre_recherche} [{statut}]")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 4. Test d'envoi d'email
    print("\n4️⃣ Test d'envoi d'email:")
    if hasattr(app, 'mail') and admin and hasattr(admin, 'email') and admin.email:
        try:
            from flask_mail import Message
            msg = Message(
                subject="🧪 Test - Configuration Email OK",
                recipients=[admin.email]
            )
            msg.html = """
            <h2>Test réussi ! ✅</h2>
            <p>Si vous recevez cet email, la configuration email fonctionne correctement.</p>
            """
            app.mail.send(msg)
            print(f"   ✅ Email de test envoyé à {admin.email}")
            print("   👉 Vérifiez votre boîte mail (y compris spam)")
        except Exception as e:
            print(f"   ❌ Erreur envoi: {e}")
    else:
        print("   ⚠️ Impossible de tester (Flask-Mail ou email admin manquant)")
    
    print("\n" + "="*60)
    print("FIN DU DIAGNOSTIC")
    print("="*60 + "\n")
