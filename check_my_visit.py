"""Script pour vérifier les visites Starlink et humaines récentes"""
from app import app, db
from models.models import VisitorLog
from datetime import datetime, timedelta, timezone

with app.app_context():
    # Dernières 24 heures
    recent = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # Visites Starlink/SpaceX
    starlink_visits = VisitorLog.query.filter(
        VisitorLog.visited_at >= recent,
        VisitorLog.isp.like('%SpaceX%')
    ).order_by(VisitorLog.visited_at.desc()).limit(10).all()
    
    print(f'📡 Visites Starlink (24h): {len(starlink_visits)}')
    for v in starlink_visits[:10]:
        bot_label = 'BOT' if v.is_bot else 'HUMAIN'
        city = v.city if v.city else 'N/A'
        print(f'{bot_label:7} | {v.visited_at} | {city:15} | is_bot={v.is_bot}')
    
    print()
    
    # Dernières visites HUMAINES (peu importe ISP)
    human_visits = VisitorLog.query.filter(
        VisitorLog.visited_at >= recent,
        VisitorLog.is_bot == False
    ).order_by(VisitorLog.visited_at.desc()).limit(10).all()
    
    print(f'👤 Dernières visites HUMAINES (24h): {len(human_visits)}')
    for v in human_visits[:10]:
        city = v.city if v.city else 'N/A'
        isp = v.isp[:50] if v.isp else 'N/A'
        print(f'  {v.visited_at} | {city:15} | {isp}')
