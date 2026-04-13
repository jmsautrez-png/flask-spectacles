from app import create_app
from models.models import Show

app = create_app()
with app.app_context():
    show = Show.query.first()
    print(f"Titre: [{show.title}]")
    print(f"Longueur: {len(show.title)}")
    print("\nCaractères:")
    for i, c in enumerate(show.title):
        print(f"  {i}: '{c}' (ord={ord(c)}, {repr(c)})")
