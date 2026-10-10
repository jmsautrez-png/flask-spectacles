"""Offer previews, explicit gifts, and per-company access (no real SMTP)."""

from datetime import datetime, timedelta

import pytest


@pytest.fixture
def offer_setup(app, client, normal_user, admin_user):
    from models import db
    from models.models import DemandeAnimation, Show

    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    normal_user.created_at = datetime(2026, 9, 12)
    show = Show(
        title="Test company", user=normal_user, approved=True,
        specialites="Clown", category="Clown", region="Bretagne",
        public_categories="famille", public_sous_options="fam_10",
        contact_email=normal_user.email,
    )
    fields = dict(
        structure="SECRET_STRUCTURE", nom="SECRET_NAME",
        telephone="SECRET_PHONE", contact_email="secret-contact@example.test",
        lieu_ville="SECRET_CITY", code_postal="99991",
        dates_horaires="SECRET_DATE_TEXT", type_espace="SECRET_SPACE",
        genre_recherche="Clown", age_range="fam_10",
        jauge="100", budget="1000", region="Bretagne",
        intitule="SECRET_DESCRIPTION", contraintes="SECRET_CONSTRAINT",
        accessibilite="SECRET_ACCESS", approved=True,
        public_categories="famille", public_sous_options="fam_10",
        created_at=datetime.utcnow(),
    )
    demande = DemandeAnimation(**fields)
    other = DemandeAnimation(**{**fields, "contact_email": "other-secret@example.test"})
    db.session.add_all([show, demande, other])
    db.session.commit()
    return normal_user, admin_user, show, demande, other


class FakeMail:
    def __init__(self, fail_recipient=None):
        self.messages = []
        self.fail_recipient = fail_recipient

    def connect(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def send(self, message):
        if self.fail_recipient in message.recipients:
            raise RuntimeError("Simulated SMTP failure")
        self.messages.append(message)


def login(client, user):
    with client.session_transaction() as session:
        session["username"] = user.username


def assert_masked(html):
    for value in (
        "SECRET_NAME", "SECRET_PHONE", "secret-contact@example.test",
        "SECRET_CITY", "SECRET_STRUCTURE", "99991", "SECRET_DESCRIPTION",
        "SECRET_CONSTRAINT", "SECRET_ACCESS", "SECRET_SPACE", "SECRET_DATE_TEXT",
    ):
        assert value not in html


@pytest.mark.parametrize("viewer", ["anonymous", "no-approved-show", "needs-subscription"])
def test_public_offer_cta_price_preserves_destination(client, offer_setup, viewer):
    from html.parser import HTMLParser
    from models import db

    user, admin, show, demande, other = offer_setup
    if viewer != "anonymous":
        login(client, user)
    if viewer == "no-approved-show":
        show.approved = False
        user.created_at = datetime(2026, 9, 11)
        db.session.commit()
    response = client.get("/demandes-animation")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    emoji = "🔓" if viewer == "needs-subscription" else "🔒"
    label = f"{emoji} Appels d'offres illimités : 49 € TTC la première année, puis 99 €/an"

    class PriceLinks(HTMLParser):
        def __init__(self):
            super().__init__()
            self.href = None
            self.matches = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.href = dict(attrs).get("href")

        def handle_data(self, data):
            if data == label:
                self.matches.append(self.href)

    links = PriceLinks()
    links.feed(html)
    destination = {
        "anonymous": "/register",
        "no-approved-show": "/dashboard",
        "needs-subscription": "/adhesion",
    }[viewer]
    assert links.matches
    assert all(href == destination for href in links.matches)
    assert "Publier votre spectacle pour voir l'intitulé complet" not in html


@pytest.mark.parametrize("action", ["send_matched", "send"])
@pytest.mark.parametrize("gift", [False, True])
def test_admin_send_uses_explicit_gift_only(app, client, offer_setup, monkeypatch, action, gift):
    from models.models import AppelOffreEnvoi
    user, admin, show, demande, other = offer_setup
    mail = FakeMail()
    monkeypatch.setattr(app, "mail", mail)
    login(client, admin)
    data = {
        "action": action, "matched_show_ids": [str(show.id)],
        "emails[]": [user.email], "categories": ["Clown"],
    }
    if gift:
        data["gift_user_ids"] = [str(user.id)]
    response = client.post(f"/admin/envoyer-demande/{demande.id}", data=data)
    assert response.status_code == 302
    sent = [m for m in mail.messages if m.recipients == [user.email]]
    assert len(sent) == 1
    delivery = AppelOffreEnvoi.query.filter_by(user_id=user.id, demande_id=demande.id).one()
    assert delivery.offert is gift
    assert user.cadeaux_offerts_count == int(gift)
    assert user.apercus_envoyes_count == int(not gift)
    recap = next(m for m in mail.messages if m.subject.startswith("[ADMIN]"))
    assert "Bilan des envois réussis" in recap.html
    assert "Total aperçus" in recap.html
    assert user.email in recap.html
    assert ("Offre cadeau" if gift else "Aperçu masqué") in recap.html
    assert AppelOffreEnvoi.query.filter_by(demande_id=other.id).count() == 0
    if gift:
        assert "secret-contact@example.test" in sent[0].html
        assert "SECRET_PHONE" in sent[0].html
        assert "offert" in sent[0].html
    else:
        assert_masked(sent[0].html + sent[0].subject)
        assert "Je découvre l'abonnement" in sent[0].html
        assert "Une belle occasion pour votre compagnie !" in sent[0].html
        assert "Pourquoi ne pas vous abonner" in sent[0].html
        assert "🔒" not in sent[0].html
        assert f"/appels-offres/{demande.id}" in sent[0].html
    login(client, user)
    html = client.get(f"/appels-offres/{demande.id}").get_data(as_text=True)
    if gift:
        assert "secret-contact@example.test" in html
    else:
        assert_masked(html)
        assert "Je découvre l'abonnement" in html
        assert "Pourquoi ne pas vous abonner" in html
        assert "🔒" not in html
    assert_masked(client.get(f"/appels-offres/{other.id}").get_data(as_text=True))


@pytest.mark.parametrize("action", ["send_matched", "send"])
def test_failed_email_does_not_grant_gift(app, client, offer_setup, monkeypatch, action):
    from models.models import AppelOffreEnvoi
    user, admin, show, demande, _ = offer_setup
    monkeypatch.setattr(app, "mail", FakeMail(fail_recipient=user.email))
    login(client, admin)
    response = client.post(f"/admin/envoyer-demande/{demande.id}", data={
        "action": action, "matched_show_ids": [str(show.id)],
        "emails[]": [user.email], "gift_user_ids": [str(user.id)],
        "categories": ["Clown"],
    })
    assert response.status_code == 302
    assert AppelOffreEnvoi.query.count() == 0
    assert user.cadeaux_offerts_count == 0
    assert user.apercus_envoyes_count == 0
    recap = next(m for m in app.mail.messages if m.subject.startswith("[ADMIN]"))
    assert "Aucun envoi réussi." in recap.html
    assert "Simulated SMTP failure" in recap.html


@pytest.mark.parametrize("path", ["/mes-appels-offres", "/demandes-animation"])
def test_listing_masks_source_and_unlocks_only_gift(client, offer_setup, path):
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup
    login(client, user)
    response = client.get(path)
    assert response.status_code == 200
    assert_masked(response.get_data(as_text=True))
    record_offer_delivery(user, demande, gift=True)
    html = client.get(path).get_data(as_text=True)
    assert "secret-contact@example.test" in html
    assert "other-secret@example.test" not in html


@pytest.mark.parametrize("kind", ["legacy", "subscriber", "admin"])
def test_existing_full_access_is_preserved(client, offer_setup, kind):
    from models import db
    user, admin, _, demande, _ = offer_setup
    if kind == "legacy":
        user.created_at = datetime(2026, 9, 11, 23, 59, 59)
    elif kind == "subscriber":
        user.is_subscribed = True
    else:
        user = admin
    db.session.commit()
    login(client, user)
    assert "secret-contact@example.test" in client.get(
        f"/appels-offres/{demande.id}",
    ).get_data(as_text=True)


def test_gift_is_scoped_to_company_and_respects_expiry_and_block(client, offer_setup):
    from models import db
    from models.models import User
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup
    record_offer_delivery(user, demande, gift=True)
    other_user = User(
        username="other-company", email="other@example.test",
        created_at=datetime(2026, 9, 13),
    )
    other_user.set_password("test-password")
    db.session.add(other_user)
    db.session.commit()
    login(client, other_user)
    # No approved show, subscription or notification: no direct access.
    assert client.get(f"/appels-offres/{demande.id}").status_code == 302
    login(client, user)
    demande.created_at = datetime.utcnow() - timedelta(days=11)
    db.session.commit()
    html = client.get(f"/appels-offres/{demande.id}").get_data(as_text=True)
    assert "secret-contact@example.test" not in html
    assert "SECRET_PHONE" not in html
    assert "désactivée" in html
    user.bloque_appels_offres = True
    db.session.commit()
    assert client.get(f"/appels-offres/{demande.id}").status_code == 302


def test_private_offer_requires_personal_notification(client, offer_setup):
    from models import db
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup
    demande.is_private = True
    demande.approved = False
    db.session.commit()
    login(client, user)
    assert client.get(f"/appels-offres/{demande.id}").status_code == 404
    record_offer_delivery(user, demande)
    assert_masked(client.get(f"/appels-offres/{demande.id}").get_data(as_text=True))
    record_offer_delivery(user, demande, gift=True)
    assert "secret-contact@example.test" in client.get(
        f"/appels-offres/{demande.id}",
    ).get_data(as_text=True)


def test_preview_never_revokes_previous_gift(offer_setup):
    from models.models import AppelOffreEnvoi
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup
    record_offer_delivery(user, demande, gift=True)
    record_offer_delivery(user, demande, gift=False)
    assert AppelOffreEnvoi.query.count() == 1
    assert AppelOffreEnvoi.query.one().offert is True
    assert user.cadeaux_offerts_count == 1
    assert user.apercus_envoyes_count == 1


def test_admin_choices_render_preview_by_default(client, offer_setup, monkeypatch, app):
    user, admin, _, demande, _ = offer_setup
    monkeypatch.setattr(app, "mail", FakeMail())
    login(client, admin)
    response = client.get(f"/admin/envoyer-demande/{demande.id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f'name="gift_user_ids" value="{user.id}"' in html
    assert "aperçu par défaut" in html
    response = client.post(f"/admin/envoyer-demande/{demande.id}", data={
        "action": "preview", "categories": ["Clown"],
    })
    assert response.status_code == 200
    assert f'name="gift_user_ids" value="{user.id}"' in response.get_data(as_text=True)


def test_gift_persistence_failure_is_reported(app, client, offer_setup, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    from utils import offres
    import app as app_module
    user, _, _, demande, _ = offer_setup

    def fail(*args, **kwargs):
        raise SQLAlchemyError("Simulated persistence failure")

    monkeypatch.setattr(offres, "record_offer_delivery", fail)
    with app.test_request_context():
        app_module._record_appel_offre_delivery(user, demande, gift=True)
        from flask import get_flashed_messages
        assert any(
            "n'a pas pu être enregistré" in message
            for message in get_flashed_messages()
        )


def test_delivery_rows_removed_with_offer(offer_setup):
    from models import db
    from models.models import AppelOffreEnvoi
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup
    record_offer_delivery(user, demande, gift=True)
    db.session.delete(demande)
    db.session.commit()
    assert AppelOffreEnvoi.query.count() == 0


@pytest.mark.parametrize("gift", [False, True])
def test_additional_regional_recipient_uses_same_rules(app, client, offer_setup, monkeypatch, gift):
    from models import db
    from models.models import AppelOffreEnvoi
    user, admin, show, demande, _ = offer_setup
    user.region = "Bretagne"
    show.contact_email = "show-contact@example.test"
    db.session.commit()
    mail = FakeMail()
    monkeypatch.setattr(app, "mail", mail)
    login(client, admin)
    data = {
        "action": "send", "categories": ["Clown"],
        "regions": ["Bretagne"], "emails[]": [user.email],
    }
    if gift:
        data["gift_user_ids"] = [str(user.id)]
    assert client.post(f"/admin/envoyer-demande/{demande.id}", data=data).status_code == 302
    sent = [m for m in mail.messages if m.recipients == [user.email]]
    assert len(sent) == 1
    assert AppelOffreEnvoi.query.one().offert is gift
    if gift:
        assert "secret-contact@example.test" in sent[0].html
        assert f"/appels-offres/{demande.id}" in sent[0].html
    else:
        assert_masked(sent[0].html + sent[0].subject)
    assert user.cadeaux_offerts_count == int(gift)
    assert user.apercus_envoyes_count == int(not gift)


@pytest.mark.parametrize("kind", ["legacy", "subscriber"])
def test_existing_users_receive_full_email_without_gift_choice(app, client, offer_setup, monkeypatch, kind):
    from models import db
    from models.models import AppelOffreEnvoi
    user, admin, show, demande, _ = offer_setup
    if kind == "legacy":
        user.created_at = datetime(2026, 9, 11)
    else:
        user.is_subscribed = True
    db.session.commit()
    mail = FakeMail()
    monkeypatch.setattr(app, "mail", mail)
    login(client, admin)
    client.post(f"/admin/envoyer-demande/{demande.id}", data={
        "action": "send_matched", "matched_show_ids": [str(show.id)],
    })
    sent = [m for m in mail.messages if m.recipients == [user.email]]
    assert len(sent) == 1
    assert "secret-contact@example.test" in sent[0].html
    assert "Cet appel d'offre vous est offert" not in sent[0].html
    assert AppelOffreEnvoi.query.count() == 0
    assert user.cadeaux_offerts_count == 0
    assert user.apercus_envoyes_count == 0


def test_blocked_company_cannot_be_given_full_offer(app, client, offer_setup, monkeypatch):
    from models import db
    from models.models import AppelOffreEnvoi
    user, admin, show, demande, _ = offer_setup
    user.bloque_appels_offres = True
    db.session.commit()
    mail = FakeMail()
    monkeypatch.setattr(app, "mail", mail)
    login(client, admin)
    client.post(f"/admin/envoyer-demande/{demande.id}", data={
        "action": "send_matched", "matched_show_ids": [str(show.id)],
        "gift_user_ids": [str(user.id)],
    })
    sent = [m for m in mail.messages if m.recipients == [user.email]]
    assert len(sent) == 1
    assert_masked(sent[0].html + sent[0].subject)
    assert AppelOffreEnvoi.query.one().offert is False
    assert user.cadeaux_offerts_count == 0


def test_only_admin_can_send_and_invalid_gift_is_rejected(app, client, offer_setup, monkeypatch):
    from models.models import AppelOffreEnvoi
    user, admin, show, demande, _ = offer_setup
    mail = FakeMail()
    monkeypatch.setattr(app, "mail", mail)
    data = {
        "action": "send_matched", "matched_show_ids": [str(show.id)],
        "gift_user_ids": ["not-an-id"],
    }
    login(client, user)
    assert client.post(f"/admin/envoyer-demande/{demande.id}", data=data).status_code in (302, 403)
    login(client, admin)
    assert client.post(f"/admin/envoyer-demande/{demande.id}", data=data).status_code == 302
    assert mail.messages == []
    assert AppelOffreEnvoi.query.count() == 0


def test_notification_rows_removed_with_company(offer_setup):
    from models import db
    from models.models import AppelOffreEnvoi
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup
    record_offer_delivery(user, demande, gift=True)
    db.session.delete(user)
    db.session.commit()
    assert AppelOffreEnvoi.query.count() == 0


@pytest.mark.parametrize(
    "path,card_id",
    [("/mes-appels-offres", "details-"), ("/demandes-animation", "deta-")],
)
def test_preview_search_uses_region_not_hidden_city(client, offer_setup, path, card_id):
    user, _, _, demande, _ = offer_setup
    login(client, user)
    html = client.get(path, query_string={"region": "Bretagne"}).get_data(as_text=True)
    assert f'id="{card_id}{demande.id}"' in html
    assert_masked(html)
    html = client.get(path, query_string={"region": "SECRET_CITY"}).get_data(as_text=True)
    assert f'id="{card_id}{demande.id}"' not in html


@pytest.mark.parametrize("action", ["send_matched", "send"])
def test_preview_counter_counts_successful_resends_not_duplicate_shows(
    app, client, offer_setup, monkeypatch, action,
):
    from models import db
    from models.models import Show
    user, admin, show, demande, _ = offer_setup
    duplicate = Show(
        title="Second show", user=user, approved=True, category="Clown",
        contact_email=user.email,
    )
    db.session.add(duplicate)
    db.session.commit()
    monkeypatch.setattr(app, "mail", FakeMail())
    login(client, admin)
    data = {
        "action": action, "categories": ["Clown"],
        "matched_show_ids": [str(show.id), str(duplicate.id)],
        "emails[]": [user.email],
    }
    for count in (1, 2):
        client.post(f"/admin/envoyer-demande/{demande.id}", data=data)
        assert user.apercus_envoyes_count == count
        assert user.cadeaux_offerts_count == 0
    assert len([m for m in app.mail.messages if m.recipients == [user.email]]) == 2


@pytest.mark.parametrize("action", ["send_matched", "send"])
def test_recap_mixed_modes_uses_only_successful_recipients(
    app, client, offer_setup, monkeypatch, action,
):
    from models import db
    from models.models import User, Show
    user, admin, show, demande, _ = offer_setup
    users = []
    shows = [show]
    for name in ("gift", "legacy", "failed"):
        recipient = User(
            username=name, email=f"{name}@example.test",
            created_at=datetime(2026, 9, 11 if name == "legacy" else 13),
        )
        recipient.set_password("test-password")
        item = Show(
            title=f"Company {name}", user=recipient, approved=True,
            category="Clown", contact_email=recipient.email,
        )
        db.session.add_all([recipient, item])
        users.append(recipient)
        shows.append(item)
    db.session.commit()
    gift_user, legacy_user, failed_user = users
    mail = FakeMail(fail_recipient=failed_user.email)
    monkeypatch.setattr(app, "mail", mail)
    login(client, admin)
    client.post(f"/admin/envoyer-demande/{demande.id}", data={
        "action": action, "categories": ["Clown"],
        "matched_show_ids": [str(item.id) for item in shows],
        "gift_user_ids": [str(gift_user.id)],
    })
    recap = next(m for m in mail.messages if m.subject.startswith("[ADMIN]"))
    from html import unescape
    from re import sub
    text = " ".join(unescape(sub(r"<[^>]+>", " ", recap.html)).split())
    assert "Aperçus masqués : 1" in text
    assert "Cadeaux : 1" in text
    assert "Envois complets habituels : 1" in text
    assert "Company gift" in text
    assert "Company legacy" in text
    assert "Company failed" not in text
    assert "Simulated SMTP failure" in text
    assert user.apercus_envoyes_count == 1
    assert gift_user.cadeaux_offerts_count == 1
    assert legacy_user.apercus_envoyes_count == 0
    assert failed_user.apercus_envoyes_count == 0
    if action == "send":
        organizer_mail = next(
            m for m in mail.messages if m.recipients == [demande.contact_email]
        )
        assert "Company failed" not in organizer_mail.html


def test_counter_and_grant_roll_back_on_commit_failure(offer_setup, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    from models import db
    from models.models import AppelOffreEnvoi
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup

    def fail():
        raise SQLAlchemyError("Simulated failed commit")

    with monkeypatch.context() as patch:
        patch.setattr(db.session, "commit", fail)
        with pytest.raises(SQLAlchemyError):
            record_offer_delivery(user, demande)
        db.session.rollback()
    assert user.apercus_envoyes_count == 0
    assert AppelOffreEnvoi.query.count() == 0


def test_admin_tables_show_both_counters(app, client, offer_setup, monkeypatch):
    from utils.offres import record_offer_delivery
    user, admin, _, demande, _ = offer_setup
    record_offer_delivery(user, demande)
    record_offer_delivery(user, demande)
    record_offer_delivery(user, demande, gift=True)
    monkeypatch.setattr(app, "mail", FakeMail())
    login(client, admin)
    html = client.get(f"/admin/envoyer-demande/{demande.id}").get_data(as_text=True)
    assert "Aperçus</th>" in html
    assert 'title="Aperçus masqués envoyés avec succès"' in html
    assert '>2</span>' in html
    html = client.post(f"/admin/envoyer-demande/{demande.id}", data={
        "action": "preview", "categories": ["Clown"],
    }).get_data(as_text=True)
    assert "Aperçus : 2" in html
    assert "Cadeaux : 1" in html


def test_preview_counter_migration_preserves_existing_gifts(app, monkeypatch):
    from types import SimpleNamespace
    from sqlalchemy import create_engine, text
    from models import db
    import app as app_module

    engine = create_engine("sqlite:///:memory:")
    try:
        db.metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO users (username, password_hash, cadeaux_offerts_count) "
                "VALUES ('existing-company', 'test-hash', 4)"
            ))
            connection.execute(text("ALTER TABLE users DROP COLUMN apercus_envoyes_count"))
        monkeypatch.setattr(app_module, "db", SimpleNamespace(engine=engine))
        app_module._run_critical_migrations(app)
        app_module._run_critical_migrations(app)
        with engine.connect() as connection:
            assert connection.execute(text(
                "SELECT cadeaux_offerts_count, apercus_envoyes_count FROM users "
                "WHERE username = 'existing-company'"
            )).one() == (4, 0)
    finally:
        engine.dispose()
