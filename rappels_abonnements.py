"""Script quotidien : rappels d'expiration abonnement AO + désactivation auto + email admin.

Flow pour chaque User abonné (is_subscribed=True) :
    - Si subscribed_until arrive dans ~30 jours (fenêtre 28-32) et pas déjà notifié → email J-30
    - Si subscribed_until arrive dans ~7 jours (fenêtre 5-9) et pas déjà notifié → email J-7
    - Si subscribed_until est passé et pas déjà notifié → email d'expiration + désactivation is_subscribed
    - Si abonnement expiré depuis > 1 jour et toujours is_subscribed=True → désactivation forcée

Idempotence : chaque envoi stocke subscribed_until dans renewal_*_sent_for pour éviter les doublons.
Un renouvellement par admin remet subscribed_until à une nouvelle date → le tracking est automatiquement périmé.

Usage :
    # Dry-run (par défaut, aucune modification)
    python rappels_abonnements.py

    # Appliquer réellement (envoi des emails + désactivation)
    python rappels_abonnements.py --apply

    # Appliquer sans envoyer d'email (test ou maintenance)
    python rappels_abonnements.py --apply --no-email

    # Appliquer sans envoyer le récap admin
    python rappels_abonnements.py --apply --skip-admin-recap

Lancement en cron (Render) :
    - Crée un Cron Job Render
    - Build Command : pip install -r requirements.txt
    - Command : python rappels_abonnements.py --apply
    - Schedule : 0 7 * * * (= tous les jours à 7h UTC = 9h Paris)
    - Même DATABASE_URL + MAIL_* que le web service

IMPORTANT : pour cibler la base de PRODUCTION, positionner DATABASE_URL AVANT le lancement.
"""
import argparse
from datetime import datetime, timedelta

from app import app, db
from models.models import User

try:
    from flask_mail import Message as MailMessage  # type: ignore
except Exception:
    MailMessage = None  # type: ignore


PAYPAL_URL = "https://paypal.me/SpectaclementVotre"
TARIF_RENOUVELLEMENT = 99  # €
WEBSITE_URL = "https://www.spectacleanimation.fr"


def _send_mail(recipient, subject, html):
    """Envoie un email HTML. Silencieux si Flask-Mail non configuré."""
    if MailMessage is None:
        return False
    if not getattr(app, "mail", None):
        return False
    if not app.config.get("MAIL_USERNAME"):
        return False
    try:
        msg = MailMessage(subject=subject, recipients=[recipient])
        msg.html = html
        app.mail.send(msg)  # type: ignore[attr-defined]
        return True
    except Exception as e:
        print(f"        [MAIL] envoi echoue a {recipient} : {e}")
        return False


def _html_rappel_j30(user, date_fin):
    paypal_link = f"{PAYPAL_URL}/{TARIF_RENOUVELLEMENT}EUR"
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;color:#333;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#1976d2,#1565c0);color:#fff;padding:22px;text-align:center;">
      <h2 style="margin:0;">📅 Votre abonnement arrive à échéance</h2>
    </div>
    <div style="padding:24px;line-height:1.55;">
      <p>Bonjour <strong>{user.raison_sociale or user.username}</strong>,</p>
      <p>Votre abonnement <strong>« Appels d'offres »</strong> sur Spectacle'ment Vôtre expire dans <strong>environ 30 jours</strong>, le <strong>{date_fin.strftime('%d/%m/%Y')}</strong>.</p>
      <p>Pour continuer à recevoir les appels d'offres de nos partenaires (mairies, écoles, CSE…) sans interruption, renouvelez dès maintenant votre abonnement pour une nouvelle année : <strong>{TARIF_RENOUVELLEMENT} €</strong>.</p>
      <div style="text-align:center;margin:28px 0;">
        <a href="{paypal_link}" target="_blank"
           style="display:inline-block;background:linear-gradient(135deg,#003087,#009cde);color:#fff;padding:14px 32px;border-radius:30px;text-decoration:none;font-weight:700;font-size:1.05rem;box-shadow:0 3px 10px rgba(0,48,135,0.3);">
          Renouveler pour {TARIF_RENOUVELLEMENT} € avec PayPal
        </a>
      </div>
      <p style="font-size:0.88rem;color:#666;">Ou contactez-nous à <a href="mailto:contact@spectacleanimation.fr">contact@spectacleanimation.fr</a> pour un virement bancaire.</p>
      <p>Après paiement, votre abonnement sera prolongé automatiquement par notre équipe sous 24h.</p>
      <p style="margin-top:20px;color:#555;">Cordialement,<br>L'équipe <strong>Spectacle'ment Vôtre</strong></p>
    </div>
  </div>
</body></html>"""


def _html_rappel_j7(user, date_fin):
    paypal_link = f"{PAYPAL_URL}/{TARIF_RENOUVELLEMENT}EUR"
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;color:#333;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#ef6c00,#e65100);color:#fff;padding:22px;text-align:center;">
      <h2 style="margin:0;">⚠️ Dernière semaine avant expiration</h2>
    </div>
    <div style="padding:24px;line-height:1.55;">
      <p>Bonjour <strong>{user.raison_sociale or user.username}</strong>,</p>
      <p>Votre abonnement « Appels d'offres » expire dans <strong>moins d'une semaine</strong>, le <strong>{date_fin.strftime('%d/%m/%Y')}</strong>.</p>
      <p style="background:#fff3e0;border-left:4px solid #ff9800;padding:12px 16px;border-radius:6px;">
        <strong>Après cette date</strong>, l'accès aux appels d'offres sera désactivé automatiquement.
      </p>
      <p>Renouvelez dès maintenant pour <strong>{TARIF_RENOUVELLEMENT} €</strong> et conservez votre accès sans coupure :</p>
      <div style="text-align:center;margin:28px 0;">
        <a href="{paypal_link}" target="_blank"
           style="display:inline-block;background:linear-gradient(135deg,#003087,#009cde);color:#fff;padding:14px 32px;border-radius:30px;text-decoration:none;font-weight:700;font-size:1.05rem;box-shadow:0 3px 10px rgba(0,48,135,0.3);">
          Renouveler maintenant — {TARIF_RENOUVELLEMENT} €
        </a>
      </div>
      <p style="font-size:0.88rem;color:#666;">Besoin d'aide ? Contactez-nous à <a href="mailto:contact@spectacleanimation.fr">contact@spectacleanimation.fr</a>.</p>
      <p style="margin-top:20px;color:#555;">Cordialement,<br>L'équipe <strong>Spectacle'ment Vôtre</strong></p>
    </div>
  </div>
</body></html>"""


def _html_rappel_expired(user, date_fin):
    paypal_link = f"{PAYPAL_URL}/{TARIF_RENOUVELLEMENT}EUR"
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;color:#333;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#c62828,#b71c1c);color:#fff;padding:22px;text-align:center;">
      <h2 style="margin:0;">🔒 Votre abonnement est arrivé à échéance</h2>
    </div>
    <div style="padding:24px;line-height:1.55;">
      <p>Bonjour <strong>{user.raison_sociale or user.username}</strong>,</p>
      <p>Votre abonnement « Appels d'offres » a expiré le <strong>{date_fin.strftime('%d/%m/%Y')}</strong>. L'accès aux appels d'offres est <strong>temporairement désactivé</strong>.</p>
      <p>Pour <strong>réactiver</strong> votre accès et retrouver tous les nouveaux appels d'offres de nos partenaires, renouvelez votre abonnement pour <strong>{TARIF_RENOUVELLEMENT} €</strong> :</p>
      <div style="text-align:center;margin:28px 0;">
        <a href="{paypal_link}" target="_blank"
           style="display:inline-block;background:linear-gradient(135deg,#003087,#009cde);color:#fff;padding:14px 32px;border-radius:30px;text-decoration:none;font-weight:700;font-size:1.05rem;box-shadow:0 3px 10px rgba(0,48,135,0.3);">
          Réactiver mon abonnement — {TARIF_RENOUVELLEMENT} €
        </a>
      </div>
      <p>Notre équipe réactivera votre accès sous 24h après réception du paiement.</p>
      <p style="font-size:0.88rem;color:#666;">Pour un virement bancaire ou toute question : <a href="mailto:contact@spectacleanimation.fr">contact@spectacleanimation.fr</a>.</p>
      <p style="margin-top:20px;color:#555;">Cordialement,<br>L'équipe <strong>Spectacle'ment Vôtre</strong></p>
    </div>
  </div>
</body></html>"""


def _html_recap_admin(stats):
    rows = ""
    for label, users in [
        ("🟡 Rappels J-30 envoyés", stats["j30"]),
        ("🟠 Rappels J-7 envoyés", stats["j7"]),
        ("🔴 Expirés notifiés + désactivés", stats["expired"]),
        ("⚪ Déjà désactivés précédemment", stats["already_expired"]),
    ]:
        rows += f"<tr><td style='padding:8px;color:#333;border-bottom:1px solid #eee;'><strong>{label}</strong></td><td style='padding:8px;border-bottom:1px solid #eee;text-align:right;font-size:1.1em;font-weight:700;'>{len(users)}</td></tr>"
        if users:
            lignes = "".join(
                f"<li style='padding:3px 0;color:#555;'>{u.raison_sociale or u.username} · {u.email or '—'} · expire {u.subscribed_until.strftime('%d/%m/%Y') if u.subscribed_until else '—'}</li>"
                for u in users
            )
            rows += f"<tr><td colspan='2' style='padding:0 8px 10px 24px;'><ul style='margin:4px 0;font-size:0.85em;'>{lignes}</ul></td></tr>"

    if not rows:
        rows = "<tr><td style='padding:20px;text-align:center;color:#999;'>Aucune action aujourd&rsquo;hui.</td></tr>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;color:#333;">
  <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:#455a64;color:#fff;padding:18px;text-align:center;">
      <h2 style="margin:0;">📊 Récap quotidien — Rappels abonnement AO</h2>
      <p style="margin:4px 0 0 0;opacity:0.85;font-size:0.9rem;">Exécuté le {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}</p>
    </div>
    <div style="padding:20px;">
      <table style="width:100%;border-collapse:collapse;">
        {rows}
      </table>
      <p style="margin-top:18px;font-size:0.85rem;color:#777;text-align:center;">
        Pour voir le dashboard complet : <a href="{WEBSITE_URL}/admin/abonnements-a-renouveler" style="color:#1976d2;">tableau abonnements</a>
      </p>
    </div>
  </div>
</body></html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Rappels quotidiens abonnement AO + désactivation auto.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--apply", action="store_true",
                        help="Applique réellement (sinon dry-run par défaut).")
    parser.add_argument("--no-email", action="store_true",
                        help="N'envoie aucun email aux utilisateurs (utile pour test local).")
    parser.add_argument("--skip-admin-recap", action="store_true",
                        help="N'envoie pas le récap admin.")
    args = parser.parse_args()

    stats = {"j30": [], "j7": [], "expired": [], "already_expired": []}

    with app.app_context():
        now = datetime.utcnow()
        # Fenêtres de tolérance pour attraper les cron qui auraient manqué un jour
        j30_min = now + timedelta(days=28)
        j30_max = now + timedelta(days=32)
        j7_min = now + timedelta(days=5)
        j7_max = now + timedelta(days=9)

        candidats = (
            User.query
            .filter(User.subscribed_until.isnot(None))
            .filter(User.is_admin.is_(False))
            .all()
        )

        print()
        print("=" * 90)
        print(f"RAPPELS ABONNEMENT AO — {now.strftime('%d/%m/%Y %H:%M UTC')}")
        if not args.apply:
            print("MODE DRY-RUN (aucune modification, aucun email)")
        print("=" * 90)
        print(f"Utilisateurs avec date d'abonnement : {len(candidats)}")
        print()

        for u in candidats:
            sub_until = u.subscribed_until
            if sub_until is None:
                continue

            # --- Expiration déjà passée ---
            if sub_until < now:
                # Pas encore notifié pour cette période ?
                if u.renewal_expired_sent_for != sub_until:
                    stats["expired"].append(u)
                    print(f"  🔴 EXPIRE : {u.username} (fin {sub_until.strftime('%d/%m/%Y')})")
                    if args.apply:
                        if not args.no_email and u.email:
                            if _send_mail(u.email,
                                          "🔒 Votre abonnement Appels d'offres a expiré",
                                          _html_rappel_expired(u, sub_until)):
                                print(f"        [OK] Email expiration envoye a {u.email}")
                        u.renewal_expired_sent_for = sub_until
                        # Désactivation auto (Niveau 3)
                        if u.is_subscribed:
                            u.is_subscribed = False
                            print("        [OK] is_subscribed desactive")
                else:
                    # Déjà notifié : s'assurer que is_subscribed est bien False (safety net)
                    if u.is_subscribed:
                        stats["already_expired"].append(u)
                        print(f"  ⚪ Deja expire mais toujours is_subscribed=True : {u.username}")
                        if args.apply:
                            u.is_subscribed = False
                            print("        [OK] is_subscribed desactive (safety)")
                continue

            # --- J-7 (fenêtre 5-9 jours) ---
            if j7_min <= sub_until <= j7_max:
                if u.renewal_j7_sent_for != sub_until:
                    stats["j7"].append(u)
                    nb_jours = (sub_until - now).days
                    print(f"  🟠 J-7 : {u.username} (expire dans {nb_jours}j, le {sub_until.strftime('%d/%m/%Y')})")
                    if args.apply:
                        if not args.no_email and u.email:
                            if _send_mail(u.email,
                                          f"⚠️ Dernière semaine : abonnement AO expire le {sub_until.strftime('%d/%m/%Y')}",
                                          _html_rappel_j7(u, sub_until)):
                                print(f"        [OK] Email J-7 envoye a {u.email}")
                        u.renewal_j7_sent_for = sub_until
                continue

            # --- J-30 (fenêtre 28-32 jours) ---
            if j30_min <= sub_until <= j30_max:
                if u.renewal_j30_sent_for != sub_until:
                    stats["j30"].append(u)
                    nb_jours = (sub_until - now).days
                    print(f"  🟡 J-30 : {u.username} (expire dans {nb_jours}j, le {sub_until.strftime('%d/%m/%Y')})")
                    if args.apply:
                        if not args.no_email and u.email:
                            if _send_mail(u.email,
                                          f"📅 Votre abonnement AO expire le {sub_until.strftime('%d/%m/%Y')}",
                                          _html_rappel_j30(u, sub_until)):
                                print(f"        [OK] Email J-30 envoye a {u.email}")
                        u.renewal_j30_sent_for = sub_until
                continue

        if args.apply:
            db.session.commit()

        # --- Récap admin ---
        print()
        print("=" * 90)
        print("RECAP")
        print(f"  J-30 traites       : {len(stats['j30'])}")
        print(f"  J-7 traites        : {len(stats['j7'])}")
        print(f"  Expirations notif. : {len(stats['expired'])}")
        print(f"  Deja expires (safety desactivation) : {len(stats['already_expired'])}")
        print("=" * 90)

        total = sum(len(v) for v in stats.values())
        if args.apply and not args.skip_admin_recap and total > 0:
            admin_addr = app.config.get("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_USERNAME")
            if admin_addr:
                if _send_mail(admin_addr,
                              f"[Récap AO] {total} action(s) aujourd'hui — J-30:{len(stats['j30'])} J-7:{len(stats['j7'])} Expirés:{len(stats['expired'])}",
                              _html_recap_admin(stats)):
                    print(f"[RECAP ADMIN] Email envoye a {admin_addr}")
                else:
                    print("[RECAP ADMIN] Envoi echoue")
        elif not args.apply:
            print()
            print("DRY-RUN termine. Pour appliquer : relancez avec --apply.")


if __name__ == "__main__":
    main()
