from datetime import datetime, timedelta


def _make_demande(email, user_id=None):
    from models.models import DemandeAnimation

    return DemandeAnimation(
        structure="Association",
        telephone="0102030405",
        lieu_ville="Paris",
        nom="Contact",
        dates_horaires="2026-12-01",
        type_espace="Salle",
        genre_recherche="Musique",
        age_range="Tout public",
        jauge="100",
        budget="1000",
        contact_email=email,
        user_id=user_id,
    )


def test_target_validation_excludes_animation_requesters(db, normal_user, monkeypatch):
    import purge_notified_inactive_accounts as purge

    normal_user.email = "Organizer@example.test"
    monkeypatch.setattr(purge, "TARGET_USER_IDS", (normal_user.id,))
    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    db.session.commit()

    _, errors = purge._validate_targets()
    assert errors == []

    db.session.add(_make_demande("organizer@example.test"))
    db.session.commit()

    _, errors = purge._validate_targets()
    assert any("demande d'animation" in error for error in errors)


def test_due_notice_is_cancelled_if_request_arrives(db, normal_user, monkeypatch, capsys):
    import purge_notified_inactive_accounts as purge
    from models.models import InactiveAccountPurgeNotice

    monkeypatch.setattr(purge, "TARGET_USER_IDS", (normal_user.id,))
    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    now = datetime.utcnow()
    notice = InactiveAccountPurgeNotice(
        user_id=normal_user.id,
        email=normal_user.email,
        notified_at=now - timedelta(days=2),
        delete_after=now - timedelta(seconds=1),
        status="pending",
    )
    db.session.add_all([notice, _make_demande(normal_user.email, normal_user.id)])
    db.session.commit()

    assert purge.process_due(confirm=True) == 0

    db.session.refresh(notice)
    assert db.session.get(type(normal_user), normal_user.id) is normal_user
    assert notice.status == "cancelled"
    assert "demande d'animation" in notice.last_error
    assert "[CONSERVÉ]" in capsys.readouterr().out


def test_notice_email_escapes_username(app):
    from purge_notified_inactive_accounts import _notice_message

    with app.app_context():
        message = _notice_message(
            "<script>alert(1)</script>",
            datetime(2026, 11, 5, 12, 0),
        )
    assert "<script>" not in message.html
    assert "&lt;script&gt;" in message.html
    assert "48 heures" in message.subject
