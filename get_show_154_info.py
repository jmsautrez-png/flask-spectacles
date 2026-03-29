from app import app, db
from models.models import Show, User

with app.app_context():
    show = Show.query.get(154)
    
    if show:
        print("=" * 70)
        print(f"📺 SPECTACLE ID: {show.id}")
        print("=" * 70)
        print(f"Titre: {show.title}")
        print(f"Catégorie: {show.category}")
        print(f"Durée: {show.duration or 'N/A'}")
        print(f"Public: {show.age_range or 'N/A'}")
        print(f"Tarif: {show.tarif or 'N/A'}")
        print()
        
        if show.user:
            print(f"👤 Propriétaire:")
            print(f"   Username: {show.user.username}")
            print(f"   Raison sociale: {show.user.raison_sociale or 'N/A'}")
            print(f"   Email: {show.user.email}")
            print(f"   Téléphone: {show.user.phone or 'N/A'}")
        else:
            print("⚠️  Aucun propriétaire associé")
        
        print("=" * 70)
    else:
        print("❌ Spectacle ID 154 non trouvé")
