"""
Script pour reclassifier les visiteurs en bots/humains
avec la nouvelle détection stricte

Ce script :
1. Applique la nouvelle fonction is_bot_visitor() à tous les logs existants
2. Met à jour la colonne is_bot dans la base de données
3. Affiche les statistiques avant/après
"""
import sys
from app import app, db
from models.models import VisitorLog

def is_bot_visitor(user_agent: str, isp: str = None) -> bool:
    """Détection stricte des bots avec LISTE BLANCHE (copie exacte de app.py v3)"""
    if not user_agent:
        return False
    
    user_agent_lower = user_agent.lower()
    
    # Liste des patterns de robots connus dans User-Agent
    bot_patterns = [
        'bot', 'crawler', 'spider', 'scraper', 'slurp', 'mediapartners',
        'googlebot', 'bingbot', 'yandexbot', 'baiduspider', 'facebookexternalhit',
        'twitterbot', 'linkedinbot', 'whatsapp', 'telegrambot', 'discordbot',
        'slackbot', 'pinterestbot', 'applebot', 'duckduckbot', 'ahrefsbot',
        'semrushbot', 'mj12bot', 'dotbot', 'rogerbot', 'exabot', 'sogou', 
        'archive.org', 'wget', 'curl', 'python-requests', 'java/', 'go-http',
        'phantom', 'headless', 'selenium', 'webdriver', 'prerender'
    ]
    
    # Vérifier si un pattern de bot est présent dans le User-Agent
    for pattern in bot_patterns:
        if pattern in user_agent_lower:
            return True
    
    # APPROCHE LISTE BLANCHE : Si pas d'ISP ou ISP inconnu = BOT
    if not isp or isp == 'N/A':
        return True  # Pas d'ISP identifié = suspect
    
    isp_lower = isp.lower()
    
    # Détection des IPs brutes (non résolues) → TOUJOURS des bots
    import re
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', isp.strip()):
        return True  # IP non résolue = bot/proxy/datacenter
    
    # LISTE BLANCHE : FAI français résidentiels UNIQUEMENT
    # Tout ce qui n'est PAS dans cette liste = BOT
    trusted_french_isps = [
        # Opérateurs principaux
        'orange',
        'proxad',  # Free
        'free sas',
        'free telecom',
        'sfr',
        'societe francaise du radiotelephone',
        'bouygues',
        'numericable',
        
        # Opérateurs secondaires français
        'la poste mobile',
        'transatel',
        'lycamobile',
        'nrj mobile',
        'coriolis',
        'completel',
        'neuf',
        'cegetel',
        'iliad',  # Maison-mère de Free
        'outremer telecom',
        
        # FAI régionaux français
        'alsatis',
        'auchan telecom',
        'adista',
        'netissime',
        'ielo',
        'k-net'
    ]
    
    # Vérifier si l'ISP est dans la liste blanche
    for trusted_isp in trusted_french_isps:
        if trusted_isp in isp_lower:
            return False  # ISP français reconnu = HUMAIN
    
    # Si on arrive ici : ISP inconnu/étranger = BOT
    return True

def reclassify_all_visitors():
    """Reclassifie tous les visiteurs avec la nouvelle détection stricte"""
    with app.app_context():
        print("🔍 Récupération de tous les logs de visiteurs...")
        all_visitors = VisitorLog.query.all()
        total = len(all_visitors)
        print(f"📊 Total de visiteurs: {total}")
        
        # Statistiques avant
        bots_before = VisitorLog.query.filter_by(is_bot=True).count()
        humans_before = VisitorLog.query.filter_by(is_bot=False).count()
        print(f"\n📈 AVANT reclassification:")
        print(f"   Bots: {bots_before} ({bots_before/total*100:.1f}%)")
        print(f"   Humains: {humans_before} ({humans_before/total*100:.1f}%)")
        
        # Reclassification
        print(f"\n🔄 Reclassification en cours...")
        changed_to_bot = 0
        changed_to_human = 0
        unchanged = 0
        
        for i, visitor in enumerate(all_visitors):
            # Afficher progression tous les 100 entrées
            if (i + 1) % 100 == 0:
                print(f"   Traitement: {i+1}/{total}...")
            
            # Calculer nouvelle classification
            new_is_bot = is_bot_visitor(visitor.user_agent, visitor.isp)
            
            # Détecter changements
            if visitor.is_bot and not new_is_bot:
                changed_to_human += 1
                if changed_to_human <= 5:  # Afficher les 5 premiers
                    print(f"   ⚠️  BOT → HUMAIN: {visitor.isp[:50] if visitor.isp else 'N/A'}")
            elif not visitor.is_bot and new_is_bot:
                changed_to_bot += 1
                if changed_to_bot <= 10:  # Afficher les 10 premiers
                    print(f"   ✅ HUMAIN → BOT: {visitor.isp[:50] if visitor.isp else 'N/A'}")
            else:
                unchanged += 1
            
            # Mettre à jour
            visitor.is_bot = new_is_bot
        
        # Sauvegarder les changements
        print(f"\n💾 Sauvegarde des changements dans la base de données...")
        db.session.commit()
        
        # Statistiques après
        bots_after = VisitorLog.query.filter_by(is_bot=True).count()
        humans_after = VisitorLog.query.filter_by(is_bot=False).count()
        
        print(f"\n📈 APRÈS reclassification:")
        print(f"   Bots: {bots_after} ({bots_after/total*100:.1f}%)")
        print(f"   Humains: {humans_after} ({humans_after/total*100:.1f}%)")
        
        print(f"\n📊 CHANGEMENTS:")
        print(f"   Humain → Bot: {changed_to_bot}")
        print(f"   Bot → Humain: {changed_to_human}")
        print(f"   Inchangés: {unchanged}")
        
        print(f"\n✅ Reclassification terminée!")
        
        # Afficher quelques exemples de bots détectés
        print(f"\n🤖 Exemples de BOTS détectés (10 premiers):")
        sample_bots = VisitorLog.query.filter_by(is_bot=True).limit(10).all()
        for bot in sample_bots:
            print(f"   - ISP: {bot.isp[:60] if bot.isp else 'N/A'}")
            print(f"     User-Agent: {bot.user_agent[:100] if bot.user_agent else 'N/A'}...")
            print()

if __name__ == '__main__':
    print("=" * 80)
    print("🤖 RECLASSIFICATION DES BOTS/HUMAINS")
    print("=" * 80)
    print()
    
    response = input("⚠️  Cette action va modifier TOUS les logs. Continuer? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        reclassify_all_visitors()
    else:
        print("❌ Opération annulée")
