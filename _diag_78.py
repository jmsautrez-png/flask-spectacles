from app import create_app
from models.models import Show, DemandeAnimation
from utils.matching import compute_score

a = create_app()
with a.app_context():
    s = Show.query.get(78)
    d = DemandeAnimation.query.get(59)
    if not s or not d:
        print("introuvable", s, d); raise SystemExit
    print("=== SHOW 78 ===")
    print(" title    :", s.title)
    print(" approved :", s.approved)
    print(" specs    :", repr(s.specialites))
    print(" events   :", repr(s.evenements))
    print(" lieux    :", repr(s.lieux_intervention))
    print(" regions  :", repr(s.regions_intervention))
    print(" location :", repr(s.location))
    print(" public_categories  :", repr(s.public_categories))
    print(" public_sous_options:", repr(s.public_sous_options))
    print(" age_range:", repr(getattr(s, 'age_range', None)))
    u = s.user
    print(" user.cp  :", repr(getattr(u, 'code_postal', None)))
    print(" user.dpt :", repr(getattr(u, 'departement', None)))
    print(" user.reg :", repr(getattr(u, 'region', None)))
    print()
    print("=== DEMANDE 59 ===")
    print(" specs       :", repr(d.specialites_recherchees))
    print(" events      :", repr(d.evenements_contexte))
    print(" lieux       :", repr(d.lieux_souhaites))
    print(" cp          :", repr(d.code_postal))
    print(" dpt         :", repr(d.departement))
    print(" region      :", repr(d.region))
    print(" portee_nat  :", d.portee_nationale)
    print(" public_cats :", repr(d.public_categories))
    print(" public_subs :", repr(d.public_sous_options))
    print(" age_range   :", repr(d.age_range))
    print()
    sc = compute_score(s, d)
    print("=== SCORE ===")
    for k, v in sc.items():
        print(f"  {k}: {v}")
