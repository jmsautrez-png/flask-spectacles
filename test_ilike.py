from app import create_app
from models.models import Show

app = create_app()
with app.app_context():
    # Test direct avec ILIKE
    patterns_to_test = ['pere-noel', 'pere noel', 'Père-Noël', 'Pere-Noel']
    
    for pattern in patterns_to_test:
        result = Show.query.filter(Show.title.ilike(f'%{pattern}%')).first()
        print(f"Pattern '{pattern}': {'FOUND' if result else 'NOT FOUND'}")
        if result:
            print(f"  -> Titre: {result.title}")
