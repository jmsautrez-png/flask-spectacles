from datetime import datetime

import pytest


def make_adhesion(db, user, **fields):
    from models.models import Adhesion

    adh = Adhesion(
        user=user, nom="Test", email=user.email, telephone="0102030405",
        **fields,
    )
    db.session.add(adh)
    db.session.commit()
    return adh


def login(client, user):
    with client.session_transaction() as session:
        session["username"] = user.username


@pytest.mark.parametrize("statut", ["pending", "contacted", "rejected"])
def test_delete_only_internal_request(client, admin_user, normal_user, statut):
    from models import db
    from models.models import Adhesion, Show, User

    normal_user.is_subscribed = True
    normal_user.subscribed_until = datetime(2027, 11, 3)
    show = Show(title="Spectacle conservé", user=normal_user)
    db.session.add(show)
    db.session.commit()
    show_id, user_id = show.id, normal_user.id
    adh = make_adhesion(db, normal_user, statut=statut)
    adh_id = adh.id
    login(client, admin_user)
    page = client.get("/admin/adhesions").get_data(as_text=True)
    assert f"/admin/adhesions/{adh_id}/delete" in page
    assert "Le compte utilisateur et ses spectacles seront conservés." in page
    response = client.post(f"/admin/adhesions/{adh_id}/delete")
    assert response.status_code == 302
    db.session.expire_all()
    assert db.session.get(Adhesion, adh_id) is None
    assert db.session.get(Show, show_id) is not None
    user = db.session.get(User, user_id)
    assert user.is_subscribed
    assert user.subscribed_until == datetime(2027, 11, 3)


@pytest.mark.parametrize("fields", [
    {"statut": "activated"},
    {"statut": "rejected", "activated_at": datetime(2026, 10, 1)},
    {"statut": "pending", "invoice_number": "2026-001"},
    {"statut": "contacted", "invoice_sent_at": datetime(2026, 10, 1)},
])
def test_protected_requests_hidden_and_rejected_server_side(
    client, admin_user, normal_user, fields,
):
    from models import db
    from models.models import Adhesion

    adh = make_adhesion(db, normal_user, **fields)
    adh_id = adh.id
    login(client, admin_user)
    page = client.get("/admin/adhesions").get_data(as_text=True)
    assert f"/admin/adhesions/{adh_id}/delete" not in page
    response = client.post(f"/admin/adhesions/{adh_id}/delete", follow_redirects=True)
    assert "Suppression impossible" in response.get_data(as_text=True)
    assert db.session.get(Adhesion, adh_id) is not None


@pytest.mark.parametrize("authenticated", [False, True])
def test_admin_only(client, normal_user, authenticated):
    from models import db
    from models.models import Adhesion

    adh = make_adhesion(db, normal_user, statut="pending")
    adh_id = adh.id
    if authenticated:
        login(client, normal_user)
    response = client.post(f"/admin/adhesions/{adh_id}/delete")
    assert response.status_code in (302, 403)
    assert db.session.get(Adhesion, adh_id) is not None


def test_post_only_and_missing_request(client, admin_user):
    login(client, admin_user)
    assert client.get("/admin/adhesions/999999/delete").status_code == 405
    assert client.post("/admin/adhesions/999999/delete").status_code == 404


def test_delete_requires_csrf_token(client, admin_user, normal_user, monkeypatch):
    from models import db
    from models.models import Adhesion

    adh = make_adhesion(db, normal_user, statut="pending")
    adh_id = adh.id
    login(client, admin_user)
    monkeypatch.setitem(client.application.config, "WTF_CSRF_ENABLED", True)
    response = client.post(f"/admin/adhesions/{adh_id}/delete", follow_redirects=True)
    assert "Votre session a expiré" in response.get_data(as_text=True)
    assert db.session.get(Adhesion, adh_id) is not None
