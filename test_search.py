from app import create_app
from models.models import Show
from utils.search import generate_search_patterns

app = create_app()
with app.app_context():
    # Test de recherche
    query = "pere noel"
    patterns = generate_search_patterns(query)
    
    print(f"🔍 Recherche: '{query}'")
    print(f"📋 Patterns générés ({len(patterns)}): {patterns[:20]}")
    print()
    
    # Simuler la recherche dans app.py
    from sqlalchemy import or_
    
    # Chercher avec tous les patterns
    conditions = []
    for pattern in patterns:
        like_pattern = f"%{pattern}%"
        conditions.extend([
            Show.title.ilike(like_pattern),
            Show.description.ilike(like_pattern),
            Show.category.ilike(like_pattern),
        ])
    
    shows = Show.query.filter(Show.approved.is_(True)).filter(or_(*conditions)).all()
    
    print(f"✅ Résultats: {len(shows)} carte(s) trouvée(s)")
    for show in shows:
        print(f"   - {show.title} (Catégorie: {show.category})")
