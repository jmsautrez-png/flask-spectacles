from datetime import datetime, timedelta

import pytest


def _adhesion(user):
    from models.models import Adhesion

    return Adhesion(
        user=user, nom="Compagnie test", email=user.email,
        telephone="0102030405", statut="pending",
    )


def test_new_subscription_and_existing_subscriber_renewal(db, normal_user):
    from app import _default_adhesion_amount

    adhesion = _adhesion(normal_user)
    db.session.add(adhesion)
    db.session.commit()
    assert _default_adhesion_amount(adhesion) == 49

    normal_user.subscribed_until = datetime(2026, 12, 1)
    db.session.commit()
    assert _default_adhesion_amount(adhesion) == 99


def test_previous_invoice_sets_renewal_price_without_changing_history(db, normal_user):
    from app import _default_adhesion_amount

    previous = _adhesion(normal_user)
    previous.invoice_number = "2026-OLD"
    previous.invoice_amount = 49
    current = _adhesion(normal_user)
    db.session.add_all([previous, current])
    db.session.commit()

    assert _default_adhesion_amount(current) == 99
    db.session.refresh(previous)
    assert previous.invoice_amount == 49


def test_upgrade_preview_requires_admin_amount_and_preserves_current_expiry(
    client, admin_user, normal_user, monkeypatch,
):
    import app as app_module
    from models import db
    from models.models import Show

    expiry = datetime.utcnow() + timedelta(days=120)
    normal_user.is_subscribed = True
    normal_user.formule_abonnement = "49"
    normal_user.subscribed_until = expiry
    normal_user.renewal_j30_sent_for = expiry
    previous = _adhesion(normal_user)
    previous.statut = "activated"
    previous.formule_abonnement = "49"
    previous.activated_at = datetime.utcnow()
    request = _adhesion(normal_user)
    request.formule_abonnement = "99"
    db.session.add_all([
        previous, request, Show(title="Spectacle validé", user=normal_user, approved=True),
    ])
    db.session.commit()
    with client.session_transaction() as session:
        session["username"] = admin_user.username

    response = client.get(
        f"/admin/adhesions/{request.id}/preview-invoice?formule=99",
        follow_redirects=True,
    )
    assert "saisissez le montant au prorata" in response.get_data(as_text=True)

    response = client.get(
        f"/admin/adhesions/{request.id}/preview-invoice?formule=99&amount=35",
    )
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Passage à la formule avec téléphone" in html
    assert expiry.strftime("%d/%m/%Y") in html
    assert "35 €" in html
    assert "ne prolonge pas" in html
    assert "lien de paiement par carte sera créé" in html

    class Mail:
        def __init__(self):
            self.messages = []

        def send(self, message):
            self.messages.append(message)

    mail = Mail()
    monkeypatch.setattr(client.application, "mail", mail)
    monkeypatch.setitem(client.application.config, "STRIPE_SECRET_KEY", "sk_test_fake")
    calls = []

    class Response:
        def __init__(self, value):
            self.value = value

        def raise_for_status(self):
            pass

        def json(self):
            return self.value

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/prices"):
            return Response({"id": "price_test"})
        return Response({"url": "https://buy.stripe.com/test_upgrade"})

    monkeypatch.setattr(app_module.requests, "post", fake_post)
    client.post(
        f"/admin/adhesions/{request.id}/send-invoice",
        data={"formule": "99", "amount": "35"},
    )
    db.session.refresh(request)
    assert request.invoice_amount == 35
    assert request.is_midterm_upgrade
    assert request.upgrade_until == expiry
    assert normal_user.formule_abonnement == "49"
    assert request.stripe_payment_url == "https://buy.stripe.com/test_upgrade"
    assert len(calls) == 2
    assert calls[0][1]["data"]["unit_amount"] == 3500
    assert calls[1][1]["data"]["restrictions[completed_sessions][limit]"] == 1
    assert "https://buy.stripe.com/test_upgrade" in mail.messages[0].html
    assert "Payer 35 € par carte" in mail.messages[0].html
    client.post(
        f"/admin/adhesions/{request.id}/send-invoice",
        data={"formule": "99", "amount": "35"},
    )
    assert len(calls) == 2
    response = client.post(
        f"/admin/adhesions/{request.id}/send-invoice",
        data={"formule": "99", "amount": "40"},
        follow_redirects=True,
    )
    assert "montant de cette facture de changement est figé" in response.get_data(as_text=True)
    assert request.invoice_amount == 35

    from utils.offres import telephone_visible

    assert not telephone_visible(normal_user)

    client.post(
        f"/admin/adhesions/{request.id}/statut",
        data={"statut": "activated", "formule": "99"},
    )
    db.session.refresh(normal_user)
    assert normal_user.formule_abonnement == "99"
    assert normal_user.subscribed_until == expiry
    assert normal_user.renewal_j30_sent_for == expiry

    assert telephone_visible(normal_user)


def test_upgrade_missing_stripe_key_does_not_send_invoice(
    client, admin_user, normal_user, monkeypatch,
):
    from models import db

    normal_user.is_subscribed = True
    normal_user.formule_abonnement = "49"
    normal_user.subscribed_until = datetime.utcnow() + timedelta(days=120)
    adhesion = _adhesion(normal_user)
    adhesion.formule_abonnement = "99"
    db.session.add(adhesion)
    db.session.commit()
    monkeypatch.setitem(client.application.config, "STRIPE_SECRET_KEY", "")
    with client.session_transaction() as session:
        session["username"] = admin_user.username
    response = client.post(
        f"/admin/adhesions/{adhesion.id}/send-invoice",
        data={"formule": "99", "amount": "35"},
        follow_redirects=True,
    )
    assert "clé Stripe n&#39;est pas configurée" in response.get_data(as_text=True)
    db.session.refresh(adhesion)
    assert adhesion.invoice_sent_at is None
    assert adhesion.stripe_payment_url is None
    assert normal_user.formule_abonnement == "49"


def test_upgrade_stripe_failure_can_be_retried_without_changing_request(
    client, admin_user, normal_user, monkeypatch,
):
    import app as app_module
    from models import db

    normal_user.is_subscribed = True
    normal_user.formule_abonnement = "49"
    normal_user.subscribed_until = datetime.utcnow() + timedelta(days=120)
    adhesion = _adhesion(normal_user)
    adhesion.formule_abonnement = "99"
    db.session.add(adhesion)
    db.session.commit()
    monkeypatch.setitem(client.application.config, "STRIPE_SECRET_KEY", "sk_test_fake")
    messages = []
    monkeypatch.setattr(client.application.mail, "send", messages.append)
    keys = []

    def failed_post(url, **kwargs):
        keys.append(kwargs["headers"]["Idempotency-Key"])
        raise app_module.requests.Timeout("Stripe unavailable")

    monkeypatch.setattr(app_module.requests, "post", failed_post)
    with client.session_transaction() as session:
        session["username"] = admin_user.username
    for _ in range(2):
        response = client.post(
            f"/admin/adhesions/{adhesion.id}/send-invoice",
            data={"formule": "99", "amount": "35"},
            follow_redirects=True,
        )
        assert "Impossible de créer le lien de paiement" in response.get_data(as_text=True)
    db.session.refresh(adhesion)
    assert keys[0] == keys[1]
    assert adhesion.invoice_sent_at is None
    assert adhesion.stripe_payment_url is None
    assert not messages
    assert normal_user.formule_abonnement == "49"


def test_upgrade_at_179_euros_is_one_time_card_payment(app):
    from app import _build_adhesion_invoice_html
    from types import SimpleNamespace

    adh = SimpleNamespace(nom="Test", email="test@example.com", telephone="0102030405", user_id=None)
    now = datetime.utcnow()
    with app.app_context():
        html = _build_adhesion_invoice_html(
            adh, 179, "test", now, now, now + timedelta(days=90), "", "",
            is_midterm_upgrade=True, stripe_payment_url="https://buy.stripe.com/test_upgrade",
        )
    assert "Payer 179 € par carte" in html
    assert "Souscrire à l'abonnement" not in html


def test_invoice_preview_keeps_issued_amount(client, admin_user, normal_user):
    from models import db

    adhesion = _adhesion(normal_user)
    adhesion.invoice_number = "2026-OLD"
    adhesion.invoice_amount = 49
    db.session.add(adhesion)
    db.session.commit()
    with client.session_transaction() as session:
        session["username"] = admin_user.username

    response = client.get(f"/admin/adhesions/{adhesion.id}/preview-invoice")
    assert response.status_code == 200
    assert "/52EUR" in response.get_data(as_text=True)
    db.session.refresh(adhesion)
    assert adhesion.invoice_amount == 49


@pytest.mark.parametrize("kind", ["j30", "j7", "expired"])
def test_renewal_emails_virement_99_paypal_104(app, normal_user, kind):
    import rappels_abonnements as reminders

    html = getattr(reminders, f"_html_rappel_{kind}")(
        normal_user, datetime(2026, 12, 1),
    )
    assert "99 €" in html
    assert "/104EUR" in html
    assert "/99EUR" not in html
    assert "/149EUR" not in html


def test_copie_relance_envoyee_a_l_admin(app, normal_user, monkeypatch):
    import rappels_abonnements as reminders

    envois = []
    monkeypatch.setattr(reminders, "_send_mail",
                        lambda dest, sujet, html: envois.append((dest, sujet, html)) or True)
    monkeypatch.setitem(app.config, "MAIL_DEFAULT_SENDER", "admin@test.com")

    reminders._copie_admin("Relance J-7 abonnement AO", normal_user, datetime(2026, 12, 1))

    assert len(envois) == 1
    dest, sujet, html = envois[0]
    assert dest == "admin@test.com"
    assert sujet == "[Copie relance] Relance J-7 abonnement AO"
    assert normal_user.email in html
    assert "01/12/2026" in html


@pytest.mark.parametrize("path", ["/adhesion", "/cgu", "/abonnement-compagnie/appels-offres"])
def test_public_subscription_prices(client, admin_user, path):
    if path == "/adhesion":
        with client.session_transaction() as session:
            session["username"] = admin_user.username
    response = client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "49 €" in html
    assert "99 €" in html
    assert "79 € TTC" not in html.replace("179 € TTC", "")
