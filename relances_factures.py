"""Script quotidien : relances des factures d'adhésion AO impayées.

Pour chaque Adhesion dont la facture a été envoyée (statut « contacted ») mais non activée
ni rejetée :
    - J+3 après l'envoi de la facture : rappel au client
    - J+7 : second rappel au client (remplace le J+3 s'il n'a pas pu partir)
    - J+10 : alerte à l'administrateur (aucun mail au client)

Idempotence : chaque envoi stocke invoice_sent_at dans relance_*_sent_for / alerte_admin_j10_sent_for.
Une nouvelle émission de facture change invoice_sent_at et relance donc le cycle.
Un envoi échoué n'est pas enregistré : il sera retenté au passage suivant.

Usage :
    # Dry-run (par défaut, aucune modification, aucun email)
    python relances_factures.py

    # Appliquer réellement (envoi des relances et de l'alerte)
    python relances_factures.py --apply

Lancement en cron (Render) :
    - Command : python relances_factures.py --apply
    - Schedule : 0 8 * * * (= tous les jours à 8h UTC = 9h/10h Paris)
    - Même DATABASE_URL + MAIL_* que le web service
"""
import argparse
from datetime import datetime

from app import app, db, _adhesion_frais_paypal
from models.models import Adhesion
from rappels_abonnements import _send_mail, PAYPAL_URL, WEBSITE_URL

JOURS_RELANCE_1 = 3
JOURS_RELANCE_2 = 7
JOURS_ALERTE_ADMIN = 10
EMAIL_CONTACT = "laureline@spectacleanimation.fr"


def actions_dues(adh, now):
    """Retourne (relance, alerte) pour une facture.

    relance : 'j7', 'j3' ou None (une seule relance client par passage).
    alerte  : True si l'alerte admin J+10 est à envoyer.
    """
    if (
        adh.statut != "contacted"
        or adh.invoice_sent_at is None
        or adh.activated_at is not None
        or adh.rejected_at is not None
    ):
        return None, False

    envoi = adh.invoice_sent_at
    jours = (now - envoi).total_seconds() / 86400

    relance = None
    if jours >= JOURS_RELANCE_2 and adh.relance_j7_sent_for != envoi:
        relance = "j7"
    elif (
        jours >= JOURS_RELANCE_1
        and adh.relance_j3_sent_for != envoi
        and adh.relance_j7_sent_for != envoi
    ):
        relance = "j3"

    alerte = jours >= JOURS_ALERTE_ADMIN and adh.alerte_admin_j10_sent_for != envoi
    return relance, alerte


def _html_relance(adh, amount, invoice_number, date_envoi, dernier):
    frais_paypal = _adhesion_frais_paypal(adh)
    paypal_amount = amount + frais_paypal
    titre = "Dernier rappel" if dernier else "Rappel"
    dernier_txt = "<p>Ceci est notre <strong>dernier rappel automatique</strong>.</p>" if dernier else ""
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;color:#333;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#6a1b9a,#4a148c);color:#fff;padding:22px;text-align:center;">
      <h2 style="margin:0;">{titre} : facture en attente de règlement</h2>
    </div>
    <div style="padding:24px;line-height:1.55;">
      <p>Bonjour <strong>{adh.nom}</strong>,</p>
      <p>Nous vous avons envoyé le {date_envoi.strftime('%d/%m/%Y')} la facture n° <strong>{invoice_number}</strong> pour votre abonnement « Appels d'offres » ({amount} €). Nous n'avons pas encore reçu votre règlement.</p>
      {dernier_txt}
      <p><strong>Par PayPal</strong> (le plus rapide) : {paypal_amount} € ({amount} € + {frais_paypal} € de frais PayPal).</p>
      <div style="text-align:center;margin:24px 0;">
        <a href="{PAYPAL_URL}/{paypal_amount}EUR" target="_blank"
           style="display:inline-block;background:linear-gradient(135deg,#003087,#009cde);color:#fff;padding:14px 32px;border-radius:30px;text-decoration:none;font-weight:700;font-size:1.05rem;box-shadow:0 3px 10px rgba(0,48,135,0.3);">
          Payer {paypal_amount} € avec PayPal
        </a>
      </div>
      <p><strong>Par virement</strong> ({amount} €, sans frais) : utilisez les coordonnées bancaires indiquées sur la facture, avec la référence <strong>{invoice_number} — {adh.nom}</strong>.
        Un virement peut prendre <strong>jusqu'à 48 h</strong> avant d'apparaître sur notre compte.</p>
      <p>Dès que votre virement est effectué, merci de nous prévenir par e-mail à <a href="mailto:{EMAIL_CONTACT}">{EMAIL_CONTACT}</a> en indiquant la référence.</p>
      <p style="margin-top:20px;color:#555;">Cordialement,<br>L'équipe <strong>Spectacle'ment Vôtre</strong></p>
    </div>
  </div>
</body></html>"""


def _html_alerte_admin(adh, amount, invoice_number, date_envoi, jours):
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;color:#333;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:#c62828;color:#fff;padding:18px;text-align:center;">
      <h2 style="margin:0;">🚨 Facture impayée à J+{jours}</h2>
    </div>
    <div style="padding:20px;line-height:1.55;">
      <p><strong>{adh.nom}</strong> · {adh.email} · {adh.telephone}</p>
      <p>Facture n° <strong>{invoice_number}</strong> de {amount} € envoyée le {date_envoi.strftime('%d/%m/%Y')}, toujours sans règlement ni activation.</p>
      <p>Relances client : J+3 {'envoyée' if adh.relance_j3_sent_for == date_envoi else 'non envoyée'}, J+7 {'envoyée' if adh.relance_j7_sent_for == date_envoi else 'non envoyée'}.</p>
      <p style="text-align:center;margin-top:24px;">
        <a href="{WEBSITE_URL}/admin/adhesions" style="color:#1976d2;">Voir les demandes d'adhésion</a>
      </p>
    </div>
  </div>
</body></html>"""


def traiter(now, apply, envoyer=_send_mail, admin_addr=None):
    """Applique les relances dues. Retourne les compteurs {'j3', 'j7', 'alerte'}.

    En dry-run, les compteurs indiquent ce qui serait envoyé. Rien n'est enregistré.
    """
    stats = {"j3": 0, "j7": 0, "alerte": 0}

    adhesions = (
        Adhesion.query
        .filter(Adhesion.statut == "contacted", Adhesion.invoice_sent_at.isnot(None))
        .order_by(Adhesion.invoice_sent_at)
        .all()
    )

    for adh in adhesions:
        relance, alerte = actions_dues(adh, now)
        if not relance and not alerte:
            continue

        envoi = adh.invoice_sent_at
        jours = int((now - envoi).total_seconds() // 86400)
        amount = adh.invoice_amount or 0
        numero = adh.invoice_number or "(sans numéro)"

        if relance:
            label = "J+7" if relance == "j7" else "J+3"
            print(f"  📨 Relance {label} : {adh.nom} · {adh.email} · facture {numero} · envoyée il y a {jours} j")
            stats["j7" if relance == "j7" else "j3"] += 1
            if apply:
                html = _html_relance(adh, amount, numero, envoi, dernier=(relance == "j7"))
                sujet = f"{'Dernier rappel' if relance == 'j7' else 'Rappel'} : facture {numero} en attente de règlement"
                if envoyer(adh.email, sujet, html):
                    if relance == "j7":
                        adh.relance_j7_sent_for = envoi
                        # Le J+3 n'a plus lieu d'être une fois le J+7 envoyé (cas où le cron a manqué le J+3).
                        adh.relance_j3_sent_for = envoi
                    else:
                        adh.relance_j3_sent_for = envoi
                    print("        [OK] relance envoyée")
                else:
                    print("        [ECHEC] relance non envoyée, nouvelle tentative au prochain passage")

        if alerte:
            print(f"  🚨 Alerte admin J+10 : {adh.nom} · facture {numero} · {amount} €")
            stats["alerte"] += 1
            if apply:
                if not admin_addr:
                    print("        [ECHEC] aucune adresse admin configurée (MAIL_DEFAULT_SENDER / MAIL_USERNAME)")
                else:
                    html = _html_alerte_admin(adh, amount, numero, envoi, jours)
                    sujet = f"[Alerte] Facture {numero} impayée à J+{jours} — {adh.nom}"
                    if envoyer(admin_addr, sujet, html):
                        adh.alerte_admin_j10_sent_for = envoi
                        print("        [OK] alerte envoyée à l'admin")
                    else:
                        print("        [ECHEC] alerte non envoyée, nouvelle tentative au prochain passage")

    if apply:
        db.session.commit()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Relances automatiques des factures d'adhésion AO impayées.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--apply", action="store_true",
                        help="Envoie réellement les relances et l'alerte (sinon dry-run par défaut).")
    args = parser.parse_args()

    with app.app_context():
        now = datetime.utcnow()
        admin_addr = app.config.get("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_USERNAME")

        print()
        print("=" * 90)
        print(f"RELANCES FACTURES ADHESION AO — {now.strftime('%d/%m/%Y %H:%M UTC')}")
        if not args.apply:
            print("MODE DRY-RUN (aucune modification, aucun email)")
        print("=" * 90)

        stats = traiter(now, args.apply, admin_addr=admin_addr)

        print()
        print(f"Relances J+3 dues : {stats['j3']} · Relances J+7 dues : {stats['j7']} · Alertes admin J+10 dues : {stats['alerte']}")


if __name__ == "__main__":
    main()
