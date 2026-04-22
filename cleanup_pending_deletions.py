"""
Script à exécuter périodiquement (cron / Render Cron Job, ex. quotidien)
pour supprimer définitivement les comptes en préavis dont la date est dépassée
ET qui n'ont toujours aucun spectacle approuvé.

Usage :
    python cleanup_pending_deletions.py
"""
from datetime import datetime
from app import app, db
from models.models import User, Show, ShowView, Review, Conversation, Message, Notification

try:
    from flask_mail import Message as MailMessage  # type: ignore
except Exception:
    MailMessage = None  # type: ignore


def _send_final_email(username, email):
    if not email or MailMessage is None:
        return
    if not getattr(app, "mail", None):
        return
    if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
        return
    body_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#7c4dff,#536dfe);color:#fff;padding:24px;text-align:center;">
      <h2 style="margin:0;">Spectacle'ment V&Oslash;tre</h2>
    </div>
    <div style="padding:28px;color:#333;line-height:1.6;">
      <p>Bonjour <strong>{username}</strong>,</p>
      <p>Conform&eacute;ment au pr&eacute;avis envoy&eacute; il y a 7 jours, votre compte sur <strong>Spectacle'ment V&Oslash;tre</strong> vient d'&ecirc;tre <strong>supprim&eacute; pour inactivit&eacute;</strong> (aucun spectacle publi&eacute;).</p>
      <div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="margin:0;"><strong>Vous changez d'avis ?</strong></p>
        <p style="margin:8px 0 0 0;">L'inscription est toujours <strong>100 % gratuite</strong>.</p>
        <p style="text-align:center;margin:16px 0 0 0;">
          <a href="https://www.spectacleanimation.fr/register" style="display:inline-block;padding:12px 26px;background:#1b5e20;color:#fff;text-decoration:none;border-radius:6px;font-weight:700;">Cr&eacute;er un nouveau compte</a>
        </p>
      </div>
      <p style="margin-top:24px;">L'&eacute;quipe Spectacle'ment V&Oslash;tre<br>contact@spectacleanimation.fr</p>
    </div>
  </div>
</body></html>"""
    try:
        msg = MailMessage(subject="Suppression de votre compte Spectacle'ment VØtre", recipients=[email])
        msg.html = body_html
        app.mail.send(msg)  # type: ignore[attr-defined]
        print(f"  ✓ Email final envoyé à {email}")
    except Exception as e:
        print(f"  ✗ Email final non envoyé à {email}: {e}")


def _delete_user_cascade(user):
    """Supprime un User et ses dépendances (mêmes opérations que admin_delete_user)."""
    if hasattr(user, 'shows'):
        for show in list(user.shows):
            ShowView.query.filter_by(show_id=show.id).delete()
            Review.query.filter_by(show_id=show.id).delete()
            for conv in Conversation.query.filter_by(show_id=show.id).all():
                Message.query.filter_by(conversation_id=conv.id).delete()
                db.session.delete(conv)
            db.session.delete(show)
    for conv in Conversation.query.filter(
        (Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)
    ).all():
        Message.query.filter_by(conversation_id=conv.id).delete()
        db.session.delete(conv)
    Notification.query.filter_by(user_id=user.id).delete()
    Review.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)


def main():
    now = datetime.utcnow()
    with app.app_context():
        candidats = User.query.filter(
            User.pending_deletion_at.isnot(None),
            User.pending_deletion_at <= now,
            User.is_admin.is_(False),
        ).all()
        if not candidats:
            print("Aucun compte à supprimer.")
            return
        print(f"{len(candidats)} compte(s) en préavis dépassé.")
        nb_deleted = 0
        for u in candidats:
            nb_approved = sum(1 for s in u.shows if getattr(s, 'approved', False)) if hasattr(u, 'shows') else 0
            if nb_approved > 0:
                # L'utilisateur a finalement publié → annule le préavis
                print(f"  ↩️  {u.username}: {nb_approved} spectacle(s) publié(s) → préavis annulé")
                u.pending_deletion_at = None
                continue
            print(f"  🗑️  Suppression {u.username} (id={u.id}, email={u.email})")
            email = u.email
            username = u.username
            try:
                _delete_user_cascade(u)
                db.session.commit()
                _send_final_email(username, email)
                nb_deleted += 1
            except Exception as e:
                db.session.rollback()
                print(f"     ✗ Erreur: {e}")
        db.session.commit()
        print(f"\n✅ Terminé : {nb_deleted} compte(s) supprimé(s).")


if __name__ == "__main__":
    main()
