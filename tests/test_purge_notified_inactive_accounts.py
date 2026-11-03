from datetime import datetime, timedelta

import pytest


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
    monkeypatch.setattr(purge, "_latest_ids", lambda: set())
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


def _notice(db, user, age=timedelta(hours=49), **overrides):
    from models.models import InactiveAccountPurgeNotice

    sent = datetime.utcnow() - age
    fields = dict(
        user_id=user.id, email=user.email, notified_at=sent,
        delete_after=sent + timedelta(hours=48), status="pending",
    )
    fields.update(overrides)
    notice = InactiveAccountPurgeNotice(**fields)
    db.session.add(notice)
    db.session.commit()
    return notice


def test_monthly_selection_protects_latest_seven_and_requesters(db, monkeypatch):
    import purge_notified_inactive_accounts as purge
    from models.models import User, Show

    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    users = [
        User(username=f"monthly-{i}", password_hash="test",
             email=f"monthly-{i}@example.test",
             created_at=datetime(2026, 1, 1) + timedelta(days=i))
        for i in range(16)
    ]
    db.session.add_all(users)
    db.session.flush()
    users[0].is_admin = True
    users[1].is_organisateur = True
    users[5].pending_deletion_at = datetime(2026, 12, 1)
    db.session.add_all([
        _make_demande(users[2].email, users[2].id),
        _make_demande("  MONTHLY-3@EXAMPLE.TEST "),
        Show(title="Draft", user=users[4], approved=False),
    ])
    db.session.commit()
    _notice(db, users[6], status="cancelled")
    _notice(db, users[7])

    assert [user.id for user in purge._monthly_targets()] == [users[8].id]


@pytest.mark.parametrize("protection", ["organiser", "admin", "draft", "request", "latest"])
def test_due_account_protection(db, normal_user, monkeypatch, protection):
    import purge_notified_inactive_accounts as purge
    from models.models import Show, User

    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    monkeypatch.setattr(purge, "_latest_ids", lambda: set())
    notice = _notice(db, normal_user)
    if protection == "organiser":
        normal_user.is_organisateur = True
    elif protection == "admin":
        normal_user.is_admin = True
    elif protection == "draft":
        db.session.add(Show(title="Draft", user=normal_user, approved=False))
    elif protection == "request":
        db.session.add(_make_demande(normal_user.email.upper()))
    else:
        monkeypatch.setattr(purge, "_latest_ids", lambda: {normal_user.id})
    db.session.commit()

    assert purge.process_due(True) == 0
    assert db.session.get(User, normal_user.id) is not None
    db.session.refresh(notice)
    assert notice.status == "cancelled"
    assert notice.email is None


def test_delete_due_monthly_account_once(db, normal_user, monkeypatch):
    import purge_notified_inactive_accounts as purge
    from models.models import User

    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    monkeypatch.setattr(purge, "_latest_ids", lambda: set())
    calls = []
    monkeypatch.setattr(purge, "notify_admin_show_deletion", lambda *args: calls.append(args))
    uid = normal_user.id
    notice = _notice(db, normal_user)
    assert purge.process_due(False) == 0
    assert db.session.get(User, uid) is not None
    assert purge.process_due(True) == 0
    db.session.expire_all()
    assert db.session.get(User, uid) is None
    db.session.refresh(notice)
    assert notice.status == "deleted"
    assert notice.email is None
    assert purge.process_due(True) == 0
    assert len(calls) == 1


def test_no_delete_before_48_hours_even_with_early_deadline(db, normal_user, monkeypatch):
    import purge_notified_inactive_accounts as purge
    from models.models import User

    notice = _notice(
        db, normal_user, age=timedelta(hours=47),
        delete_after=datetime.utcnow() - timedelta(seconds=1),
    )
    assert purge.process_due(True) == 0
    assert db.session.get(User, normal_user.id) is not None
    db.session.refresh(notice)
    assert notice.status == "pending"


class FakeMail:
    def __init__(self, fail=False):
        self.messages = []
        self.fail = fail

    def send(self, message):
        if self.fail:
            raise RuntimeError("SMTP unavailable")
        self.messages.append(message)


@pytest.mark.parametrize("fail", [False, True])
def test_monthly_notice_idempotency_and_smtp_failure(db, normal_user, monkeypatch, fail):
    import purge_notified_inactive_accounts as purge
    from models.models import InactiveAccountPurgeNotice

    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    monkeypatch.setattr(purge, "_latest_ids", lambda: set())
    mail = FakeMail(fail)
    monkeypatch.setattr(purge.app, "mail", mail)
    monkeypatch.setitem(purge.app.config, "MAIL_USERNAME", "fake")
    monkeypatch.setitem(purge.app.config, "MAIL_PASSWORD", "fake")
    monkeypatch.setitem(purge.app.config, "MAIL_SUPPRESS_SEND", False)
    monkeypatch.setattr(purge.app.extensions["mail"], "suppress", False)

    assert purge.send_notices(False, monthly=True) == 0
    assert InactiveAccountPurgeNotice.query.count() == 0
    before = datetime.utcnow()
    assert purge.send_notices(True, monthly=True) == (1 if fail else 0)
    notice = InactiveAccountPurgeNotice.query.one()
    if fail:
        assert notice.status == "notice_failed"
        assert purge.process_due(True) == 0
        assert "SMTP unavailable" in notice.last_error
    else:
        assert notice.status == "pending"
        assert notice.notified_at >= before
        assert notice.delete_after - notice.notified_at == timedelta(hours=48)
        assert purge.send_notices(True, monthly=True) == 0
        assert len(mail.messages) == 1


def test_database_identity_registration_is_stable_and_not_automatic(db, monkeypatch, capsys):
    import purge_notified_inactive_accounts as purge
    from models.models import InactiveAccountPurgeDatabase

    monkeypatch.setenv("PURGE_EXPECTED_DATABASE_ID", "wrong")
    assert purge.run_automatic(True, True) == 1
    assert InactiveAccountPurgeDatabase.query.count() == 0
    assert purge.database_status(True) == 0
    marker = InactiveAccountPurgeDatabase.query.one()
    identity = marker.identity
    assert purge.database_status(True) == 0
    assert marker.identity == identity
    assert purge.run_automatic(True, True) == 1
    monkeypatch.setenv("PURGE_EXPECTED_DATABASE_ID", identity)
    # Even the matching marker must not permit destructive SQLite automation.
    assert purge.run_automatic(True, True) == 1
    assert "nécessite PostgreSQL" in capsys.readouterr().out


@pytest.mark.parametrize("day,expected_sends", [(4, 0), (5, 1), (6, 0)])
def test_automatic_schedule(db, monkeypatch, day, expected_sends):
    from contextlib import contextmanager
    import purge_notified_inactive_accounts as purge
    from models.models import InactiveAccountPurgeDatabase

    db.session.add(InactiveAccountPurgeDatabase(id=1, identity="verified"))
    db.session.commit()
    monkeypatch.setenv("PURGE_EXPECTED_DATABASE_ID", "verified")
    monkeypatch.setattr(db.engine.dialect, "name", "postgresql")
    monkeypatch.setattr(purge, "_utcnow", lambda: datetime(2026, 12, day, 2))
    @contextmanager
    def locked():
        yield True
    monkeypatch.setattr(purge, "_automatic_lock", locked)
    sends, deletes = [], []
    monkeypatch.setattr(purge, "send_notices",
                        lambda confirm, monthly=False: sends.append((confirm, monthly)) or 0)
    monkeypatch.setattr(purge, "process_due",
                        lambda confirm: deletes.append(confirm) or 0)
    assert purge.run_automatic(True, True) == 0
    assert len(sends) == expected_sends
    assert deletes == [True]


def test_smtp_failure_can_retry_but_sending_and_pending_cannot(db, normal_user, monkeypatch):
    import purge_notified_inactive_accounts as purge
    from models.models import InactiveAccountPurgeNotice

    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    monkeypatch.setattr(purge, "_latest_ids", lambda: set())
    mail = FakeMail()
    monkeypatch.setattr(purge.app, "mail", mail)
    monkeypatch.setitem(purge.app.config, "MAIL_USERNAME", "fake")
    monkeypatch.setitem(purge.app.config, "MAIL_PASSWORD", "fake")
    monkeypatch.setitem(purge.app.config, "MAIL_SUPPRESS_SEND", False)
    monkeypatch.setattr(purge.app.extensions["mail"], "suppress", False)
    notice = _notice(db, normal_user, status="sending")
    assert purge.send_notices(True, monthly=True) == 0
    assert mail.messages == []
    notice.status = "notice_failed"
    db.session.commit()
    assert purge.send_notices(True, monthly=True) == 0
    db.session.refresh(notice)
    assert notice.status == "pending"
    assert InactiveAccountPurgeNotice.query.count() == 1
    assert len(mail.messages) == 1
    assert purge.send_notices(True, monthly=True) == 0
    assert len(mail.messages) == 1


def test_manual_cancel_prevents_deletion_and_future_notices(db, normal_user, monkeypatch):
    import purge_notified_inactive_accounts as purge

    monkeypatch.setattr(purge, "PROTECTED_USER_IDS", frozenset())
    monkeypatch.setattr(purge, "_latest_ids", lambda: set())
    notice = _notice(db, normal_user)
    assert purge.cancel_notice(normal_user.id, False) == 0
    db.session.refresh(notice)
    assert notice.status == "pending"
    assert purge.cancel_notice(normal_user.id, True) == 0
    db.session.refresh(notice)
    assert notice.status == "cancelled"
    assert purge._monthly_targets() == []
    assert purge.process_due(True) == 0


def test_historical_maintenance_leaves_monthly_notice_alone(client, admin_user, normal_user):
    from models import db
    from models.models import User

    normal_user.pending_deletion_at = datetime.utcnow() - timedelta(days=1)
    db.session.commit()
    notice = _notice(db, normal_user)
    uid = normal_user.id
    with client.session_transaction() as session:
        session["username"] = admin_user.username
    response = client.post("/admin/inactive-users/maintenance")
    assert response.status_code == 302
    db.session.expire_all()
    assert db.session.get(User, uid) is not None
    db.session.refresh(notice)
    assert notice.status == "pending"
