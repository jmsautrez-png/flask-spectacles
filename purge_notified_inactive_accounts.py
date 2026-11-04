"""Monthly 48-hour notices and deletion after rechecking account eligibility."""
import argparse
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from html import escape
from uuid import uuid4

from sqlalchemy import func, or_

from app import app, db, notify_admin_show_deletion
from models.models import (
    Adhesion,
    DemandeAnimation,
    InactiveAccountPurgeDatabase,
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


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _latest_ids():
    return {
        user.id for user in User.query.filter(~User.shows.any()).order_by(
            User.created_at.desc(), User.id.desc()
        ).limit(7).all()
    }


def database_status(register=False):
    with app.app_context():
        marker = db.session.get(InactiveAccountPurgeDatabase, 1)
        if marker is None and register:
            marker = InactiveAccountPurgeDatabase(id=1, identity=str(uuid4()))
            db.session.add(marker)
            db.session.commit()
        print(f"Utilisateurs : {User.query.count()}")
        print(f"Préavis en attente : {InactiveAccountPurgeNotice.query.filter_by(status='pending').count()}")
        print(f"Identité de base : {marker.identity if marker else '(non enregistrée)'}")
        if register:
            print("Aucun email envoyé, aucun compte supprimé.")
        return 0


@contextmanager
def _automatic_lock():
    """Keep a dedicated PostgreSQL session lock across per-account commits."""
    with db.engine.connect() as connection:
        acquired = connection.execute(
            db.text("SELECT pg_try_advisory_lock(785041925)")
        ).scalar_one()
        try:
            yield acquired
        finally:
            if acquired:
                connection.execute(db.text("SELECT pg_advisory_unlock(785041925)"))


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
        if user.is_organisateur:
            errors.append(f"ID {user.id} est organisateur.")
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
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#ff9800,#f57c00);color:#fff;padding:24px;text-align:center;">
      <h2 style="margin:0;">Préavis de suppression</h2>
    </div>
    <div style="padding:28px;color:#333;line-height:1.6;">
      <p>Bonjour <strong>{safe_username}</strong>,</p>
      <p>Nous avons remarqué qu'<strong>aucun spectacle n'a encore été publié</strong> sur votre compte Spectacle'ment VØtre.</p>
      <p>Sans publication de votre part, votre compte sera <strong>automatiquement supprimé à partir du {deadline_text}</strong>, jamais avant <strong>48 heures après cet envoi</strong>.</p>
      <div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="margin:0;"><strong>Comment conserver votre compte ?</strong></p>
        <p style="margin:8px 0 0 0;">Connectez-vous et publiez votre premier spectacle. C'est <strong>gratuit</strong> et cela prend quelques minutes.</p>
        <p style="text-align:center;margin:16px 0 0 0;">
          <a href="https://www.spectacleanimation.fr/login" style="display:inline-block;padding:12px 26px;background:#1b5e20;color:#fff;text-decoration:none;border-radius:6px;font-weight:700;">Me connecter et publier</a>
        </p>
      </div>
      <div style="background:#f3e5f5;border-left:4px solid #6a1b9a;padding:16px 18px;border-radius:6px;margin:20px 0;">
        <p style="margin:0 0 8px 0;"><strong>Pourquoi c'est efficace ?</strong></p>
        <p style="margin:0 0 8px 0;font-size:14px;line-height:1.6;">Spectacle'ment VØtre fonctionne comme un <strong>annuaire national de référence</strong> : plus il y a de spectacles publiés, plus les <strong>mairies, écoles, CSE, agences et organisateurs</strong> prennent l'habitude d'y chercher leurs animations &mdash; et d'y déposer leurs <strong>appels d'offres</strong>.</p>
        <p style="margin:0 0 8px 0;font-size:14px;line-height:1.6;"><strong>Au niveau local</strong>, votre département gagne en visibilité à mesure que des compagnies de la région s'y inscrivent : les acteurs culturels de chez vous tombent alors sur <strong>votre profil en priorité</strong>.</p>
        <p style="margin:0 0 8px 0;font-size:14px;line-height:1.6;"><strong>Au niveau national</strong>, vous recevrez aussi des appels d'offres venant de <strong>toute la France</strong> &mdash; un complément précieux à votre démarche commerciale régionale, qui vous ouvre des dates et des territoires que vous n'auriez pas prospectés seul.</p>
        <p style="margin:0;font-size:13px;color:#555;font-style:italic;line-height:1.6;">C'est en accompagnant les compagnies qui le souhaitent dans l'édition des contrats de cession, des feuilles de route, des contrats de travail et des factures, ainsi que dans le suivi de vos contrats dans leur intégralité, et grâce à nos services optionnels annexes que nous assurons la <strong>pérennité</strong> et l'<strong>entretien</strong> du site.</p>
      </div>
      <p style="font-size:0.9em;color:#666;">Si vous publiez un spectacle avant cette échéance, votre compte sera conservé automatiquement, même si ce spectacle attend encore son approbation.</p>
      <p>Si ce compte est utilisé comme organisateur ou si vous avez besoin d'aide, répondez à ce message ou contactez contact@spectacleanimation.fr avant cette échéance.</p>
      <p style="margin-top:24px;">Cordialement,<br><strong>L'équipe Spectacle'ment VØtre</strong><br>contact@spectacleanimation.fr</p>
    </div>
  </div>
</body></html>"""
    return MailMessage(
        subject="Votre compte Spectacle'ment VØtre sera supprimé dans 48 heures",
        recipients=[],
        html=body,
    )


def _monthly_targets():
    protected = _latest_ids() | PROTECTED_USER_IDS
    users = User.query.filter(
        User.is_admin.is_(False),
        User.is_organisateur.is_(False),
        ~User.shows.any(),
        User.created_at.isnot(None),
        User.pending_deletion_at.is_(None),
        ~User.id.in_(protected),
    ).order_by(User.created_at.asc(), User.id.asc()).all()
    requesters = _requester_ids(users) if users else set()
    selected = []
    for user in users:
        notice = InactiveAccountPurgeNotice.query.filter_by(user_id=user.id).first()
        if user.id in requesters:
            continue
        # A cancelled notice is an explicit protection, not a new monthly candidate.
        if notice is not None and notice.status != "notice_failed":
            continue
        selected.append(user)
    return selected


def send_notices(confirm, monthly=False):
    with app.app_context():
        users, errors = (_monthly_targets(), []) if monthly else _validate_targets()
        if errors:
            print("ARRÊT : vérification des candidats échouée.")
            for error in errors:
                print(f" - {error}")
            return 1

        print(f"Candidats vérifiés : {len(users)}")
        for user in users:
            deadline = _utcnow() + NOTICE_DURATION
            print(
                f"{user.id} | {user.username} | {user.email} | "
                f"échéance {deadline.strftime('%d/%m/%Y %H:%M UTC')}"
            )

        if not confirm:
            print("DRY-RUN : aucun email envoyé, aucun préavis enregistré.")
            return 0

        if not users:
            print("Aucun nouveau compte à prévenir.")
            return 0
        if (
            MailMessage is None
            or not getattr(app, "mail", None)
            or not app.config.get("MAIL_USERNAME")
            or not app.config.get("MAIL_PASSWORD")
            or app.config.get("MAIL_SUPPRESS_SEND")
            or getattr(app.extensions.get("mail"), "suppress", False)
        ):
            print("ERREUR : configuration email absente; aucun avis envoyé.")
            return 1

        sent = 0
        errors = 0
        for user in users:
            user_id = user.id
            notice_id = None
            try:
                if not user.email or "@" not in user.email or any(c.isspace() for c in user.email):
                    raise ValueError(f"Adresse email inexploitable pour l'ID {user_id}.")
                notice = InactiveAccountPurgeNotice.query.filter_by(
                    user_id=user_id
                ).populate_existing().with_for_update().first()
                if notice is not None and notice.status != "notice_failed":
                    print(f"[IGNORÉ] ID {user_id} : préavis déjà traité ou en cours.")
                    db.session.rollback()
                    continue
                started = _utcnow()
                deadline = started + NOTICE_DURATION
                if notice is None:
                    notice = InactiveAccountPurgeNotice(
                        user_id=user_id,
                        email=user.email,
                        notified_at=started,
                        delete_after=deadline,
                        status="sending",
                    )
                    db.session.add(notice)
                else:
                    notice.status = "sending"
                    notice.email = user.email
                db.session.commit()
                notice_id = notice.id
                message = _notice_message(user.username, deadline)
                message.recipients = [user.email]
                try:
                    app.mail.send(message)
                except Exception:
                    notice.status = "notice_failed"
                    db.session.commit()
                    raise
                notice.notified_at = _utcnow()
                notice.delete_after = notice.notified_at + NOTICE_DURATION
                notice.status = "pending"
                notice.last_error = None
                db.session.commit()
                sent += 1
                print(f"[OK] Préavis envoyé à l'ID {user_id} ({user.email}).")
            except Exception as exc:
                db.session.rollback()
                errors += 1
                if notice_id is not None:
                    notice = db.session.get(InactiveAccountPurgeNotice, notice_id)
                    notice.last_error = str(exc)
                    db.session.commit()
                print(f"[ERREUR] ID {user_id}, email/préavis non confirmé : {exc}")

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
        now = _utcnow()
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
            notice_id = notice.id
            user_id = notice.user_id
            notice = InactiveAccountPurgeNotice.query.filter_by(
                id=notice_id, status="pending"
            ).populate_existing().with_for_update().first()
            if notice is None:
                continue
            if notice.delete_after > now or notice.notified_at + NOTICE_DURATION > now:
                print(f"[ATTENTE] ID {user_id} : délai complet de 48 heures non écoulé.")
                db.session.rollback()
                continue
            user = User.query.filter_by(id=notice.user_id).with_for_update().first()
            reason = None
            if user is None:
                reason = "compte déjà absent"
            elif user.id in PROTECTED_USER_IDS or user.id in _latest_ids() or user.is_admin:
                reason = "compte protégé ou administrateur"
            elif user.is_organisateur:
                reason = "compte organisateur"
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
        ).with_for_update().first()
        if notice is None:
            print(f"Aucun préavis en attente pour l'ID {user_id}.")
            return 1

        print(f"Préavis en attente pour l'ID {user_id}, échéance "
              f"{notice.delete_after.strftime('%d/%m/%Y %H:%M UTC')}.")
        if not confirm:
            print("DRY-RUN : préavis non annulé.")
            return 0

        notice.status = "cancelled"
        notice.completed_at = _utcnow()
        notice.last_error = "Préavis annulé manuellement."
        notice.email = None
        db.session.commit()
        print(f"Préavis annulé pour l'ID {user_id}.")
        return 0


def run_automatic(confirm_notices=False, confirm_delete=False):
    with app.app_context():
        marker = db.session.get(InactiveAccountPurgeDatabase, 1)
        expected = os.environ.get("PURGE_EXPECTED_DATABASE_ID", "")
        if not expected or marker is None or marker.identity != expected:
            print("ARRÊT : identité de base absente ou différente de PURGE_EXPECTED_DATABASE_ID.")
            return 1
        if db.engine.dialect.name != "postgresql":
            print("ARRÊT : le cron automatique nécessite PostgreSQL.")
            return 1
        print(f"Base vérifiée : {marker.identity}")
        print(f"Utilisateurs : {User.query.count()}")
        print(f"Préavis en attente : {InactiveAccountPurgeNotice.query.filter_by(status='pending').count()}")
        db.session.rollback()
        with _automatic_lock() as acquired:
            if not acquired:
                print("Maintenance déjà en cours : aucun traitement concurrent.")
                return 0
            result = process_due(confirm_delete)
            if _utcnow().day == 5:
                result = max(result, send_notices(confirm_notices, monthly=True))
            else:
                print("Préavis mensuels : prochain passage le 5 (UTC).")
            return result


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
    parser.add_argument("--monthly-notices", action="store_true",
                        help="Sélectionner les nouveaux candidats mensuels (dry-run).")
    parser.add_argument("--automatic", action="store_true",
                        help="Traiter les échéances et envoyer les préavis le 5 (UTC).")
    parser.add_argument("--database-status", action="store_true",
                        help="Afficher l'identité non secrète de la base et les compteurs.")
    parser.add_argument("--register-database", action="store_true",
                        help="Enregistrer l'identité depuis le Shell du service Web.")
    args = parser.parse_args()

    selected_modes = sum((
        args.send_notices,
        args.process_due,
        args.cancel_notice is not None,
        args.monthly_notices,
        args.automatic,
        args.database_status,
        args.register_database,
    ))
    if selected_modes != 1:
        parser.error(
            "Choisissez exactement une action."
        )
    if args.confirm_notices and not (args.send_notices or args.monthly_notices or args.automatic):
        parser.error("--confirm-notices nécessite une action d'envoi.")
    if args.confirm_delete and not (args.process_due or args.automatic):
        parser.error("--confirm-delete nécessite --process-due ou --automatic.")
    if args.confirm_cancel and args.cancel_notice is None:
        parser.error("--confirm-cancel nécessite --cancel-notice.")

    if args.send_notices:
        return send_notices(args.confirm_notices)
    if args.process_due:
        return process_due(args.confirm_delete)
    if args.monthly_notices:
        return send_notices(args.confirm_notices, monthly=True)
    if args.automatic:
        return run_automatic(args.confirm_notices, args.confirm_delete)
    if args.database_status or args.register_database:
        return database_status(args.register_database)
    return cancel_notice(args.cancel_notice, args.confirm_cancel)


if __name__ == "__main__":
    raise SystemExit(main())
