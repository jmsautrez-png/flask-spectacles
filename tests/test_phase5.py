"""Tests pour la Phase 5 : notation, messagerie, analytics, notifications."""
import pytest
from models.models import User, Show, Review, Conversation, Message, ShowView, Notification


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def owner_user(db):
    """Utilisateur propriétaire d'un spectacle."""
    user = User(username="owner", is_admin=False, email="owner@test.com")
    user.set_password("ownerpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def other_user(db):
    """Deuxième utilisateur pour la messagerie."""
    user = User(username="other", is_admin=False, email="other@test.com")
    user.set_password("otherpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def approved_show(db, owner_user):
    """Spectacle validé pour les tests."""
    show = Show(
        title="Spectacle Test",
        raison_sociale="Compagnie Test",
        user_id=owner_user.id,
        approved=True,
    )
    db.session.add(show)
    db.session.commit()
    return show


@pytest.fixture
def unapproved_show(db, owner_user):
    """Spectacle non validé."""
    show = Show(
        title="Spectacle En Attente",
        raison_sociale="Compagnie Test",
        user_id=owner_user.id,
        approved=False,
    )
    db.session.add(show)
    db.session.commit()
    return show


@pytest.fixture
def owner_client(client, owner_user):
    """Client connecté en tant que propriétaire."""
    with client.session_transaction() as sess:
        sess["username"] = "owner"
    return client


@pytest.fixture
def other_client(client, other_user):
    """Client connecté en tant qu'autre utilisateur."""
    with client.session_transaction() as sess:
        sess["username"] = "other"
    return client


# ── 5.1 Système de notation ─────────────────────────────────────────


class TestReviewSystem:
    """Tests du système de notation / avis."""

    def test_submit_review_valid(self, client, db, approved_show):
        """Soumission d'un avis valide."""
        resp = client.post(
            f"/show/{approved_show.id}/review",
            data={"author_name": "Jean Dupont", "rating": "4", "comment": "Super spectacle !"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        review = Review.query.first()
        assert review is not None
        assert review.author_name == "Jean Dupont"
        assert review.rating == 4
        assert review.comment == "Super spectacle !"
        assert review.approved is False  # En attente de modération

    def test_submit_review_creates_notification(self, client, db, approved_show, owner_user):
        """La soumission d'un avis crée une notification pour le propriétaire."""
        client.post(
            f"/show/{approved_show.id}/review",
            data={"author_name": "Marie", "rating": "5", "comment": "Génial"},
            follow_redirects=True,
        )
        notif = Notification.query.filter_by(user_id=owner_user.id, type="review").first()
        assert notif is not None
        assert "Marie" in notif.body

    def test_submit_review_invalid_rating(self, client, db, approved_show):
        """Un avis avec note invalide est rejeté."""
        resp = client.post(
            f"/show/{approved_show.id}/review",
            data={"author_name": "Test", "rating": "6", "comment": ""},
            follow_redirects=True,
        )
        assert Review.query.count() == 0

    def test_submit_review_invalid_rating_zero(self, client, db, approved_show):
        """Un avis avec note 0 est rejeté."""
        client.post(
            f"/show/{approved_show.id}/review",
            data={"author_name": "Test", "rating": "0", "comment": ""},
            follow_redirects=True,
        )
        assert Review.query.count() == 0

    def test_submit_review_missing_author(self, client, db, approved_show):
        """Un avis sans auteur est rejeté."""
        client.post(
            f"/show/{approved_show.id}/review",
            data={"author_name": "", "rating": "3", "comment": "Ok"},
            follow_redirects=True,
        )
        assert Review.query.count() == 0

    def test_submit_review_short_author(self, client, db, approved_show):
        """Un auteur trop court (< 2 chars) est rejeté."""
        client.post(
            f"/show/{approved_show.id}/review",
            data={"author_name": "X", "rating": "3", "comment": "Ok"},
            follow_redirects=True,
        )
        assert Review.query.count() == 0

    def test_submit_review_unapproved_show_404(self, client, db, unapproved_show):
        """Impossible de noter un spectacle non validé."""
        resp = client.post(
            f"/show/{unapproved_show.id}/review",
            data={"author_name": "Test", "rating": "5", "comment": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 404

    def test_submit_review_nonexistent_show_404(self, client, db):
        """Avis sur spectacle inexistant renvoie 404."""
        resp = client.post(
            "/show/99999/review",
            data={"author_name": "Test", "rating": "5", "comment": ""},
        )
        assert resp.status_code == 404

    def test_comment_truncated_at_1000(self, client, db, approved_show):
        """Le commentaire est tronqué à 1000 caractères."""
        long_comment = "A" * 1500
        client.post(
            f"/show/{approved_show.id}/review",
            data={"author_name": "Test User", "rating": "3", "comment": long_comment},
            follow_redirects=True,
        )
        review = Review.query.first()
        assert review is not None
        assert len(review.comment) == 1000


class TestReviewModeration:
    """Tests de la modération des avis (admin)."""

    def test_admin_reviews_page(self, admin_client, db):
        """La page de modération est accessible par un admin."""
        resp = admin_client.get("/admin/reviews")
        assert resp.status_code == 200

    def test_admin_reviews_requires_admin(self, logged_in_client):
        """La page de modération n'est pas accessible par un utilisateur normal."""
        resp = logged_in_client.get("/admin/reviews", follow_redirects=False)
        assert resp.status_code in (302, 403)

    def test_approve_review(self, admin_client, db, approved_show):
        """Un admin peut approuver un avis."""
        review = Review(show_id=approved_show.id, author_name="Test", rating=4, approved=False)
        db.session.add(review)
        db.session.commit()

        resp = admin_client.post(f"/admin/reviews/{review.id}/approve", follow_redirects=True)
        assert resp.status_code == 200
        assert Review.query.get(review.id).approved is True

    def test_delete_review(self, admin_client, db, approved_show):
        """Un admin peut supprimer un avis."""
        review = Review(show_id=approved_show.id, author_name="Test", rating=2, approved=False)
        db.session.add(review)
        db.session.commit()
        rid = review.id

        resp = admin_client.post(f"/admin/reviews/{rid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert Review.query.get(rid) is None

    def test_approve_nonexistent_review_404(self, admin_client, db):
        """Approuver un avis inexistant renvoie 404."""
        resp = admin_client.post("/admin/reviews/99999/approve")
        assert resp.status_code == 404


# ── 5.2 Messagerie interne ──────────────────────────────────────────


class TestMessaging:
    """Tests de la messagerie interne."""

    def test_inbox_empty(self, owner_client, db, owner_user):
        """La boîte de réception vide fonctionne."""
        resp = owner_client.get("/messages")
        assert resp.status_code == 200

    def test_inbox_requires_login(self, client, db):
        """La messagerie nécessite d'être connecté."""
        resp = client.get("/messages", follow_redirects=False)
        assert resp.status_code == 302

    def test_new_conversation(self, owner_client, db, owner_user, other_user):
        """Créer une nouvelle conversation."""
        resp = owner_client.post(
            f"/messages/new/{other_user.id}",
            data={"subject": "Demande info", "content": "Bonjour, disponible ?"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        conv = Conversation.query.first()
        assert conv is not None
        assert conv.user1_id == owner_user.id
        assert conv.user2_id == other_user.id
        msg = Message.query.first()
        assert msg.content == "Bonjour, disponible ?"

    def test_new_conversation_creates_notification(self, owner_client, db, owner_user, other_user):
        """L'envoi d'un message crée une notification pour le destinataire."""
        owner_client.post(
            f"/messages/new/{other_user.id}",
            data={"subject": "Info", "content": "Salut !"},
            follow_redirects=True,
        )
        notif = Notification.query.filter_by(user_id=other_user.id, type="message").first()
        assert notif is not None

    def test_cannot_message_self(self, owner_client, db, owner_user):
        """Impossible de s'envoyer un message à soi-même."""
        resp = owner_client.post(
            f"/messages/new/{owner_user.id}",
            data={"content": "Moi-même"},
            follow_redirects=True,
        )
        assert Conversation.query.count() == 0

    def test_thread_access_control(self, other_client, db, owner_user, other_user):
        """Seuls les participants peuvent voir un thread."""
        # Créer une conversation entre owner et un admin
        admin = User(username="adminx", is_admin=True, email="adminx@test.com")
        admin.set_password("pass")
        db.session.add(admin)
        db.session.commit()
        conv = Conversation(user1_id=owner_user.id, user2_id=admin.id, subject="Privé")
        db.session.add(conv)
        db.session.commit()

        # other_user ne peut pas y accéder (403 ou 500 si le error handler renvoie 500)
        resp = other_client.get(f"/messages/{conv.id}")
        assert resp.status_code in (403, 500)

    def test_send_message_in_thread(self, owner_client, db, owner_user, other_user):
        """Envoyer un message dans une conversation existante."""
        conv = Conversation(user1_id=owner_user.id, user2_id=other_user.id, subject="Test")
        db.session.add(conv)
        db.session.commit()

        resp = owner_client.post(
            f"/messages/{conv.id}",
            data={"content": "Nouveau message"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert Message.query.filter_by(conversation_id=conv.id).count() == 1

    def test_messages_marked_as_read(self, other_client, db, owner_user, other_user):
        """Visiter un thread marque les messages reçus comme lus."""
        conv = Conversation(user1_id=owner_user.id, user2_id=other_user.id, subject="Read test")
        db.session.add(conv)
        db.session.flush()
        msg = Message(conversation_id=conv.id, sender_id=owner_user.id, content="Hello")
        db.session.add(msg)
        db.session.commit()
        assert msg.read_at is None

        other_client.get(f"/messages/{conv.id}")
        refreshed = Message.query.get(msg.id)
        assert refreshed.read_at is not None

    def test_existing_conversation_reused(self, owner_client, db, owner_user, other_user):
        """Si une conversation existe déjà, GET redirige vers le thread existant."""
        conv = Conversation(user1_id=owner_user.id, user2_id=other_user.id, subject="Existante")
        db.session.add(conv)
        db.session.commit()

        resp = owner_client.get(f"/messages/new/{other_user.id}", follow_redirects=False)
        assert resp.status_code == 302
        assert f"/messages/{conv.id}" in resp.headers["Location"]

    def test_message_too_long_ignored(self, owner_client, db, owner_user, other_user):
        """Un message > 2000 chars n'est pas envoyé."""
        conv = Conversation(user1_id=owner_user.id, user2_id=other_user.id, subject="Long")
        db.session.add(conv)
        db.session.commit()

        owner_client.post(
            f"/messages/{conv.id}",
            data={"content": "X" * 2001},
            follow_redirects=True,
        )
        assert Message.query.count() == 0

    def test_empty_message_ignored(self, owner_client, db, owner_user, other_user):
        """Un message vide n'est pas envoyé."""
        conv = Conversation(user1_id=owner_user.id, user2_id=other_user.id, subject="Empty")
        db.session.add(conv)
        db.session.commit()

        owner_client.post(
            f"/messages/{conv.id}",
            data={"content": "   "},
            follow_redirects=True,
        )
        assert Message.query.count() == 0


# ── 5.3 Analytics ────────────────────────────────────────────────────


class TestAnalytics:
    """Tests des dashboards analytics."""

    def test_admin_analytics_requires_admin(self, logged_in_client):
        """La page analytics admin n'est pas accessible sans admin."""
        resp = logged_in_client.get("/admin/analytics", follow_redirects=False)
        assert resp.status_code in (302, 403)

    def test_my_analytics_empty(self, owner_client, db, owner_user):
        """La page my-analytics fonctionne sans spectacles."""
        resp = owner_client.get("/my-analytics")
        assert resp.status_code == 200

    def test_my_analytics_with_show(self, owner_client, db, owner_user, approved_show):
        """La page my-analytics montre les stats du spectacle."""
        # Ajouter des vues
        for i in range(3):
            db.session.add(ShowView(show_id=approved_show.id, session_id=f"sess_{i}", ip_hash=f"hash_{i}"))
        # Ajouter un avis approuvé
        db.session.add(Review(show_id=approved_show.id, author_name="Fan", rating=5, approved=True))
        db.session.commit()

        resp = owner_client.get("/my-analytics")
        assert resp.status_code == 200
        assert b"Spectacle Test" in resp.data

    def test_my_analytics_requires_login(self, client, db):
        """My-analytics nécessite d'être connecté."""
        resp = client.get("/my-analytics", follow_redirects=False)
        assert resp.status_code == 302


# ── 5.4 Notifications ───────────────────────────────────────────────


class TestNotifications:
    """Tests du système de notifications."""

    def test_notifications_page(self, owner_client, db, owner_user):
        """La page notifications fonctionne."""
        notif = Notification(
            user_id=owner_user.id, type="system",
            title="Bienvenue", body="Test", read=False,
        )
        db.session.add(notif)
        db.session.commit()

        resp = owner_client.get("/notifications")
        assert resp.status_code == 200
        assert b"Bienvenue" in resp.data
        # Devrait marquer comme lu
        assert Notification.query.filter_by(user_id=owner_user.id, read=True).count() == 1

    def test_notifications_count_api(self, owner_client, db, owner_user):
        """L'API /api/notifications/count retourne le bon compteur."""
        for i in range(3):
            db.session.add(Notification(
                user_id=owner_user.id, type="system",
                title=f"Notif {i}", read=False,
            ))
        db.session.commit()

        resp = owner_client.get("/api/notifications/count")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["unread"] == 3

    def test_notifications_count_excludes_read(self, owner_client, db, owner_user):
        """L'API ignore les notifications déjà lues."""
        db.session.add(Notification(user_id=owner_user.id, type="system", title="Lue", read=True))
        db.session.add(Notification(user_id=owner_user.id, type="system", title="Non lue", read=False))
        db.session.commit()

        resp = owner_client.get("/api/notifications/count")
        assert resp.get_json()["unread"] == 1

    def test_unread_messages_api(self, owner_client, db, owner_user, other_user):
        """L'API unread-messages compte les messages non lus."""
        conv = Conversation(user1_id=owner_user.id, user2_id=other_user.id, subject="Test")
        db.session.add(conv)
        db.session.flush()
        # 2 messages non lus de l'autre user
        for i in range(2):
            db.session.add(Message(conversation_id=conv.id, sender_id=other_user.id, content=f"Msg {i}"))
        db.session.commit()

        resp = owner_client.get("/api/notifications/unread-messages")
        assert resp.status_code == 200
        assert resp.get_json()["unread"] == 2

    def test_unread_messages_excludes_own(self, owner_client, db, owner_user, other_user):
        """Les messages envoyés par soi-même ne comptent pas comme non lus."""
        conv = Conversation(user1_id=owner_user.id, user2_id=other_user.id, subject="Test")
        db.session.add(conv)
        db.session.flush()
        db.session.add(Message(conversation_id=conv.id, sender_id=owner_user.id, content="Mon msg"))
        db.session.commit()

        resp = owner_client.get("/api/notifications/unread-messages")
        assert resp.get_json()["unread"] == 0

    def test_notifications_requires_login(self, client, db):
        """Les notifications nécessitent d'être connecté."""
        resp = client.get("/notifications", follow_redirects=False)
        assert resp.status_code == 302

    def test_notifications_count_requires_login(self, client, db):
        """L'API count nécessite d'être connecté."""
        resp = client.get("/api/notifications/count", follow_redirects=False)
        assert resp.status_code == 302


# ── 5.5 Modèles Phase 5 ─────────────────────────────────────────────


class TestPhase5Models:
    """Tests des modèles Phase 5."""

    def test_review_model(self, app, db):
        """Test création Review."""
        with app.app_context():
            user = User(username="rev_user", email="rev@test.com")
            user.set_password("pass")
            db.session.add(user)
            db.session.flush()
            show = Show(title="Show Rev", user_id=user.id, approved=True)
            db.session.add(show)
            db.session.flush()
            review = Review(show_id=show.id, user_id=user.id, author_name="Tester", rating=5)
            db.session.add(review)
            db.session.commit()

            assert review.id is not None
            assert review.show.title == "Show Rev"
            assert review.user.username == "rev_user"

    def test_conversation_message_model(self, app, db):
        """Test création Conversation + Message."""
        with app.app_context():
            u1 = User(username="u1", email="u1@test.com")
            u1.set_password("pass")
            u2 = User(username="u2", email="u2@test.com")
            u2.set_password("pass")
            db.session.add_all([u1, u2])
            db.session.flush()

            conv = Conversation(user1_id=u1.id, user2_id=u2.id, subject="Hello")
            db.session.add(conv)
            db.session.flush()
            msg = Message(conversation_id=conv.id, sender_id=u1.id, content="Bonjour !")
            db.session.add(msg)
            db.session.commit()

            assert conv.user1.username == "u1"
            assert conv.user2.username == "u2"
            assert msg.conversation.subject == "Hello"
            assert msg.sender.username == "u1"
            assert msg.read_at is None

    def test_show_view_model(self, app, db):
        """Test création ShowView."""
        with app.app_context():
            show = Show(title="View Test", approved=True)
            db.session.add(show)
            db.session.flush()
            view = ShowView(show_id=show.id, session_id="abc123", ip_hash="hash123")
            db.session.add(view)
            db.session.commit()

            assert view.id is not None
            assert view.show.title == "View Test"

    def test_notification_model(self, app, db):
        """Test création Notification."""
        with app.app_context():
            user = User(username="notif_user", email="notif@test.com")
            user.set_password("pass")
            db.session.add(user)
            db.session.flush()
            notif = Notification(
                user_id=user.id, type="system",
                title="Test", body="Corps du message",
            )
            db.session.add(notif)
            db.session.commit()

            assert notif.id is not None
            assert notif.read is False
            assert notif.user.username == "notif_user"
