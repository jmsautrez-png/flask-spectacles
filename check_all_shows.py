from app import create_app
from models.models import Show

app = create_app()
with app.app_context():
    # Afficher toutes les cartes
    shows = Show.query.all()
    
    print(f"📋 Liste de toutes les cartes ({len(shows)}):\n")
    for show in shows:
        print(f"ID: {show.id}")
        print(f"   Titre: {show.title}")
        print(f"   Catégorie: {show.category}")
        print(f"   Region: {show.region}")
        print(f"   User: {show.user.username if show.user else 'N/A'}")
        print(f"   User region: {show.user.region if show.user else 'N/A'}")
        print(f"   Approved: {show.approved}")
        print(f"   Description (50 premiers car): {show.description[:50] if show.description else 'N/A'}")
        print()
