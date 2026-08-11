"""
Script à exécuter périodiquement (cron / Render Cron Job, ex. quotidien) pour
détecter les comptes utilisateurs inscrits depuis plus de N_INACTIVITY_DAYS
qui n'ont **aucun spectacle approuvé** et leur poser un préavis de suppression
de 7 jours + envoyer un email d'avertissement.

Le script `cleanup_pending_deletions.py` se charge ensuite de la suppression
définitive une fois le préavis dépassé.

Usage :
    python auto_flag_inactive_users.py
"""
from datetime import datetime, timedelta
from app import app, db
from models.models import User

try:
    from flask_mail import Message as MailMessage  # type: ignore
except Exception:
    MailMessage = None  # type: ignore


# Nombre de jours d'inactivité (depuis inscription) avant de poser le préavis
N_INACTIVITY_DAYS = 7
# Durée du préavis (avant suppression définitive)
N_NOTICE_DAYS = 7


def _send_notice_email(username, email, deadline_str):
    if not email or MailMessage is None:
        return False
    if not getattr(app, "mail", None):
        return False
    if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
        return False
    body_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#ff9800,#f57c00);color:#fff;padding:24px;text-align:center;">
      <h2 style="margin:0;">&#9203; Pr&eacute;avis de suppression</h2>
    </div>
    <div style="padding:28px;color:#333;line-height:1.6;">
      <p>Bonjour <strong>{username}</strong>,</p>
      <p>Nous avons remarqu&eacute; qu'<strong>aucun spectacle n'a encore &eacute;t&eacute; publi&eacute;</strong> sur votre compte Spectacle'ment V&Oslash;tre depuis votre inscription.</p>
      <p>Sans publication de votre part, votre compte sera <strong>automatiquement supprim&eacute; le {deadline_str}</strong> (dans {N_NOTICE_DAYS} jours).</p>
      <div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="margin:0;"><strong>&#9989; Comment conserver votre compte ?</strong></p>
        <p style="margin:8px 0 0 0;">Connectez-vous et publiez votre premier spectacle. C'est <strong>gratuit</strong> et cela prend quelques minutes.</p>
        <p style="text-align:center;margin:16px 0 0 0;">
          <a href="https://www.spectacleanimation.fr/login" style="display:inline-block;padding:12px 26px;background:#1b5e20;color:#fff;text-decoration:none;border-radius:6px;font-weight:700;">&#128073; Me connecter et publier</a>
        </p>
      </div>
      <p style="font-size:0.9em;color:#666;">Si vous publiez un spectacle avant cette date, votre compte sera conserv&eacute; automatiquement.</p>
      <p style="margin-top:24px;">Cordialement,<br><strong>L'&eacute;quipe Spectacle'ment V&Oslash;tre</strong><br>contact@spectacleanimation.fr</p>
    </div>
  </div>
</body></html>"""
    try:
        msg = MailMessage(
            subject="\u23F3 Votre compte Spectacle'ment V\u00D8tre sera supprim\u00E9 dans 7 jours",
            recipients=[email],
        )
        msg.html = body_html
        app.mail.send(msg)  # type: ignore[attr-defined]
        return True
    except Exception as e:
        print(f"     \u2717 Email pr\u00e9avis non envoy\u00e9 \u00e0 {email}: {e}")
        return False


def _send_admin_recap(nb_marques, lignes):
    """Recap quotidien a l'admin (envoye meme si 0) pour confirmer que le cron a tourne."""
    if MailMessage is None or not getattr(app, "mail", None):
        return
    if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
        return
    admin_email = app.config.get("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_USERNAME")
    if not admin_email:
        return
    now_str = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    items = "".join(f"<li>{l}</li>" for l in lignes) or "<li>Aucun compte mis en preavis aujourd'hui.</li>"
    body_html = (
        "<div style='font-family:Arial,sans-serif;color:#333;max-width:640px;margin:0 auto;'>"
        "<h2 style='color:#e65100;'>Cron marquage inactifs</h2>"
        f"<p><strong>{nb_marques}</strong> compte(s) mis en preavis (suppression dans {N_NOTICE_DAYS} jours).</p>"
        f"<ul>{items}</ul>"
        f"<p style='color:#999;font-size:12px;'>Execution automatique - {now_str}</p>"
        "</div>"
    )
    try:
        msg = MailMessage(
            subject=f"[CRON] Marquage inactifs : {nb_marques} compte(s) mis en preavis",
            recipients=[admin_email],
        )
        msg.html = body_html
        app.mail.send(msg)
        print(f"  Recap admin envoye a {admin_email}")
    except Exception as e:
        print(f"  Recap admin non envoye: {e}")


def main():
    now = datetime.utcnow()
    seuil_inscription = now - timedelta(days=N_INACTIVITY_DAYS)
    with app.app_context():
        # Candidats : non-admin, inscrits depuis > N_INACTIVITY_DAYS, pas déjà en préavis
        candidats = User.query.filter(
            User.is_admin.is_(False),
            User.pending_deletion_at.is_(None),
            User.created_at <= seuil_inscription,
        ).all()

        if not candidats:
            print("Aucun candidat \u00e0 marquer.")
            _send_admin_recap(0, [])
            return

        nb_marques = 0
        lignes = []
        for u in candidats:
            nb_approved = sum(1 for s in u.shows if getattr(s, 'approved', False)) if hasattr(u, 'shows') else 0
            if nb_approved > 0:
                continue  # a déjà publié → on ne touche pas

            deadline = now + timedelta(days=N_NOTICE_DAYS)
            deadline_str = deadline.strftime('%d/%m/%Y')
            try:
                u.pending_deletion_at = deadline
                db.session.commit()
                print(f"  \u23F3 Pr\u00e9avis pos\u00e9 sur {u.username} (id={u.id}, email={u.email}) \u2192 suppression le {deadline_str}")
                if _send_notice_email(u.username, u.email, deadline_str):
                    print(f"     \u2713 Email pr\u00e9avis envoy\u00e9 \u00e0 {u.email}")
                lignes.append(f"{u.username} (id={u.id}, {u.email}) - suppression le {deadline_str}")
                nb_marques += 1
            except Exception as e:
                db.session.rollback()
                print(f"     \u2717 Erreur sur {u.username}: {e}")

        print(f"\n\u2705 Termin\u00e9 : {nb_marques} compte(s) mis en pr\u00e9avis.")
        _send_admin_recap(nb_marques, lignes)


if __name__ == "__main__":
    main()
