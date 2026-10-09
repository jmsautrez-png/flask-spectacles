"""Anonymous per-session consultation totals, visible only to admins."""

from tests.test_offre_delivery import offer_setup, login


def test_lists_do_not_count_but_openings_count_once_across_surfaces(client, offer_setup):
    from models import db
    user, _, _, demande, other = offer_setup
    login(client, user)
    for path in ("/demandes-animation", "/mes-appels-offres"):
        html = client.get(path).get_data(as_text=True)
        assert "data-offer-consultation=" in html
        assert "X-CSRFToken" in html
        assert "Consultations :" not in html
    db.session.refresh(demande)
    assert demande.consultations_count == 0
    url = f"/appels-offres/{demande.id}/consultation"
    assert client.post(url).status_code == 204
    assert client.post(url).status_code == 204
    assert client.get(f"/appels-offres/{demande.id}").status_code == 200
    db.session.refresh(demande)
    assert demande.consultations_count == 1
    client.get(f"/appels-offres/{other.id}")
    db.session.refresh(other)
    assert other.consultations_count == 1


def test_anonymous_sessions_count_separately_without_user_identity(app, client, offer_setup):
    from models import db
    from models.models import AppelOffreConsultation
    _, _, _, demande, _ = offer_setup
    url = f"/appels-offres/{demande.id}/consultation"
    assert client.post(url).status_code == 204
    with app.test_client() as second:
        assert second.post(url).status_code == 204
        assert second.post(url).status_code == 204
    db.session.refresh(demande)
    assert demande.consultations_count == 2
    assert AppelOffreConsultation.query.count() == 2
    assert {c.name for c in AppelOffreConsultation.__table__.columns} == {
        "id", "demande_id", "session_key",
    }


def test_admin_visits_are_excluded_and_counter_shown_only_in_admin(client, offer_setup):
    from models import db
    user, admin, _, demande, _ = offer_setup
    login(client, user)
    client.get(f"/appels-offres/{demande.id}")
    login(client, admin)
    client.get(f"/appels-offres/{demande.id}")
    assert client.post(f"/appels-offres/{demande.id}/consultation").status_code == 204
    db.session.refresh(demande)
    assert demande.consultations_count == 1
    assert "Consultations :</strong> 1" in client.get(
        "/admin/demandes-animation",
    ).get_data(as_text=True)
    assert "Consultations :</strong> 1" in client.get(
        f"/admin/envoyer-demande/{demande.id}",
    ).get_data(as_text=True)
    from utils.offres import offer_view
    assert not hasattr(offer_view(demande, user, set()), "consultations_count")


def test_refused_access_does_not_count(client, offer_setup):
    from models import db
    user, _, _, demande, _ = offer_setup
    demande.is_private = True
    db.session.commit()
    assert client.post(f"/appels-offres/{demande.id}/consultation").status_code == 404
    login(client, user)
    assert client.get(f"/appels-offres/{demande.id}").status_code == 404
    demande.is_private = False
    demande.approved = False
    db.session.commit()
    assert client.post(f"/appels-offres/{demande.id}/consultation").status_code == 404
    demande.approved = True
    user.bloque_appels_offres = True
    db.session.commit()
    assert client.post(f"/appels-offres/{demande.id}/consultation").status_code == 403
    assert client.get(f"/appels-offres/{demande.id}").status_code == 302
    db.session.refresh(demande)
    assert demande.consultations_count == 0


def test_private_gift_direct_consultation_counts(client, offer_setup):
    from models import db
    from utils.offres import record_offer_delivery
    user, _, _, demande, _ = offer_setup
    demande.is_private = True
    db.session.commit()
    record_offer_delivery(user, demande, gift=True)
    login(client, user)
    client.get(f"/appels-offres/{demande.id}")
    db.session.refresh(demande)
    assert demande.consultations_count == 1


def test_count_endpoint_requires_csrf(app, client, offer_setup, monkeypatch):
    _, _, _, demande, _ = offer_setup
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    assert client.post(f"/appels-offres/{demande.id}/consultation").status_code == 302
    assert demande.consultations_count == 0


def test_failed_counter_returns_error_and_logs(app, client, offer_setup, monkeypatch, caplog):
    from sqlalchemy.exc import SQLAlchemyError
    from utils import offres
    _, _, _, demande, _ = offer_setup

    def fail(*args):
        raise SQLAlchemyError("Simulated counter failure")

    monkeypatch.setattr(offres, "record_offer_consultation", fail)
    response = client.post(f"/appels-offres/{demande.id}/consultation")
    assert response.status_code == 503
    assert "non enregistrée" in caplog.text
    assert demande.consultations_count == 0


def test_deleted_offer_removes_session_deduplication(client, offer_setup):
    from models import db
    from models.models import AppelOffreConsultation
    _, _, _, demande, _ = offer_setup
    client.post(f"/appels-offres/{demande.id}/consultation")
    assert AppelOffreConsultation.query.count() == 1
    db.session.delete(demande)
    db.session.commit()
    assert AppelOffreConsultation.query.count() == 0


def test_counter_migration_starts_at_zero_and_preserves_offer(app, monkeypatch):
    from types import SimpleNamespace
    from sqlalchemy import create_engine, text
    from models import db
    import app as app_module

    engine = create_engine("sqlite:///:memory:")
    try:
        db.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO demande_animation "
                "(structure,telephone,lieu_ville,nom,dates_horaires,type_espace,"
                "genre_recherche,age_range,jauge,budget,contact_email) VALUES "
                "('original','phone','city','name','date','space','genre','age','100','1000','mail')"
            ))
            conn.execute(text("ALTER TABLE demande_animation DROP COLUMN consultations_count"))
        monkeypatch.setattr(app_module, "db", SimpleNamespace(engine=engine))
        app_module._run_critical_migrations(app)
        app_module._run_critical_migrations(app)
        with engine.connect() as conn:
            assert conn.execute(text(
                "SELECT structure, consultations_count FROM demande_animation"
            )).one() == ("original", 0)
    finally:
        engine.dispose()
