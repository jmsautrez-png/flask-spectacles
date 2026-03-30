from app import app, db
from models.models import Show

with app.app_context():
    # Rechercher tous les spectacles avec "marionnette" dans la catégorie
    shows = Show.query.filter(Show.category.ilike('%marionnette%')).all()
    
    # Récupérer les emails uniques
    emails = set()
    details = []
    
    for show in shows:
        # Priorité : email du spectacle, sinon email de l'utilisateur
        email = show.contact_email
        if not email and show.user:
            email = show.user.email if hasattr(show.user, 'email') else None
        
        if email:
            emails.add(email)
        
        details.append({
            'titre': show.title,
            'categorie': show.category,
            'email_spectacle': show.contact_email or '(aucun)',
            'email_utilisateur': show.user.email if (show.user and hasattr(show.user, 'email')) else '(aucun)',
            'email_final': email or '(aucun)',
            'approuve': 'OUI' if show.approved else 'NON'
        })
    
    print('\n' + '='*60)
    print('RECHERCHE: CATEGORIE MARIONNETTE')
    print('='*60)
    print(f'\n📊 Nombre de spectacles trouvés: {len(shows)}')
    print(f'📧 Nombre d\'emails uniques: {len(emails)}')
    
    print('\n' + '='*60)
    print('LISTE DES EMAILS UNIQUES')
    print('='*60)
    for email in sorted(emails):
        print(f'  ✉️  {email}')
    
    print('\n' + '='*60)
    print('DETAILS DES SPECTACLES')
    print('='*60)
    for idx, detail in enumerate(details, 1):
        print(f'\n[{idx}] {detail["titre"]}')
        print(f'    Catégorie: {detail["categorie"]}')
        print(f'    Email spectacle: {detail["email_spectacle"]}')
        print(f'    Email utilisateur: {detail["email_utilisateur"]}')
        print(f'    Email retenu: {detail["email_final"]}')
        print(f'    Approuvé: {detail["approuve"]}')
    
    print('\n' + '='*60)
