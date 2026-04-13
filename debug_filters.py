from app import create_app
from models.models import Show
from sqlalchemy import or_

app = create_app()
with app.app_context():
    print("=== TEST 1: Filtre catégorie uniquement ===")
    categories = ["Père Noël"]
    
    query = Show.query.filter(Show.approved.is_(True))
    category_filters = []
    for cat in categories:
        category_filters.extend([
            Show.category.ilike(f"%{cat}%"),
            Show.title.ilike(f"%{cat}%"),
            Show.description.ilike(f"%{cat}%"),
        ])
    query = query.filter(or_(*category_filters))
    
    shows = query.all()
    print(f"Résultats: {len(shows)} carte(s)")
    for show in shows:
        print(f"  - {show.title} (catégorie: {show.category}, région: {show.region})")
    
    print("\n=== TEST 2: Filtre région uniquement ===")
    regions = ["Occitanie"]
    
    query2 = Show.query.filter(Show.approved.is_(True))
    from models.models import User as UserModel
    from app import db
    user_ids_in_region = db.session.query(UserModel.id).filter(
        or_(*[UserModel.region.ilike(f"%{reg}%") for reg in regions])
    ).subquery()
    region_filters = []
    for reg in regions:
        region_filters.append(Show.region.ilike(f"%{reg}%"))
    region_filters.append(Show.user_id.in_(user_ids_in_region))
    query2 = query2.filter(or_(*region_filters))
    
    shows2 = query2.all()
    print(f"Résultats: {len(shows2)} carte(s)")
    for show in shows2:
        print(f"  - {show.title} (région: {show.region}, user_id: {show.user_id})")
    
    print("\n=== TEST 3: Les deux filtres combinés ===")
    query3 = Show.query.filter(Show.approved.is_(True))
    
    # Catégorie
    category_filters = []
    for cat in categories:
        category_filters.extend([
            Show.category.ilike(f"%{cat}%"),
            Show.title.ilike(f"%{cat}%"),
            Show.description.ilike(f"%{cat}%"),
        ])
    query3 = query3.filter(or_(*category_filters))
    
    # Région
    region_filters = []
    for reg in regions:
        region_filters.append(Show.region.ilike(f"%{reg}%"))
    region_filters.append(Show.user_id.in_(user_ids_in_region))
    query3 = query3.filter(or_(*region_filters))
    
    shows3 = query3.all()
    print(f"Résultats: {len(shows3)} carte(s)")
    for show in shows3:
        print(f"  - {show.title}")
