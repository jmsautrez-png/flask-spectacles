from datetime import datetime

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
    assert "79 € TTC" not in html
