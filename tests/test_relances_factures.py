from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest


NOW = datetime(2026, 10, 20, 12, 0, 0)


def make_adhesion(db, user, **fields):
    from models.models import Adhesion

    adh = Adhesion(
        user=user, nom="Test", email=user.email, telephone="0102030405",
        **fields,
    )
    db.session.add(adh)
    db.session.commit()
    return adh


def _sent_days_ago(days):
    return NOW - timedelta(days=days)


def _facture_html(amount=49):
    from app import _build_adhesion_invoice_html

    adh = SimpleNamespace(
        nom="Test", email="test@example.com", telephone="0102030405", user_id=None,
    )
    return _build_adhesion_invoice_html(
        adh, amount, "2026-10-2027-001", NOW, NOW, NOW.replace(year=2027),
        "jsautrez@yahoo.fr", "https://spectacleanimation.fr/cgu",
    )


def test_invoice_paypal_adds_fee_and_virement_keeps_amount():
    html = _facture_html(49)

    assert "paypal.me/SpectaclementVotre/52EUR" in html
    assert "Payer 52 € avec" in html
    assert "paypal.me/SpectaclementVotre/49EUR" not in html
    assert "<strong>49 €</strong> par virement SEPA" in html
    assert "jusqu'à 48 h" in html
    assert "nous prévenir par e-mail" in html


def test_invoice_stripe_block_only_when_link_set(monkeypatch):
    import app as app_module

    monkeypatch.setitem(app_module.STRIPE_LIENS_PAR_MONTANT, 49, "")
    assert "Payer 49 € par carte" not in _facture_html(49)

    monkeypatch.setitem(app_module.STRIPE_LIENS_PAR_MONTANT, 49, "https://buy.stripe.com/test_49")
    html = _facture_html(49)
    assert 'href="https://buy.stripe.com/test_49"' in html
    assert "Payer 49 € par carte" in html


@pytest.mark.parametrize(
    "fields, expected",
    [
        ({"statut": "pending", "invoice_sent_at": None}, (None, False)),
        ({"statut": "activated", "invoice_sent_at": _sent_days_ago(12)}, (None, False)),
        ({"statut": "rejected", "invoice_sent_at": _sent_days_ago(12)}, (None, False)),
        ({"statut": "contacted", "invoice_sent_at": _sent_days_ago(2)}, (None, False)),
        ({"statut": "contacted", "invoice_sent_at": _sent_days_ago(3)}, ("j3", False)),
        ({"statut": "contacted", "invoice_sent_at": _sent_days_ago(8)}, ("j7", False)),
        ({"statut": "contacted", "invoice_sent_at": _sent_days_ago(8), "relance_j7_sent_for": _sent_days_ago(8)}, (None, False)),
        ({"statut": "contacted", "invoice_sent_at": _sent_days_ago(5), "relance_j3_sent_for": _sent_days_ago(5)}, (None, False)),
        ({"statut": "contacted", "invoice_sent_at": _sent_days_ago(10)}, ("j7", True)),
        ({"statut": "contacted", "invoice_sent_at": _sent_days_ago(11), "alerte_admin_j10_sent_for": _sent_days_ago(11)}, ("j7", False)),
    ],
)
def test_actions_dues(fields, expected):
    from relances_factures import actions_dues

    fields.setdefault("activated_at", None)
    fields.setdefault("rejected_at", None)
    fields.setdefault("relance_j3_sent_for", None)
    fields.setdefault("relance_j7_sent_for", None)
    fields.setdefault("alerte_admin_j10_sent_for", None)
    adh = SimpleNamespace(**fields)

    assert actions_dues(adh, NOW) == expected


def test_renouvellement_paypal_104_virement_99():
    from types import SimpleNamespace
    from rappels_abonnements import (
        _html_rappel_j30, _html_rappel_j7, _html_rappel_expired,
    )

    user = SimpleNamespace(raison_sociale="Mairie Test", username="mairie")
    fin = NOW

    for rendu in (_html_rappel_j30, _html_rappel_j7, _html_rappel_expired):
        html = rendu(user, fin)
        assert "paypal.me/SpectaclementVotre/104EUR" in html
        assert "paypal.me/SpectaclementVotre/99EUR" not in html
        assert "104 €" in html
        assert "99 €" in html
        assert "jusqu'à <strong>48 h</strong>" in html
        assert "nous prévenir" in html


def test_renouvellement_bouton_carte_seulement_si_lien(monkeypatch):
    from types import SimpleNamespace
    import app as app_module
    from rappels_abonnements import _html_rappel_j7

    user = SimpleNamespace(raison_sociale="Mairie Test", username="mairie")

    monkeypatch.setitem(app_module.STRIPE_LIENS_PAR_MONTANT, 99, "")
    assert "Payer 99 € par carte" not in _html_rappel_j7(user, NOW)

    monkeypatch.setitem(app_module.STRIPE_LIENS_PAR_MONTANT, 99, "https://buy.stripe.com/test_99")
    html = _html_rappel_j7(user, NOW)
    assert 'href="https://buy.stripe.com/test_99"' in html
    assert "Payer 99 € par carte" in html


def test_traiter_sends_then_is_idempotent(db, normal_user):
    from relances_factures import traiter
    from models.models import Adhesion

    adh = make_adhesion(
        db, normal_user, statut="contacted", invoice_number="2026-10-2027-001",
        invoice_amount=49, invoice_sent_at=_sent_days_ago(8),
    )
    adh_id = adh.id
    envois = []

    def fake_envoi(to, sujet, html):
        envois.append((to, sujet))
        return True

    stats = traiter(NOW, apply=True, envoyer=fake_envoi, admin_addr="admin@test.com")
    assert stats == {"j3": 0, "j7": 1, "alerte": 0}
    assert envois == [(normal_user.email, "Dernier rappel : facture 2026-10-2027-001 en attente de règlement")]

    adh = db.session.get(Adhesion, adh_id)
    assert adh.relance_j7_sent_for == adh.invoice_sent_at
    assert adh.relance_j3_sent_for == adh.invoice_sent_at

    envois.clear()
    stats = traiter(NOW, apply=True, envoyer=fake_envoi, admin_addr="admin@test.com")
    assert stats == {"j3": 0, "j7": 0, "alerte": 0}
    assert envois == []


def test_traiter_dry_run_changes_nothing(db, normal_user):
    from relances_factures import traiter
    from models.models import Adhesion

    adh = make_adhesion(
        db, normal_user, statut="contacted", invoice_number="2026-10-2027-002",
        invoice_amount=49, invoice_sent_at=_sent_days_ago(11),
    )
    adh_id = adh.id
    envois = []

    stats = traiter(NOW, apply=False, envoyer=lambda *a: envois.append(a) or True, admin_addr="admin@test.com")
    assert stats == {"j3": 0, "j7": 1, "alerte": 1}
    assert envois == []

    adh = db.session.get(Adhesion, adh_id)
    assert adh.relance_j7_sent_for is None
    assert adh.alerte_admin_j10_sent_for is None


def test_traiter_failed_send_is_not_recorded(db, normal_user):
    from relances_factures import traiter
    from models.models import Adhesion

    adh = make_adhesion(
        db, normal_user, statut="contacted", invoice_number="2026-10-2027-003",
        invoice_amount=49, invoice_sent_at=_sent_days_ago(4),
    )
    adh_id = adh.id

    stats = traiter(NOW, apply=True, envoyer=lambda *a: False, admin_addr="admin@test.com")
    assert stats == {"j3": 1, "j7": 0, "alerte": 0}

    adh = db.session.get(Adhesion, adh_id)
    assert adh.relance_j3_sent_for is None
