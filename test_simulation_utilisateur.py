#!/usr/bin/env python3
"""
Script de test pour simuler un utilisateur et tester l'envoi d'appels d'offre
Usage: python test_simulation_utilisateur.py VOTRE-EMAIL@gmail.com
"""

import sys
from app import create_app
from models.models import db, User, Show, DemandeAnimation
from werkzeug.security import generate_password_hash
from datetime import datetime

if len(sys.argv) < 2:
    print("❌ Usage: python test_simulation_utilisateur.py VOTRE-EMAIL@gmail.com")
    sys.exit(1)

EMAIL_TEST = sys.argv[1]

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("🎭 SIMULATION UTILISATEUR POUR TESTS APPELS D'OFFRE")
    print("="*70)
    
    # 1. Créer ou récupérer l'utilisateur test
    print(f"\n1️⃣ Création utilisateur test avec email: {EMAIL_TEST}")
    user = User.query.filter_by(email=EMAIL_TEST).first()
    
    if user:
        print(f"   ✅ Utilisateur existant trouvé: {user.username}")
    else:
        user = User(
            username=f"test_{datetime.now().strftime('%H%M%S')}",
            password_hash=generate_password_hash("test123"),
            email=EMAIL_TEST,
            full_name="Utilisateur Test",
            region="Île-de-France",
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        print(f"   ✅ Utilisateur créé: {user.username}")
    
    # 2. Créer un spectacle approuvé pour cet utilisateur
    print(f"\n2️⃣ Création/vérification spectacle approuvé pour {user.username}")
    show = Show.query.filter_by(user_id=user.id, approved=True).first()
    
    if show:
        print(f"   ✅ Spectacle approuvé existant: {show.title}")
    else:
        show = Show(
            user_id=user.id,
            title="Spectacle de Test - Magie",
            description="Spectacle de magie pour tests appels d'offre",
            category="Magie",
            region="Île-de-France",
            approved=True,
            created_at=datetime.utcnow()
        )
        db.session.add(show)
        db.session.commit()
        print(f"   ✅ Spectacle créé et approuvé: {show.title}")
    
    # 3. Afficher les stats
    print(f"\n3️⃣ Statistiques:")
    print(f"   - ID utilisateur: {user.id}")
    print(f"   - Email: {user.email}")
    print(f"   - Région: {user.region}")
    print(f"   - Spectacle ID: {show.id}")
    print(f"   - Catégorie spectacle: {show.category}")
    print(f"   - Approuvé: {show.approved}")
    
    # 4. Vérifier les appels d'offre existants
    print(f"\n4️⃣ Appels d'offre correspondants:")
    appels = DemandeAnimation.query.filter(
        DemandeAnimation.is_private == False,
        DemandeAnimation.approved == True,
        DemandeAnimation.genre_recherche.ilike(f"%{show.category}%")
    ).all()
    
    if appels:
        print(f"   ✅ {len(appels)} appel(s) d'offre trouvé(s) pour la catégorie '{show.category}':")
        for ao in appels:
            print(f"      - #{ao.id}: {ao.structure} - {ao.genre_recherche}")
    else:
        print(f"   ℹ️ Aucun appel d'offre pour la catégorie '{show.category}'")
    
    print("\n" + "="*70)
    print("✅ SIMULATION TERMINÉE")
    print("="*70)
    print(f"\n📧 Tous les emails d'appels d'offre seront envoyés à: {EMAIL_TEST}")
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("   1. Lancez l'application: python app.py")
    print("   2. Connectez-vous en admin (admin / Mael,2012)")
    print("   3. Allez sur Admin > Appels d'offre")
    print("   4. Créez un appel d'offre avec:")
    print(f"      - Genre: {show.category}")
    print(f"      - Région: {user.region}")
    print("   5. Prévisualisez les destinataires")
    print(f"   6. Vérifiez que {user.username} apparaît dans la liste")
    print("   7. Envoyez l'appel d'offre")
    print(f"   8. Vérifiez votre boîte mail: {EMAIL_TEST}")
    print("\n💡 ASTUCE: Pour tester sans publier de spectacle:")
    print(f"   - Supprimez le spectacle: python -c 'from app import create_app; from models.models import db, Show; app = create_app(); app.app_context().push(); Show.query.filter_by(id={show.id}).delete(); db.session.commit(); print(\"Spectacle supprimé\")'")
    print(f"   - L'utilisateur ne recevra PLUS les emails")
    print(f"   - La page /mes-appels-offres sera bloquée")
    print("\n")
