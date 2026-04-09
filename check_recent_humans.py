"""Script pour analyser toutes les visites humaines récentes avec détails"""
from app import app, db
from models.models import VisitorLog
from datetime import datetime, timedelta, timezone

with app.app_context():
    # Dernières 48 heures
    recent = datetime.now(timezone.utc) - timedelta(hours=48)
    
    # TOUTES les visites humaines avec ISP détaillé
    human_visits = VisitorLog.query.filter(
        VisitorLog.visited_at >= recent,
        VisitorLog.is_bot == False
    ).order_by(VisitorLog.visited_at.desc()).limit(20).all()
    
    print(f'👤 VISITES HUMAINES (48h): {len(human_visits)}')
    print('='*100)
    for v in human_visits:
        city = v.city if v.city else 'N/A'
        isp = v.isp if v.isp else 'N/A'
        ua = v.user_agent[:80] if v.user_agent else 'N/A'
        print(f'{v.visited_at} | is_bot={v.is_bot}')
        print(f'  City: {city:20} | ISP: {isp}')
        print(f'  UA: {ua}')
        print('-'*100)
    
    print()
    print('='*100)
    
    # Recherche large pour Starlink/SpaceX
    starlink_all = VisitorLog.query.filter(
        VisitorLog.visited_at >= recent
    ).filter(
        db.or_(
            VisitorLog.isp.like('%Starlink%'),
            VisitorLog.isp.like('%SpaceX%'),
            VisitorLog.isp.like('%Space Exploration%')
        )
    ).order_by(VisitorLog.visited_at.desc()).limit(10).all()
    
    print(f'📡 Visites Starlink/SpaceX (toutes, 48h): {len(starlink_all)}')
    for v in starlink_all:
        bot_label = 'BOT' if v.is_bot else 'HUMAIN'
        print(f'{bot_label:7} | {v.visited_at} | {v.isp} | {v.city}')
