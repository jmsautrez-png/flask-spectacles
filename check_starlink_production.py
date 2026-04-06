"""
Script à exécuter sur RENDER pour vérifier les visites Starlink en production
"""
from app import app, db
from models.models import VisitorLog
from datetime import datetime, timedelta, timezone

with app.app_context():
    # Dernières 48 heures
    recent = datetime.now(timezone.utc) - timedelta(hours=48)
    
    print("="*100)
    print("🔍 RECHERCHE VISITES STARLINK/SPACEX EN PRODUCTION (48h)")
    print("="*100)
    print()
    
    # TOUTES les visites Starlink/SpaceX (BOT ou HUMAIN)
    starlink_all = VisitorLog.query.filter(
        VisitorLog.visited_at >= recent
    ).filter(
        db.or_(
            VisitorLog.isp.like('%Starlink%'),
            VisitorLog.isp.like('%SpaceX%'),
            VisitorLog.isp.like('%Space Exploration%')
        )
    ).order_by(VisitorLog.visited_at.desc()).all()
    
    print(f'📡 Total visites Starlink trouvées: {len(starlink_all)}')
    print()
    
    if len(starlink_all) == 0:
        print("❌ Aucune visite Starlink trouvée dans les 48 dernières heures")
        print()
        print("Vérifications:")
        print("1. As-tu visité le site de PRODUCTION (https://spectacleanimation.fr) ?")
        print("2. Ou as-tu visité le site LOCAL (localhost:5000) ?")
        print()
        print("Note: Les visites sur localhost ne sont PAS enregistrées en production.")
    else:
        # Grouper par session_id
        sessions = {}
        for v in starlink_all:
            sid = v.session_id
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(v)
        
        print(f'👥 Sessions uniques: {len(sessions)}')
        print()
        print("="*100)
        
        # Afficher chaque session
        for i, (session_id, visits) in enumerate(sorted(sessions.items(), key=lambda x: x[1][0].visited_at, reverse=True), 1):
            first_visit = visits[0]
            last_visit = visits[-1]
            bot_label = '🤖 BOT' if first_visit.is_bot else '✅ HUMAIN'
            
            print(f"SESSION #{i}")
            print(f'{bot_label} | Session ID: {session_id[:30]}...')
            print(f'📊 Nombre de pages visitées: {len(visits)}')
            print(f'🌐 ISP: {first_visit.isp}')
            print(f'📍 Ville: {first_visit.city or "N/A"}')
            print(f'🇫🇷 Région: {first_visit.region or "N/A"}')
            print(f'⏰ Première visite: {last_visit.visited_at}')
            print(f'⏰ Dernière visite: {first_visit.visited_at}')
            print(f'💻 User-Agent: {first_visit.user_agent[:100] if first_visit.user_agent else "N/A"}...')
            
            # Explication si marqué BOT
            if first_visit.is_bot:
                print()
                print(f'⚠️  MARQUÉ COMME BOT - Raisons possibles:')
                if len(visits) >= 10:
                    print(f'   ✓ Détection comportementale: {len(visits)} pages visitées (limite: 10)')
                else:
                    print(f'   ✓ Détection ISP ou User-Agent')
            
            print('-'*100)
            print()
        
        # Statistiques globales
        total_bot = sum(1 for v in starlink_all if v.is_bot)
        total_human = sum(1 for v in starlink_all if not v.is_bot)
        
        print("="*100)
        print("📊 STATISTIQUES STARLINK")
        print("="*100)
        print(f"Total visites: {len(starlink_all)}")
        print(f"  🤖 Marquées BOT: {total_bot} ({total_bot/len(starlink_all)*100:.1f}%)")
        print(f"  ✅ Marquées HUMAIN: {total_human} ({total_human/len(starlink_all)*100:.1f}%)")
        print()
        
        # Pages par session
        pages_per_session = [len(visits) for visits in sessions.values()]
        print(f"Pages par session:")
        print(f"  Minimum: {min(pages_per_session)}")
        print(f"  Maximum: {max(pages_per_session)}")
        print(f"  Moyenne: {sum(pages_per_session)/len(pages_per_session):.1f}")
