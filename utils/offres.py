"""Per-company offer delivery and restricted display."""

from types import SimpleNamespace
from secrets import token_hex

from flask import session
from sqlalchemy.exc import IntegrityError

from models import db
from models.models import AppelOffreConsultation, AppelOffreEnvoi, DemandeAnimation


def record_offer_consultation(demande, user):
    if user and user.is_admin:
        return
    key = session.get("offer_consultation_key")
    if key is None:
        key = token_hex(16)
        session["offer_consultation_key"] = key
    if AppelOffreConsultation.query.filter_by(
        demande_id=demande.id, session_key=key,
    ).first():
        return
    try:
        db.session.add(AppelOffreConsultation(demande_id=demande.id, session_key=key))
        db.session.flush()
        DemandeAnimation.query.filter_by(id=demande.id).update({
            DemandeAnimation.consultations_count: DemandeAnimation.consultations_count + 1,
        })
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Concurrent openings of the same offer in one session count only once.
        if not AppelOffreConsultation.query.filter_by(
            demande_id=demande.id, session_key=key,
        ).first():
            raise


def needs_offer_subscription(user):
    return bool(
        user and user.is_modele_payant and not user.is_subscribed
        and not user.is_admin
    )


def gift_selected(user, user_ids):
    return bool(
        needs_offer_subscription(user) and not user.bloque_appels_offres
        and user.id in user_ids
    )


def offered_ids(user):
    if not user or user.bloque_appels_offres:
        return set()
    return {
        row.demande_id for row in AppelOffreEnvoi.query.filter_by(
            user_id=user.id, offert=True,
        ).all()
    }


def record_offer_delivery(user, demande, gift=False):
    """Persist only after SMTP success; an existing gift is never revoked."""
    if not needs_offer_subscription(user):
        return
    delivery = AppelOffreEnvoi.query.filter_by(
        user_id=user.id, demande_id=demande.id,
    ).first()
    if delivery is None:
        delivery = AppelOffreEnvoi(user_id=user.id, demande_id=demande.id, offert=gift)
        db.session.add(delivery)
    elif gift:
        delivery.offert = True
    if gift:
        user.cadeaux_offerts_count = (user.cadeaux_offerts_count or 0) + 1
    else:
        user.apercus_envoyes_count = (user.apercus_envoyes_count or 0) + 1
    db.session.commit()


def delivery_recap_entry(user, email, title, gift=False, show=None, tracked=True):
    eligible = needs_offer_subscription(user)
    mode = "cadeau" if eligible and gift else "apercu" if eligible else "complet"
    return {
        "email": email, "title": title, "show": show, "mode": mode,
        "tracked": tracked,
        "cadeaux": (user.cadeaux_offerts_count or 0) if eligible else None,
        "apercus": (user.apercus_envoyes_count or 0) if eligible else None,
    }


def offer_view(demande, user, gifts):
    """Never put restricted contact/free-text values in rendered HTML."""
    restricted = needs_offer_subscription(user) and demande.id not in gifts
    inactive = demande.is_desactivee and not (user and user.is_admin)
    values = {col.name: getattr(demande, col.name) for col in demande.__table__.columns}
    values.pop("consultations_count", None)
    if restricted:
        for name in (
            "nom", "telephone", "contact_email", "code_postal", "intitule",
            "contraintes", "accessibilite", "type_espace", "dates_horaires",
            "auto_datetime", "latitude", "longitude",
        ):
            values[name] = None
        values["structure"] = "Organisateur masqué"
        values["lieu_ville"] = "Ville masquée"
        values["dates_horaires"] = "Dates disponibles avec l'abonnement"
    elif inactive:
        for name in ("nom", "telephone", "contact_email"):
            values[name] = None
    values["is_desactivee"] = demande.is_desactivee
    values["offert"] = demande.id in gifts
    values["acces_complet"] = not restricted
    return SimpleNamespace(**values)
