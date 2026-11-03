"""Send a 48-hour warning and safely purge the explicitly reviewed account batch.

The notification and deletion modes are dry-runs by default. The delete mode is
limited to the fixed, reviewed account IDs and rechecks every exclusion at run time.
"""
import argparse
from datetime import datetime, timedelta
from html import escape

from sqlalchemy import func, or_

from app import app, db, notify_admin_show_deletion
from models.models import (
    Adhesion,
    DemandeAnimation,
    InactiveAccountPurgeNotice,
    User,
    VisitorLog,
)
from purge_inactive_accounts import _delete_user_cascade

try:
    from flask_mail import Message as MailMessage
except ImportError:
    MailMessage = None


TARGET_USER_IDS = (
    478, 476, 475, 473, 472, 468, 465, 464, 462, 457, 455, 448,
    445, 444, 443, 441, 438, 436, 434, 426, 421, 414, 413, 411,
)
PROTECTED_USER_IDS = frozenset({1, 489, 488, 487, 486, 483, 482, 481})
NOTICE_DURATION = timedelta(hours=48)


def _normalized_email(email):
    return (email or "").strip().casefold()


def _requester_ids(users):
    """Return target IDs linked to an animation request by user ID or email."""
    users_by_email = {}
    user_ids = {user.id for user in users}
    for user in users:
        normalized_email = _normalized_email(user.email)
        if normalized_email:
            users_by_email.setdefault(normalized_email, set()).add(user.id)

    conditions = [DemandeAnimation.user_id.in_(user_ids)]
    if users_by_email:
        conditions.append(
            func.lower(func.trim(DemandeAnimation.contact_email)).in_(
                list(users_by_email)
            )
        )

    requester_ids = set()
    for demande in DemandeAnimation.query.filter(or_(*conditions)).all():
        if demande.user_id in user_ids:
            requester_ids.add(demande.user_id)
        requester_ids.update(
            users_by_email.get(_normalized_email(demande.contact_email), set())
        )
    return requester_ids


def _validate_targets():
    users = User.query.filter(User.id.in_(TARGET_USER_IDS)).all()
    users_by_id = {user.id: user for user in users}
    errors = []

    missing_ids = set(TARGET_USER_IDS) - set(users_by_id)
    if missing_ids:
        errors.append(f"Comptes absents depuis le dry-run : {sorted(missing_ids)}")
    if len(users) != len(TARGET_USER_IDS):
        errors.append("Le nombre de comptes candidats ne correspond plus au dry-run.")

    requester_ids = _requester_ids(users) if users else set()
    for user in users:
        if user.id in PROTECTED_USER_IDS:
            errors.append(f"ID {user.id} fait partie des comptes à préserver.")
        if user.is_admin:
            errors.append(f"ID {user.id} est administrateur.")
        if user.shows:
            errors.append(f"ID {user.id} possède maintenant au moins un spectacle.")
        if user.id in requester_ids:
            errors.append(f"ID {user.id} est lié à une demande d'animation.")
        if not user.email or "@" not in user.email or any(c.isspace() for c in user.email):
            errors.append(f"ID {user.id} n'a pas d'adresse email exploitable.")
        if InactiveAccountPurgeNotice.query.filter_by(user_id=user.id).first():
            errors.append(f"ID {user.id} a déjà un enregistrement de préavis.")
        if user.pending_deletion_at is not None:
            errors.append(f"ID {user.id} a déjà un préavis standard en cours.")

    return users, errors


def _notice_message(username, deadline):
    safe_username = escape(username or "")
    deadline_text = deadline.strftime("%d/%m/%Y à %H:%M UTC")
    body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f6fa;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;padding:28px;color:#333;line-height:1.6;">
    <h2>Préavis concernant votre compte Spectacle'ment VØtre</h2>
    <p>Bonjour <strong>{safe_username}</strong>,</p>
    <p>Votre compte ne comporte actuellement aucun spectacle. Nous prévoyons sa suppression le
       <strong>{deadline_text}</strong>, soit dans 48 heures.</p>
    <p>Pour conserver votre compte, publiez un spectacle ou contactez-nous avant cette échéance
       si ce compte est utilisé comme organisateur ou si vous avez besoin d'aide.</p>
    <p>Vous pouvez répondre à ce message ou écrire à contact@spectacleanimation.fr.</p>
    <p><a href="https://www.spectacleanimation.fr/login">Me connecter</a></p>
    <p>Cordialement,<br>L'équipe Spectacle'ment VØtre</p>
  </div>
</body></html>"""
    return MailMessage(
        subject="Préavis : votre compte sera supprimé dans 48 heures",
        recipients=[],
        html=body,
    )


def send_notices(confirm):
    with app.app_context():
        users, errors = _validate_targets()
        if errors:
            print("ARRÊT : vérification des candidats échouée.")
            for error in errors:
                print(f" - {error}")
            return 1

        print(f"Candidats vérifiés : {len(users)}")
        for user in users:
            deadline = datetime.utcnow() + NOTICE_DURATION
            print(
                f"{user.id} | {user.username} | {user.email} | "
                f"échéance {deadline.strftime('%d/%m/%Y %H:%M UTC')}"
            )

        if not confirm:
            print("DRY-RUN : aucun email envoyé, aucun préavis enregistré.")
            return 0

        if (
            MailMessage is None
            or not getattr(app, "mail", None)
            or not app.config.get("MAIL_USERNAME")
            or not app.config.get("MAIL_PASSWORD")
        ):
            print("ERREUR : configuration email absente; aucun avis envoyé.")
            return 1

        sent = 0
        errors = 0
        for user in users:
            try:
                message = _notice_message(user.username, deadline)
                message.recipients = [user.email]
                app.mail.send(message)
                notice = InactiveAccountPurgeNotice(
                    user_id=user.id,
                    email=user.email,
                    notified_at=datetime.utcnow(),
                    delete_after=deadline,
                    status="pending",
                )
                db.session.add(notice)
                db.session.commit()
                sent += 1
                print(f"[OK] Préavis envoyé à l'ID {user.id} ({user.email}).")
            except Exception as exc:
                db.session.rollback()
                errors += 1
                print(f"[ERREUR] ID {user.id}, email/préavis non confirmé : {exc}")

        print(f"Préavis enregistrés : {sent}/{len(users)}; erreurs : {errors}.")
        return 1 if errors else 0


def _linked_demand_exists(user, notice):
    emails = {
        email for email in (
            _normalized_email(user.email),
            _normalized_email(notice.email),
        ) if email
    }
    conditions = [DemandeAnimation.user_id == user.id]
    if emails:
        conditions.append(
            func.lower(func.trim(DemandeAnimation.contact_email)).in_(list(emails))
        )
    return DemandeAnimation.query.filter(or_(*conditions)).first() is not None


def process_due(confirm):
    with app.app_context():
        now = datetime.utcnow()
        notices = InactiveAccountPurgeNotice.query.filter(
            InactiveAccountPurgeNotice.status == "pending",
            InactiveAccountPurgeNotice.delete_after <= now,
        ).order_by(InactiveAccountPurgeNotice.delete_after.asc()).all()

        print(f"Préavis arrivés à échéance : {len(notices)}")
        if not confirm:
            for notice in notices:
                user = db.session.get(User, notice.user_id)
                username = user.username if user else "(compte absent)"
                print(f"{notice.user_id} | {username} | {notice.email or ''}")
            print("DRY-RUN : aucune suppression.")
            return 0

        errors = 0
        deleted = 0
        for notice in notices:
            user = User.query.filter_by(id=notice.user_id).with_for_update().first()
            reason = None
            if notice.user_id not in TARGET_USER_IDS:
                reason = "ID hors du lot explicitement autorisé"
            elif user is None:
                reason = "compte déjà absent"
            elif user.id in PROTECTED_USER_IDS or user.is_admin:
                reason = "compte protégé ou administrateur"
            elif user.shows:
                reason = "un spectacle est désormais associé au compte"
            elif _linked_demand_exists(user, notice):
                reason = "une demande d'animation est désormais associée au compte"

            if reason:
                notice.status = "cancelled"
                notice.completed_at = now
                notice.last_error = reason
                notice.email = None
                db.session.commit()
                print(f"[CONSERVÉ] ID {notice.user_id} : {reason}.")
                continue

            try:
                username = user.username
                email = user.email
                VisitorLog.query.filter_by(user_id=user.id).update({"user_id": None})
                Adhesion.query.filter_by(user_id=user.id).update({"user_id": None})
                _delete_user_cascade(user)
                notice.status = "deleted"
                notice.completed_at = now
                notice.email = None
                db.session.commit()
                deleted += 1
                print(f"[SUPPRIMÉ] ID {notice.user_id}.")
                try:
                    notify_admin_show_deletion(
                        "Compte supprimé après préavis de 48 heures",
                        [],
                        {"username": username, "email": email},
                    )
                except Exception as exc:
                    print(f"[ERREUR] Récapitulatif admin pour ID {notice.user_id} : {exc}")
            except Exception as exc:
                notice_id = notice.id
                user_id = notice.user_id
                db.session.rollback()
                errors += 1
                retry_notice = db.session.get(
                    InactiveAccountPurgeNotice, notice_id
                )
                if retry_notice is not None:
                    retry_notice.attempts += 1
                    retry_notice.last_error = str(exc)
                    if retry_notice.attempts >= 3:
                        retry_notice.status = "failed"
                        retry_notice.email = None
                    db.session.commit()
                print(f"[ERREUR] Suppression de l'ID {user_id} : {exc}")

        print(f"Suppressions : {deleted}; erreurs : {errors}.")
        return 1 if errors else 0


def cancel_notice(user_id, confirm):
    with app.app_context():
        notice = InactiveAccountPurgeNotice.query.filter_by(
            user_id=user_id,
            status="pending",
        ).first()
        if notice is None:
            print(f"Aucun préavis en attente pour l'ID {user_id}.")
            return 1

        print(f"Préavis en attente pour l'ID {user_id}, échéance "
              f"{notice.delete_after.strftime('%d/%m/%Y %H:%M UTC')}.")
        if not confirm:
            print("DRY-RUN : préavis non annulé.")
            return 0

        notice.status = "cancelled"
        notice.completed_at = datetime.utcnow()
        notice.last_error = "Préavis annulé manuellement."
        notice.email = None
        db.session.commit()
        print(f"Préavis annulé pour l'ID {user_id}.")
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--send-notices",
        action="store_true",
        help="Vérifier et (avec --confirm-notices) envoyer les préavis de 48 h.",
    )
    parser.add_argument(
        "--confirm-notices",
        action="store_true",
        help="Autoriser l'envoi des emails et l'enregistrement des échéances.",
    )
    parser.add_argument(
        "--process-due",
        action="store_true",
        help="Traiter les préavis arrivés à échéance (dry-run par défaut).",
    )
    parser.add_argument(
        "--confirm-delete",
        action="store_true",
        help="Autoriser les suppressions après revalidation complète.",
    )
    parser.add_argument(
        "--cancel-notice",
        type=int,
        metavar="USER_ID",
        help="Vérifier ou annuler un préavis en attente pour cet ID.",
    )
    parser.add_argument(
        "--confirm-cancel",
        action="store_true",
        help="Confirmer l'annulation du préavis sélectionné.",
    )
    args = parser.parse_args()

    selected_modes = sum((
        args.send_notices,
        args.process_due,
        args.cancel_notice is not None,
    ))
    if selected_modes != 1:
        parser.error(
            "Choisissez une seule action : --send-notices, --process-due ou --cancel-notice."
        )
    if args.confirm_notices and not args.send_notices:
        parser.error("--confirm-notices nécessite --send-notices.")
    if args.confirm_delete and not args.process_due:
        parser.error("--confirm-delete nécessite --process-due.")
    if args.confirm_cancel and args.cancel_notice is None:
        parser.error("--confirm-cancel nécessite --cancel-notice.")

    if args.send_notices:
        return send_notices(args.confirm_notices)
    if args.process_due:
        return process_due(args.confirm_delete)
    return cancel_notice(args.cancel_notice, args.confirm_cancel)


if __name__ == "__main__":
    raise SystemExit(main())
