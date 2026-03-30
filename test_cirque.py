from app import app
from models.models import Show

with app.app_context():
    shows = Show.query.filter(
        Show.approved.is_(True), 
        Show.category.ilike('%cirque%')
    ).all()
    
    print(f"\n✅ Nombre de spectacles avec 'Cirque' dans la catégorie : {len(shows)}\n")
    
    if shows:
        print("📧 Emails qui recevraient la demande d'animation :\n")
        emails_found = set()
        
        for show in shows:
            email = show.contact_email
            if not email and show.user:
                email = show.user.email if hasattr(show.user, 'email') else None
            
            if email and email not in emails_found:
                emails_found.add(email)
                print(f"  • {show.title}")
                print(f"    Catégorie: {show.category}")
                print(f"    Email: {email}")
                print(f"    Région: {show.region or 'Non spécifiée'}")
                print()
        
        print(f"📊 Total: {len(emails_found)} email(s) unique(s) seraient contactés")
    else:
        print("❌ Aucun spectacle trouvé avec la catégorie 'Cirque'")
