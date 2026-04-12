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
