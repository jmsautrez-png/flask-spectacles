"""Script pour vérifier les ISP des visiteurs"""
from app import app, db
from models.models import VisitorLog

with app.app_context():
    print("=" * 80)
    print("ANALYSE DES ISP DANS LA BASE DE DONNÉES")
    print("=" * 80)
    
    total = VisitorLog.query.count()
    print(f"\nTotal visiteurs: {total}")
    
    # Compter les visiteurs avec/sans ISP
    with_isp = VisitorLog.query.filter(VisitorLog.isp != None, VisitorLog.isp != '').count()
    without_isp = total - with_isp
    
    print(f"Avec ISP: {with_isp} ({with_isp/total*100:.1f}%)")
    print(f"Sans ISP: {without_isp} ({without_isp/total*100:.1f}%)")
    
    # Afficher les 30 premiers visiteurs
    print("\n" + "=" * 80)
    print("30 PREMIERS VISITEURS:")
    print("=" * 80)
    
    visitors = VisitorLog.query.order_by(VisitorLog.visited_at.desc()).limit(30).all()
    for i, v in enumerate(visitors, 1):
        print(f"\n{i}. Date: {v.visited_at}")
        print(f"   ISP: {v.isp if v.isp else 'NULL'}")
        print(f"   Ville: {v.city if v.city else 'NULL'}")
        print(f"   User-Agent: {v.user_agent[:100] if v.user_agent else 'NULL'}...")
        print(f"   is_bot: {v.is_bot}")
