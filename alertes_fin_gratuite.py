"""Script quotidien : alerte admin 1 mois avant la fin de l'accès gratuit d'un an.

Concerne les comptes créés avant MODELE_PAYANT_DEBUT (12/09/2026) : fin = date de création + 1 an.
Pour chaque compte dont la fin tombe dans les 30 prochains jours, un seul mail est envoyé à l'administrateur.
Les comptes dont la fin est déjà passée ne sont pas alertés : ils sont seulement listés en dry-run.

Idempotence : User.fin_gratuite_alerte_sent_for stocke la date de fin alertée.
Un envoi échoué n'est pas enregistré : il sera retenté au passage suivant.

Usage :
    # Dry-run (par défaut, aucune modification, aucun email)
    python alertes_fin_gratuite.py

    # Appliquer réellement (envoi des alertes)
    python alertes_fin_gratuite.py --apply

Lancement en cron (Render) :
    - Command : python alertes_fin_gratuite.py --apply
    - Schedule : 0 8 * * * (= tous les jours à 8h UTC)
    - Même DATABASE_URL + MAIL_* que le web service
"""
import argparse
from datetime import datetime, timedelta

from app import app, db
from models.models import User, MODELE_PAYANT_DEBUT
from rappels_abonnements import _send_mail, WEBSITE_URL

JOURS_AVANT_FIN = 30


def date_fin_gratuite(created_at):
    """Fin de l'accès gratuit : même jour un an après la création (29 février → 28 février)."""
    try:
        return created_at.replace(year=created_at.year + 1)
    except ValueError:
        return created_at.replace(year=created_at.year + 1, day=28)


def comptes_a_suivre(now):
    """Retourne (a_alerter, deja_passes) : listes de (user, date_fin)."""
    a_alerter, deja_passes = [], []
    anciens = (
        User.query
        .filter(User.created_at.isnot(None), User.created_at < MODELE_PAYANT_DEBUT)
        .order_by(User.created_at)
        .all()
    )
    for user in anciens:
        if user.is_admin:
            continue
        fin = date_fin_gratuite(user.created_at)
        if fin <= now:
            deja_passes.append((user, fin))
        elif fin - timedelta(days=JOURS_AVANT_FIN) <= now and user.fin_gratuite_alerte_sent_for != fin:
            a_alerter.append((user, fin))
    return a_alerter, deja_passes


def _html_alerte(user, fin, jours):
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;color:#333;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:#ef6c00;color:#fff;padding:18px;text-align:center;">
      <h2 style="margin:0;">Fin de l'accès gratuit dans {jours} jours</h2>
    </div>
    <div style="padding:20px;line-height:1.55;">
      <p>Le compte <strong>{user.username}</strong> a été créé le {user.created_at.strftime('%d/%m/%Y')} (avant le modèle payant). Son accès gratuit d'un an se termine le <strong>{fin.strftime('%d/%m/%Y')}</strong>.</p>
      <p>Raison sociale : {user.raison_sociale or '—'}<br>
         Email : {user.email or '—'}<br>
         Téléphone : {user.telephone or '—'}</p>
      <p>Il est temps de décider ce qui se passe à cette date (voir la CGU et le bandeau « accès libre »).</p>
      <p style="text-align:center;margin-top:24px;">
        <a href="{WEBSITE_URL}/admin/users" style="color:#1976d2;">Voir les utilisateurs</a>
      </p>
    </div>
  </div>
</body></html>"""


def traiter(now, apply, envoyer=_send_mail, admin_addr=None):
    """Envoie les alertes dues. Retourne les compteurs {'alertes', 'deja_passes'}.

    En dry-run, les compteurs indiquent ce qui serait envoyé. Rien n'est enregistré.
    """
    a_alerter, deja_passes = comptes_a_suivre(now)

    for user, fin in a_alerter:
        jours = (fin - now).days
        print(f"  ⏰ Fin gratuité dans {jours} j : {user.username} · {user.email} · créé le {user.created_at:%d/%m/%Y} · fin le {fin:%d/%m/%Y}")
        if apply:
            if not admin_addr:
                print("        [ECHEC] aucune adresse admin configurée (MAIL_DEFAULT_SENDER / MAIL_USERNAME)")
                continue
            sujet = f"[Fin gratuité] {user.username} : accès gratuit terminé le {fin:%d/%m/%Y}"
            if envoyer(admin_addr, sujet, _html_alerte(user, fin, jours)):
                user.fin_gratuite_alerte_sent_for = fin
                print("        [OK] alerte envoyée à l'admin")
            else:
                print("        [ECHEC] alerte non envoyée, nouvelle tentative au prochain passage")

    for user, fin in deja_passes:
        print(f"  ⚠️ Fin déjà passée (non alerté) : {user.username} · créé le {user.created_at:%d/%m/%Y} · fin le {fin:%d/%m/%Y}")

    if apply:
        db.session.commit()

    return {"alertes": len(a_alerter), "deja_passes": len(deja_passes)}


def main():
    parser = argparse.ArgumentParser(
        description="Alerte admin 1 mois avant la fin de l'accès gratuit d'un an (comptes d'avant le modèle payant).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--apply", action="store_true",
                        help="Envoie réellement les alertes (sinon dry-run par défaut).")
    args = parser.parse_args()

    with app.app_context():
        now = datetime.utcnow()
        admin_addr = app.config.get("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_USERNAME")

        print()
        print("=" * 90)
        print(f"ALERTES FIN ACCES GRATUIT — {now.strftime('%d/%m/%Y %H:%M UTC')}")
        if not args.apply:
            print("MODE DRY-RUN (aucune modification, aucun email)")
        print("=" * 90)

        stats = traiter(now, args.apply, admin_addr=admin_addr)

        print()
        print(f"Alertes admin dues : {stats['alertes']} · Comptes déjà passés (non alertés) : {stats['deja_passes']}")


if __name__ == "__main__":
    main()
