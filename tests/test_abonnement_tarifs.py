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
    from models import db
    from models.models import Adhesion, Show

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

    monkeypatch.setattr(client.application, "mail", None, raising=False)
    client.post(
        f"/admin/adhesions/{request.id}/send-invoice",
        data={"formule": "99", "amount": "35"},
    )
    db.session.refresh(request)
    assert request.invoice_amount == 35
    assert request.is_midterm_upgrade
    assert request.upgrade_until == expiry
    assert normal_user.formule_abonnement == "49"

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
