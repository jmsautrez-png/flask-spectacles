from app import create_app
from models.models import Show

app = create_app()
with app.app_context():
    total = Show.query.count()
    approved = Show.query.filter_by(approved=True).count()
    print(f"Total spectacles: {total}")
    print(f"Spectacles approuves: {approved}")
    print(f"En attente: {total - approved}")
    
    if total > 30:
        print(f"\n✓ Pagination necessaire (plus de 30 spectacles)")
        print(f"  Nombre de pages: {(total + 29) // 30}")
    else:
        print(f"\n✓ Pagination pas encore necessaire (moins de 30 spectacles)")
