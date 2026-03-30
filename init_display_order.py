"""
Initialiser les positions d'affichage des spectacles.
Attribue des numéros séquentiels (1, 2, 3...) basés sur l'ordre actuel.
"""

from app import create_app
from models import db
from models.models import Show

app = create_app()

with app.app_context():
    try:
        # Récupérer tous les spectacles approuvés, triés par date de création (plus récent d'abord)
        shows = Show.query.filter_by(approved=True).order_by(Show.created_at.desc()).all()
        
        print(f"📊 {len(shows)} spectacles approuvés trouvés.")
        
        # Attribuer des positions séquentielles
        for i, show in enumerate(shows, start=1):
            show.display_order = i * 10  # Multiples de 10 pour pouvoir insérer entre
            print(f"  {i:3d}. [{show.display_order:4d}] {show.title[:50]}")
        
        db.session.commit()
        print(f"\n✅ Positions initialisées avec succès ! ({len(shows)} spectacles)")
        print("💡 Les positions sont en multiples de 10 (10, 20, 30...) pour faciliter l'insertion.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur: {e}")
