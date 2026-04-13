from app import create_app
from models.models import Show
from sqlalchemy import or_
from utils.search import generate_search_patterns

app = create_app()
with app.app_context():
    # Simuler la recherche de l'admin avec catégorie "Père Noël" et région "Occitanie"
    categories = ["Père Noël"]
    regions = ["Occitanie"]
    
    print(f"🔍 Recherche admin:")
    print(f"   Catégories: {categories}")
    print(f"   Régions: {regions}")
    print()
    
    # Code exact de app.py AVEC FUZZY SEARCH
    query = Show.query.filter(Show.approved.is_(True))
    
    if categories:
        category_filters = []
        for cat in categories:
            # Générer des variantes avec tirets, accents, etc.
            cat_patterns = generate_search_patterns(cat, max_variants=40)
            print(f"   Patterns générés pour '{cat}': {cat_patterns[:10]}...")
            for pattern in cat_patterns:
                category_filters.extend([
                    Show.category.ilike(f"%{pattern}%"),
                    Show.title.ilike(f"%{pattern}%"),
                    Show.description.ilike(f"%{pattern}%"),
                ])
        query = query.filter(or_(*category_filters))
    
    if regions:
        from models.models import User as UserModel
        from app import db
        user_ids_in_region = db.session.query(UserModel.id).filter(
            or_(*[UserModel.region.ilike(f"%{reg}%") for reg in regions])
        ).subquery()
        region_filters = []
        for reg in regions:
            region_filters.append(Show.region.ilike(f"%{reg}%"))
        region_filters.append(Show.user_id.in_(user_ids_in_region))
        query = query.filter(or_(*region_filters))
    
    shows = query.all()
    
    print(f"\n✅ Résultats: {len(shows)} carte(s) trouvée(s)")
    for show in shows:
        print(f"\n   📋 Carte ID {show.id}:")
        print(f"      Titre: {show.title}")
        print(f"      Catégorie: {show.category}")
        print(f"      Région show: {show.region}")
        print(f"      User: {show.user.username if show.user else 'NULL'}")
        print(f"      User région: {show.user.region if show.user else 'NULL'}")
        print(f"      Contact email: {show.contact_email or 'NULL'}")
        print(f"      User email: {show.user.email if show.user else 'NULL'}")
