"""
Script ONE-SHOT de rattrapage : supprime immediatement les comptes non-admin,
sans spectacle approuve, inscrits depuis plus de --days jours (defaut : 30),
SANS preavis. A utiliser quand le cron auto_flag_inactive_users n'a pas
tourne pendant longtemps et qu'un retard s'est accumule.

Reutilise la meme cascade de suppression que cleanup_pending_deletions.py.

Usage :
    # 1) Lister d'abord (dry-run, aucune modification)
    python purge_inactive_accounts.py

    # 2) Supprimer pour de vrai
    python purge_inactive_accounts.py --confirm

    # Optionnel : changer le seuil
    python purge_inactive_accounts.py --confirm --days 60

    # Optionnel : ne pas envoyer d'email de notification aux comptes supprimes
    python purge_inactive_accounts.py --confirm --no-email

    # Optionnel : exclure les comptes organisateurs
    python purge_inactive_accounts.py --confirm --exclude-organisateurs

IMPORTANT : pour cibler la base de PRODUCTION, positionnez la variable
d'environnement DATABASE_URL AVANT le lancement (recuperable dans le
dashboard Render, base flask-spectacles-db).
"""
import argparse
import time
from datetime import datetime, timedelta

from app import app, db, notify_admin_show_deletion
from models.models import (
    User, DemandeAnimation, PageVisit, VisitorLog,
    ShowView, Review, Conversation, Message, Notification,
)

try:
    from flask_mail import Message as MailMessage  # type: ignore
except Exception:
    MailMessage = None  # type: ignore


def _send_final_email(username, email):
    """Email de notification envoye au compte apres suppression."""
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
      <p>Votre compte sur <strong>Spectacle'ment V&Oslash;tre</strong> vient d'&ecirc;tre <strong>supprim&eacute; pour inactivit&eacute;</strong> (aucun spectacle publi&eacute;).</p>
      <p>Nous serons <strong>toujours heureux de vous revoir un jour</strong> afin de vous aider &agrave; <strong>gagner en visibilit&eacute;</strong>. L'inscription est <strong>100 % gratuite</strong> et publier votre premier spectacle prend quelques minutes.</p>
      <div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="text-align:center;margin:0;">
          <a href="https://www.spectacleanimation.fr/register" style="display:inline-block;padding:12px 26px;background:#1b5e20;color:#fff;text-decoration:none;border-radius:6px;font-weight:700;">Cr&eacute;er un nouveau compte</a>
        </p>
      </div>
      <p style="margin-top:24px;">Cordialement,<br>L'&eacute;quipe Spectacle'ment V&Oslash;tre<br>contact@spectacleanimation.fr</p>
    </div>
  </div>
</body></html>"""
    try:
        msg = MailMessage(subject="Suppression de votre compte Spectacle'ment VOtre", recipients=[email])
        msg.html = body_html
        app.mail.send(msg)  # type: ignore[attr-defined]
        print(f"        Email final envoye a {email}")
    except Exception as e:
        print(f"        Email final NON envoye a {email} : {e}")


def _delete_user_cascade(user):
    """Supprime User + dependances (Show, ShowView, Review, Conversation, Message, Notification)."""
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
    parser = argparse.ArgumentParser(
        description="Purge one-shot des comptes inactifs (rattrapage cron).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--confirm", action="store_true",
                        help="Sans ce flag = dry-run (liste seulement, AUCUNE suppression).")
    parser.add_argument("--days", type=int, default=30,
                        help="Nombre minimal de jours depuis l'inscription (defaut : 30).")
    parser.add_argument("--no-email", action="store_true",
                        help="Ne pas envoyer d'email aux utilisateurs supprimes.")
    parser.add_argument("--exclude-organisateurs", action="store_true",
                        help="Exclure les comptes is_organisateur=True (mairies, ecoles, CSE...).")
    parser.add_argument("--batch", type=int, default=None,
                        help="Nombre max de comptes a traiter par execution. Relancez la commande pour traiter le lot suivant.")
    parser.add_argument("--sleep", type=float, default=0.0,
                        help="Delai en secondes entre chaque suppression (defaut : 0). Utile pour espacer les envois SMTP.")
    args = parser.parse_args()

    seuil = datetime.utcnow() - timedelta(days=args.days)
    with app.app_context():
        q = User.query.filter(
            User.is_admin.is_(False),
            User.created_at <= seuil,
        )
        if args.exclude_organisateurs:
            q = q.filter(User.is_organisateur.is_(False))
        candidats = q.order_by(User.created_at.asc()).all()

        a_supprimer = []
        for u in candidats:
            nb_approved = sum(1 for s in u.shows if getattr(s, 'approved', False)) if hasattr(u, 'shows') else 0
            if nb_approved == 0:
                a_supprimer.append(u)

        print()
        print("=" * 100)
        print(f"Comptes non-admin, 0 spectacle approuve, inscrits depuis > {args.days} jour(s)"
              + ("  [organisateurs EXCLUS]" if args.exclude_organisateurs else ""))
        print("=" * 100)
        print(f"{'ID':<6} {'Type':<6} {'Username':<28} {'Email':<38} {'Inscrit':<12} {'Shows'}")
        print("-" * 100)
        for u in a_supprimer:
            nb_shows = len(u.shows) if getattr(u, 'shows', None) else 0
            date_ins = u.created_at.strftime('%d/%m/%Y') if u.created_at else '?'
            typ = "ORGA" if getattr(u, 'is_organisateur', False) else "CIE"
            print(f"{u.id:<6} {typ:<6} {(u.username or '')[:28]:<28} "
                  f"{(u.email or '')[:38]:<38} {date_ins:<12} {nb_shows}")
        print("-" * 100)
        print(f"Total candidats : {len(a_supprimer)}")

        if not args.confirm:
            print()
            print("MODE DRY-RUN : aucune modification. Pour supprimer, relancez avec --confirm.")
            return

        if not a_supprimer:
            print("Rien a supprimer.")
            return

        # Applique le batch : ne traite que les N premiers, les autres attendront le prochain run
        total_candidats = len(a_supprimer)
        if args.batch and args.batch > 0:
            a_traiter = a_supprimer[:args.batch]
            restants = total_candidats - len(a_traiter)
        else:
            a_traiter = a_supprimer
            restants = 0

        print()
        print("=" * 100)
        print(f"SUPPRESSION EN COURS ({len(a_traiter)} compte(s) ce run"
              + (f", {restants} restant(s) apres)" if restants > 0 else ")"))
        print("=" * 100)
        nb_deleted = 0
        recap = []
        for u in a_traiter:
            username = u.username
            email = u.email
            uid = u.id
            shows_info = []
            if hasattr(u, 'shows'):
                for s in u.shows:
                    shows_info.append({
                        "id": s.id,
                        "title": s.title,
                        "raison_sociale": getattr(s, "raison_sociale", None),
                        "category": getattr(s, "category", None),
                        "region": getattr(s, "region", None),
                    })
            try:
                # Detache les FK nullables non gerees par la cascade principale
                DemandeAnimation.query.filter_by(user_id=uid).update({"user_id": None})
                PageVisit.query.filter_by(user_id=uid).update({"user_id": None})
                VisitorLog.query.filter_by(user_id=uid).update({"user_id": None})

                _delete_user_cascade(u)
                db.session.commit()
                print(f"  [OK]  {username} (id={uid}) supprime")

                if not args.no_email:
                    _send_final_email(username, email)

                try:
                    notify_admin_show_deletion(
                        "Compte supprime (rattrapage cron auto-inactivite)",
                        shows_info,
                        {"username": username, "email": email},
                    )
                except Exception as e:
                    print(f"        (recap admin non envoye : {e})")

                recap.append(f"{username} ({email}) - {len(shows_info)} fiche(s)")
                nb_deleted += 1

                if args.sleep > 0:
                    time.sleep(args.sleep)
            except Exception as e:
                db.session.rollback()
                print(f"  [ERR] {username} (id={uid}) : {e}")

        print()
        print("=" * 100)
        print(f"TERMINE : {nb_deleted}/{len(a_traiter)} compte(s) supprime(s) sur ce run.")
        if restants > 0:
            print(f"          {restants} compte(s) restant(s) : relancez la meme commande pour traiter le lot suivant.")
        print("=" * 100)


if __name__ == "__main__":
    main()
