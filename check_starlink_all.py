"""Chercher TOUTES les visites Starlink (bots inclus)"""
from app import app, db
from models.models import VisitorLog
from datetime import datetime, timedelta, timezone

with app.app_context():
    # Dernières 48 heures
    recent = datetime.now(timezone.utc) - timedelta(hours=48)
    
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
    
    print(f'📡 TOUTES visites Starlink (48h): {len(starlink_all)}')
    print('='*100)
    
    # Grouper par session_id
    sessions = {}
    for v in starlink_all:
        sid = v.session_id
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append(v)
    
    print(f'Sessions uniques: {len(sessions)}')
    print()
    
    # Afficher chaque session
    for session_id, visits in sorted(sessions.items(), key=lambda x: x[1][0].visited_at, reverse=True):
        first_visit = visits[0]
        bot_label = '🤖 BOT' if first_visit.is_bot else '✅ HUMAIN'
        
        print(f'{bot_label} | Session: {session_id[:20]}... | Pages: {len(visits)}')
        print(f'  ISP: {first_visit.isp}')
        print(f'  City: {first_visit.city or "N/A"}')
        print(f'  Première visite: {visits[-1].visited_at}')
        print(f'  Dernière visite: {visits[0].visited_at}')
        print(f'  User-Agent: {first_visit.user_agent[:100] if first_visit.user_agent else "N/A"}')
        print('-'*100)
