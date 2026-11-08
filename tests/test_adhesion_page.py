from datetime import datetime


def login(client, user):
    with client.session_transaction() as session:
        session["username"] = user.username


def approved_show(db, user):
    from models.models import Show

    show = Show(title="Spectacle validé", user=user, approved=True)
    db.session.add(show)
    db.session.commit()


def make_adhesion(db, user, statut, created_at=None, invoice_sent_at=None):
    from models.models import Adhesion

    adh = Adhesion(
        user=user, nom="Test", email=user.email, telephone="0102030405", statut=statut,
        invoice_sent_at=invoice_sent_at,
    )
    if created_at:
        adh.created_at = created_at
    db.session.add(adh)
    db.session.commit()
    return adh.id


def test_form_shown_without_pending_request(client, normal_user):
    from models import db

    approved_show(db, normal_user)
    login(client, normal_user)
    page = client.get("/adhesion").get_data(as_text=True)
    assert 'name="telephone"' in page
    assert "Votre demande est bien reçue" not in page


def test_pending_request_without_invoice_shows_form_and_no_payment(client, normal_user):
    from models import db

    approved_show(db, normal_user)
    make_adhesion(db, normal_user, "pending", created_at=datetime(2026, 11, 5))
    login(client, normal_user)
    page = client.get("/adhesion").get_data(as_text=True)
    assert "Votre demande est bien reçue" in page
    assert "Demande du 05/11/2026" in page
    assert "L'administrateur vous enverra la facture" in page
    assert 'name="telephone"' in page
    assert "Payer 52 € avec PayPal" not in page
    assert "paypal.me/SpectaclementVotre/52EUR" not in page


def test_invoiced_request_hides_form_and_points_to_email(client, normal_user):
    from models import db

    approved_show(db, normal_user)
    make_adhesion(
        db, normal_user, "pending",
        created_at=datetime(2026, 11, 5), invoice_sent_at=datetime(2026, 11, 6),
    )
    login(client, normal_user)
    page = client.get("/adhesion").get_data(as_text=True)
    assert "Votre facture vous a été envoyée par email le 06/11/2026" in page
    assert 'name="telephone"' not in page
    assert "paypal.me/SpectaclementVotre" not in page
    assert "Payer 49 € par carte" not in page


def test_contacted_request_also_blocks_new_request(client, normal_user):
    from models import db
    from models.models import Adhesion

    approved_show(db, normal_user)
    make_adhesion(db, normal_user, "contacted")
    login(client, normal_user)
    response = client.post("/adhesion", data={
        "nom": "Nouveau", "telephone": "0600000000", "email": "a@b.fr",
    })
    assert response.status_code == 302
    assert Adhesion.query.filter_by(user_id=normal_user.id).count() == 1


def test_pending_request_prevents_duplicate_on_post(client, normal_user):
    from models import db
    from models.models import Adhesion

    approved_show(db, normal_user)
    make_adhesion(db, normal_user, "pending")
    login(client, normal_user)
    response = client.post("/adhesion", data={
        "nom": "Doublon", "telephone": "0600000000", "email": "a@b.fr",
    }, follow_redirects=True)
    assert "Vous avez déjà une demande" in response.get_data(as_text=True)
    assert Adhesion.query.filter_by(user_id=normal_user.id).count() == 1


def test_renewal_invoiced_request_has_no_payment_buttons(client, normal_user):
    from models import db

    approved_show(db, normal_user)
    make_adhesion(db, normal_user, "activated")
    make_adhesion(db, normal_user, "pending", invoice_sent_at=datetime(2026, 11, 6))
    login(client, normal_user)
    page = client.get("/adhesion").get_data(as_text=True)
    assert "Votre facture vous a été envoyée par email" in page
    assert "paypal.me/SpectaclementVotre" not in page
    assert "104" not in page


def test_invoice_paypal_amount_follows_renewal(client, normal_user):
    from app import _build_adhesion_invoice_html
    from models import db
    from models.models import Adhesion

    approved_show(db, normal_user)
    premiere_id = make_adhesion(db, normal_user, "pending")
    adh_premiere = db.session.get(Adhesion, premiere_id)
    html_premiere = _build_adhesion_invoice_html(
        adh_premiere, 49, "2026-11-0002", datetime(2026, 11, 7), datetime(2026, 11, 7), datetime(2027, 11, 7), "", "",
    )
    assert "paypal.me/SpectaclementVotre/52EUR" in html_premiere
    assert "49 € + 3 € de frais PayPal" in html_premiere

    make_adhesion(db, normal_user, "activated")
    pending_id = make_adhesion(db, normal_user, "pending")
    adh = db.session.get(Adhesion, pending_id)
    html_renouv = _build_adhesion_invoice_html(
        adh, 99, "2026-11-0001", datetime(2026, 11, 7), datetime(2026, 11, 7), datetime(2027, 11, 7), "", "",
    )
    assert "paypal.me/SpectaclementVotre/104EUR" in html_renouv
    assert "99 € + 5 € de frais PayPal" in html_renouv


def test_rejected_request_does_not_block_new_request(client, normal_user):
    from models import db
    from models.models import Adhesion

    approved_show(db, normal_user)
    make_adhesion(db, normal_user, "rejected")
    login(client, normal_user)
    page = client.get("/adhesion").get_data(as_text=True)
    assert 'name="telephone"' in page
    client.post("/adhesion", data={
        "nom": "Nouveau", "telephone": "0600000000", "email": "a@b.fr", "formule": "49",
    })
    assert Adhesion.query.filter_by(user_id=normal_user.id, statut="pending").count() == 1


def test_adhesion_request_without_formule_is_refused(client, normal_user):
    from models import db
    from models.models import Adhesion

    approved_show(db, normal_user)
    login(client, normal_user)
    response = client.post("/adhesion", data={
        "nom": "Sans formule", "telephone": "0600000000", "email": "a@b.fr",
    })
    assert response.status_code == 200
    assert "choisir une formule" in response.get_data(as_text=True)
    assert Adhesion.query.filter_by(user_id=normal_user.id).count() == 0


def test_adhesion_request_saves_chosen_formule(client, normal_user):
    from models import db
    from models.models import Adhesion

    approved_show(db, normal_user)
    login(client, normal_user)
    client.post("/adhesion", data={
        "nom": "Avec téléphone", "telephone": "0600000000", "email": "a@b.fr", "formule": "99",
    })
    adh = Adhesion.query.filter_by(user_id=normal_user.id).one()
    assert adh.formule_abonnement == "99"
