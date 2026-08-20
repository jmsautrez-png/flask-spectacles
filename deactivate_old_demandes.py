"""
Script à exécuter périodiquement (cron / Render Cron Job, ex. quotidien) pour
« acter » en base la désactivation des annonces (DemandeAnimation) parues
depuis plus de DemandeAnimation.DESACTIVATION_JOURS jours (7 par défaut).

L'actage consiste à renseigner `desactivee_at = datetime.utcnow()`. Cela
persiste l'état de désactivation (au lieu d'être calculé à la volée), ce qui :
  - fige la date exacte de désactivation (audit / stats),
  - permet un filtrage SQL rapide côté requêtes,
  - reste cohérent même si `created_at` était rétroactivement modifié.

Côté affichage, la property `DemandeAnimation.is_desactivee` reste vraie
soit parce que `desactivee_at` est renseigné, soit (fallback) parce que le
délai depuis `created_at` est dépassé — donc rien ne « clignote » entre
deux exécutions du cron.

Usage :
    python deactivate_old_demandes.py
"""
from datetime import datetime, timedelta

from app import app, db
from models.models import DemandeAnimation

try:
    from flask_mail import Message as MailMessage  # type: ignore
except Exception:
    MailMessage = None  # type: ignore


def _send_admin_recap(nb_actees: int, lignes: list) -> None:
    """Recap quotidien à l'admin (envoyé même si 0) pour confirmer que le cron a tourné."""
    if MailMessage is None or not getattr(app, "mail", None):
        return
    if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
        return
    admin_email = app.config.get("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_USERNAME")
    if not admin_email:
        return
    seuil = DemandeAnimation.DESACTIVATION_JOURS
    if nb_actees == 0:
        body_html = (
            f"<p>Cron <strong>deactivate_old_demandes</strong> OK.</p>"
            f"<p>Aucune nouvelle annonce à désactiver aujourd'hui (seuil : {seuil} jours).</p>"
        )
        subject = "[Cron] Aucune annonce à désactiver"
    else:
        rows = "".join(f"<li>{l}</li>" for l in lignes)
        body_html = (
            f"<p>Cron <strong>deactivate_old_demandes</strong> OK.</p>"
            f"<p><strong>{nb_actees}</strong> annonce(s) désactivée(s) (seuil : {seuil} jours) :</p>"
            f"<ul>{rows}</ul>"
        )
        subject = f"[Cron] {nb_actees} annonce(s) désactivée(s)"
    try:
        msg = MailMessage(subject=subject, recipients=[admin_email])
        msg.html = body_html
        app.mail.send(msg)  # type: ignore[attr-defined]
        print(f"  Recap admin envoye a {admin_email}")
    except Exception as e:
        print(f"  Recap admin non envoye: {e}")


def main() -> None:
    seuil_jours = DemandeAnimation.DESACTIVATION_JOURS
    now = datetime.utcnow()
    limite = now - timedelta(days=seuil_jours)

    with app.app_context():
        candidats = (
            DemandeAnimation.query
            .filter(DemandeAnimation.desactivee_at.is_(None))
            .filter(DemandeAnimation.created_at.isnot(None))
            .filter(DemandeAnimation.created_at <= limite)
            .order_by(DemandeAnimation.created_at.asc())
            .all()
        )

        if not candidats:
            print(f"Aucune annonce à désactiver (seuil : {seuil_jours} jours).")
            _send_admin_recap(0, [])
            return

        print(f"{len(candidats)} annonce(s) à désactiver (créée(s) avant {limite:%Y-%m-%d %H:%M} UTC).")
        lignes = []
        nb_actees = 0
        for d in candidats:
            age_jours = (now - d.created_at).days if d.created_at else "?"
            libelle = (d.intitule or d.genre_recherche or "").strip() or "(sans intitulé)"
            if len(libelle) > 60:
                libelle = libelle[:57] + "…"
            ligne = f"#{d.id} - {libelle} - {d.structure or '?'} - {age_jours}j"
            print(f"  ⏹️  {ligne}")
            d.desactivee_at = now
            lignes.append(ligne)
            nb_actees += 1

        try:
            db.session.commit()
            print(f"\n✅ Terminé : {nb_actees} annonce(s) désactivée(s).")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Erreur commit : {e}")
            return

        _send_admin_recap(nb_actees, lignes)


if __name__ == "__main__":
    main()
