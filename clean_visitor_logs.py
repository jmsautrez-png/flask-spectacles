"""
Script de nettoyage des données de tracking (Conformité RGPD)

1. Résume dans visitor_daily_stat chaque journée complète (UTC) pas encore résumée.
2. Supprime les logs bruts et les lignes « user » (par compte) de plus de 90 jours.
3. Supprime les totaux anonymes antérieurs au 1er janvier de l'année précédente
   (l'année en cours et l'année précédente restent consultables).

À exécuter régulièrement (quotidien recommandé) via cron ou planificateur de tâches.
"""
from app import app, db
from models.models import VisitorLog, VisitorDailyStat
from datetime import date, datetime, time as dt_time, timedelta
from sqlalchemy import func


def date_debut_resumes(maintenant):
    """Premier jour conservé dans visitor_daily_stat : 1er janvier de l'année précédente."""
    return date(maintenant.year - 1, 1, 1)


def resumer_jours_manquants(maintenant):
    """Résume les jours complets (avant aujourd'hui UTC) absents de visitor_daily_stat.

    Le marqueur d'avancement est la ligne total_human du dernier jour résumé :
    chaque jour écrit toujours ses deux lignes total_*, même sans visite.
    Retourne le nombre de jours résumés.
    """
    aujourd_hui = maintenant.date()
    dernier = db.session.query(func.max(VisitorDailyStat.day)).filter(
        VisitorDailyStat.kind == "total_human"
    ).scalar()
    if dernier is None:
        premier = db.session.query(func.min(VisitorLog.visited_at)).scalar()
        if premier is None:
            return 0
        jour = premier.date()
    else:
        jour = dernier + timedelta(days=1)

    nb_jours = 0
    while jour < aujourd_hui:
        debut = datetime.combine(jour, dt_time())
        filtre = (VisitorLog.visited_at >= debut, VisitorLog.visited_at < debut + timedelta(days=1))
        humain = VisitorLog.is_bot == False  # noqa: E712

        totaux = {"total_bot": (0, 0), "total_human": (0, 0)}
        for est_bot, hits, sessions in db.session.query(
            VisitorLog.is_bot,
            func.count(VisitorLog.id),
            func.count(func.distinct(VisitorLog.session_id)),
        ).filter(*filtre).group_by(VisitorLog.is_bot):
            totaux["total_bot" if est_bot else "total_human"] = (hits, sessions)

        lignes = [
            VisitorDailyStat(day=jour, kind=kind, hits=hits, sessions=sessions)
            for kind, (hits, sessions) in totaux.items()
        ]
        for url, hits in db.session.query(VisitorLog.page_url, func.count(VisitorLog.id)).filter(
            *filtre, humain
        ).group_by(VisitorLog.page_url):
            lignes.append(VisitorDailyStat(day=jour, kind="page", key=url, hits=hits))
        for ref, hits in db.session.query(VisitorLog.referrer, func.count(VisitorLog.id)).filter(
            *filtre, humain, VisitorLog.referrer.isnot(None)
        ).group_by(VisitorLog.referrer):
            lignes.append(VisitorDailyStat(day=jour, kind="referrer", key=ref, hits=hits))
        for uid, hits in db.session.query(VisitorLog.user_id, func.count(VisitorLog.id)).filter(
            *filtre, humain, VisitorLog.user_id.isnot(None)
        ).group_by(VisitorLog.user_id):
            lignes.append(VisitorDailyStat(day=jour, kind="user", key=str(uid), hits=hits))

        db.session.add_all(lignes)
        db.session.commit()
        nb_jours += 1
        jour += timedelta(days=1)
    return nb_jours


def supprimer_logs_bruts(date_limit):
    """Supprime les logs antérieurs à date_limit, un jour à la fois.

    Une petite transaction par jour : une coupure réseau (SSL) pendant un DELETE
    géant ne perd pas le travail déjà fait, et la relance reprend où elle s'était arrêtée.
    Retourne le nombre de logs supprimés.
    """
    premier = db.session.query(func.min(VisitorLog.visited_at)).scalar()
    if premier is None:
        return 0
    total = 0
    jour = datetime.combine(premier.date(), dt_time())
    while jour < date_limit:
        fin = min(jour + timedelta(days=1), date_limit)
        total += VisitorLog.query.filter(
            VisitorLog.visited_at >= jour, VisitorLog.visited_at < fin
        ).delete(synchronize_session=False)
        db.session.commit()
        jour = fin
    return total


def clean_old_visitor_logs(days=90):
    """Résume les jours manquants, puis supprime les logs bruts de plus de X jours
    et les lignes par compte (kind 'user') de plus de X jours.
    Les totaux anonymes sont gardés depuis le 1er janvier de l'année précédente."""
    with app.app_context():
        maintenant = datetime.utcnow()
        nb_resumes = resumer_jours_manquants(maintenant)
        print(f"📈 {nb_resumes} journée(s) résumée(s) dans visitor_daily_stat.")

        date_limit = maintenant - timedelta(days=days)

        count = supprimer_logs_bruts(date_limit)
        VisitorDailyStat.query.filter(
            VisitorDailyStat.kind == "user", VisitorDailyStat.day < date_limit.date()
        ).delete(synchronize_session=False)
        VisitorDailyStat.query.filter(
            VisitorDailyStat.day < date_debut_resumes(maintenant)
        ).delete(synchronize_session=False)
        db.session.commit()

        if count == 0:
            print(f"✅ Aucune donnée de plus de {days} jours à supprimer.")
            return

        print(f"✅ {count} enregistrements de plus de {days} jours supprimés.")
        print(f"📊 Conformité RGPD : Données nettoyées le {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')}")

if __name__ == "__main__":
    print("🗑️  Nettoyage des données de tracking...")
    clean_old_visitor_logs(90)  # Supprimer les données de plus de 90 jours
