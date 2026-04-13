from app import create_app
from models.models import Show

app = create_app()
with app.app_context():
    # Chercher la carte Père Noël
    show = Show.query.filter(Show.title.ilike('%pere%noel%')).first()
    
    if show:
        print(f"✅ Carte trouvée: {show.title}")
        print(f"   ID: {show.id}")
        print(f"   Approved: {show.approved}")
        print(f"   Category: {show.category}")
        print(f"   Region: {show.region}")
        print(f"   User region: {show.user.region if show.user else 'N/A'}")
    else:
        print("❌ Aucune carte Père Noël trouvée")
        
    # Chercher toutes les cartes
    all_shows = Show.query.all()
    print(f"\n📊 Total cartes en base: {len(all_shows)}")
    approved = Show.query.filter(Show.approved.is_(True)).count()
    print(f"   Approuvées: {approved}")
    print(f"   Non approuvées: {len(all_shows) - approved}")
