"""Tests for database models: User, Show, DemandeAnimation, VisitorLog."""
import pytest


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app, db):
        from models.models import User
        with app.app_context():
            user = User(username="alice", email="alice@test.com")
            user.set_password("secret123")
            db.session.add(user)
            db.session.commit()
            assert user.id is not None
            assert user.username == "alice"

    def test_password_hashing(self, app, db):
        from models.models import User
        with app.app_context():
            user = User(username="bob")
            user.set_password("mypassword")
            assert user.password_hash != "mypassword"
            assert user.check_password("mypassword") is True
            assert user.check_password("wrongpassword") is False

    def test_unique_username(self, app, db):
        from models.models import User
        from sqlalchemy.exc import IntegrityError
        with app.app_context():
            u1 = User(username="dupuser")
            u1.set_password("pass1")
            db.session.add(u1)
            db.session.commit()

            u2 = User(username="dupuser")
            u2.set_password("pass2")
            db.session.add(u2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_default_fields(self, app, db):
        from models.models import User
        with app.app_context():
            user = User(username="defaults")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()
            assert user.is_admin is False
            assert user.is_subscribed is False


class TestShowModel:
    """Tests for the Show model."""

    def test_create_show(self, app, db):
        from models.models import User, Show
        with app.app_context():
            user = User(username="artist")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            show = Show(
                title="Spectacle Magique",
                description="Un super spectacle de magie",
                category="magie",
                region="Île-de-France",
                user_id=user.id,
            )
            db.session.add(show)
            db.session.commit()
            assert show.id is not None
            assert show.title == "Spectacle Magique"

    def test_has_image(self, app, db):
        from models.models import Show
        with app.app_context():
            show = Show(title="Test", file_name="photo.webp", file_mimetype="image/webp")
            db.session.add(show)
            db.session.commit()
            assert show.has_image() is True

    def test_no_image(self, app, db):
        from models.models import Show
        with app.app_context():
            show = Show(title="Test Sans Image")
            db.session.add(show)
            db.session.commit()
            assert show.has_image() is False

    def test_is_pdf(self, app, db):
        from models.models import Show
        with app.app_context():
            show = Show(title="PDF", file_name="doc.pdf", file_mimetype="application/pdf")
            db.session.add(show)
            db.session.commit()
            assert show.is_pdf() is True

    def test_image_count(self, app, db):
        from models.models import Show
        with app.app_context():
            show = Show(
                title="Multi",
                file_name="a.webp", file_mimetype="image/webp",
                file_name2="b.webp", file_mimetype2="image/webp",
            )
            db.session.add(show)
            db.session.commit()
            assert show.image_count() == 2

    def test_approved_default_false(self, app, db):
        from models.models import Show
        with app.app_context():
            show = Show(title="Pending")
            db.session.add(show)
            db.session.commit()
            assert show.approved is False


class TestDemandeAnimation:
    """Tests for the DemandeAnimation model."""

    def test_create_demande(self, app, db):
        from models.models import DemandeAnimation
        with app.app_context():
            d = DemandeAnimation(
                structure="Mairie de Test",
                nom="Jean Dupont",
                telephone="0612345678",
                contact_email="jean@test.fr",
                lieu_ville="Paris",
                code_postal="75001",
                region="Île-de-France",
                dates_horaires="15/12 14h-16h",
                genre_recherche="Magie et Magicien",
                age_range="enfant",
                jauge="100",
                budget="1000-1500€",
                type_espace="Salle intérieur",
            )
            db.session.add(d)
            db.session.commit()
            assert d.id is not None
            assert d.structure == "Mairie de Test"


class TestVisitorStatsSummary:
    """Résumé quotidien des visites (visitor_daily_stat) et page /admin/statistiques."""

    @staticmethod
    def _log(db, jours_avant, page="/accueil", bot=False, session="s1"):
        from models.models import VisitorLog
        from datetime import datetime, timedelta
        db.session.add(VisitorLog(
            visited_at=datetime.utcnow() - timedelta(days=jours_avant),
            page_url=page, session_id=session, is_bot=bot, user_agent="Mozilla/5.0 Chrome",
        ))

    def test_resumer_jours_manquants_idempotent(self, app, db):
        from clean_visitor_logs import resumer_jours_manquants
        from models.models import VisitorDailyStat
        from datetime import datetime
        from sqlalchemy import func
        with app.app_context():
            self._log(db, 2, page="/a", session="s1")
            self._log(db, 2, page="/a", session="s2")
            self._log(db, 1, page="/b", bot=True, session="bot")
            db.session.commit()

            assert resumer_jours_manquants(datetime.utcnow()) == 2
            hits = db.session.query(func.sum(VisitorDailyStat.hits)).filter(
                VisitorDailyStat.kind == "page", VisitorDailyStat.key == "/a"
            ).scalar()
            assert hits == 2
            assert db.session.query(VisitorDailyStat).filter(
                VisitorDailyStat.kind == "page", VisitorDailyStat.key == "/b"
            ).count() == 0
            assert resumer_jours_manquants(datetime.utcnow()) == 0

    def test_statistiques_90_jours_avec_logs_bruts_supprimes(self, admin_client, app, db):
        from clean_visitor_logs import resumer_jours_manquants
        from models.models import VisitorLog
        from datetime import datetime
        with app.app_context():
            self._log(db, 40, page="/ancien", session="s1")
            self._log(db, 3, page="/recent", session="s2")
            self._log(db, 0, page="/aujourdhui", session="s3")
            db.session.commit()
            resumer_jours_manquants(datetime.utcnow())
            # Les jours résumés ne doivent plus dépendre des logs bruts
            midi_aujourdhui = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            VisitorLog.query.filter(VisitorLog.visited_at < midi_aujourdhui).delete(synchronize_session=False)
            db.session.commit()

        resp = admin_client.get("/admin/statistiques?period=90")
        assert resp.status_code == 200
        assert "pas pu être calculées".encode() not in resp.data
        for page in (b"/ancien", b"/recent", b"/aujourdhui"):
            assert page in resp.data

    def test_purge_garde_90_jours(self, app, db, monkeypatch):
        import clean_visitor_logs
        from models.models import VisitorLog, VisitorDailyStat
        monkeypatch.setattr(clean_visitor_logs, "app", app)
        with app.app_context():
            self._log(db, 100, page="/tres-ancien", session="s1")
            self._log(db, 10, page="/recent", session="s2")
            db.session.commit()

            clean_visitor_logs.clean_old_visitor_logs(90)

            pages = {row.page_url for row in VisitorLog.query.all()}
            assert pages == {"/recent"}
            assert VisitorDailyStat.query.filter(VisitorDailyStat.key == "/recent").count() == 1

    def test_purge_totaux_annee_precedente_et_comptes_90_jours(self, app, db, monkeypatch):
        import clean_visitor_logs
        from models.models import VisitorDailyStat
        from datetime import date, datetime, timedelta
        monkeypatch.setattr(clean_visitor_logs, "app", app)
        maintenant = datetime.utcnow()
        debut = date(maintenant.year - 1, 1, 1)
        with app.app_context():
            db.session.add_all([
                VisitorDailyStat(day=debut - timedelta(days=1), kind="total_human", hits=5, sessions=2),
                VisitorDailyStat(day=debut, kind="total_human", hits=5, sessions=2),
                VisitorDailyStat(day=(maintenant - timedelta(days=100)).date(), kind="user", key="7", hits=3),
                VisitorDailyStat(day=(maintenant - timedelta(days=10)).date(), kind="user", key="7", hits=3),
            ])
            db.session.commit()

            clean_visitor_logs.clean_old_visitor_logs(90)

            assert VisitorDailyStat.query.filter(VisitorDailyStat.day < debut).count() == 0
            assert VisitorDailyStat.query.filter(VisitorDailyStat.day == debut, VisitorDailyStat.kind == "total_human").count() == 1
            assert VisitorDailyStat.query.filter(VisitorDailyStat.kind == "user", VisitorDailyStat.day == (maintenant - timedelta(days=100)).date()).count() == 0
            assert VisitorDailyStat.query.filter(VisitorDailyStat.kind == "user", VisitorDailyStat.day == (maintenant - timedelta(days=10)).date()).count() == 1

    def test_vue_annee_separe_les_annees(self, admin_client, app, db):
        from models.models import VisitorDailyStat
        from datetime import date, datetime
        annee = datetime.utcnow().year
        with app.app_context():
            db.session.add_all([
                VisitorDailyStat(day=date(annee - 1, 1, 1), kind="total_human", hits=1, sessions=1),
                VisitorDailyStat(day=date(annee - 1, 6, 1), kind="page", key="/page-annee-precedente", hits=1),
                VisitorDailyStat(day=date(annee, 1, 1), kind="total_human", hits=1, sessions=1),
                VisitorDailyStat(day=date(annee, 1, 1), kind="page", key="/page-annee-courante", hits=1),
            ])
            db.session.commit()

        resp = admin_client.get(f"/admin/statistiques?period=year&year={annee}")
        assert resp.status_code == 200
        assert b"/page-annee-courante" in resp.data
        assert b"/page-annee-precedente" not in resp.data

        resp = admin_client.get(f"/admin/statistiques?period=year&year={annee - 1}")
        assert resp.status_code == 200
        assert b"/page-annee-precedente" in resp.data
        assert b"/page-annee-courante" not in resp.data
