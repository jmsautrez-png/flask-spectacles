"""Tests for public routes: home, catalogue, show_detail, SEO pages, sitemap."""
import pytest


class TestHomeRoute:
    """Tests for the home page."""

    def test_home_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_contains_brand(self, client):
        resp = client.get("/")
        assert "Spectacle" in resp.data.decode("utf-8")


class TestCatalogueRoute:
    """Tests for the catalogue listing."""

    def test_catalogue_returns_200(self, client):
        resp = client.get("/catalogue")
        assert resp.status_code == 200

    def test_catalogue_with_search(self, client):
        resp = client.get("/catalogue?q=magie")
        assert resp.status_code == 200

    def test_catalogue_with_category_filter(self, client):
        resp = client.get("/catalogue?category=clown")
        assert resp.status_code == 200


class TestSeoPages:
    """Tests for thematic SEO pages."""

    @pytest.mark.parametrize("path", [
        "/spectacles-enfants",
        "/animations-enfants",
        "/spectacles-noel",
        "/animations-entreprises",
        "/marionnettes",
        "/magiciens",
        "/clowns",
        "/animations-anniversaire",
        "/booker-artiste",
    ])
    def test_seo_page_returns_200(self, client, path):
        resp = client.get(path)
        assert resp.status_code == 200


class TestStaticPages:
    """Tests for static/info pages."""

    def test_about_page(self, client):
        resp = client.get("/qui-sommes-nous")
        assert resp.status_code == 200

    def test_legal_page(self, client):
        resp = client.get("/informations-legales")
        assert resp.status_code == 200

    def test_abonnement_page(self, client):
        resp = client.get("/abonnement-compagnie")
        assert resp.status_code == 200


class TestAdhesionEligibility:
    """An approved show is required before an AO subscription can be activated."""

    def test_adhesion_requires_approved_show(self, logged_in_client):
        resp = logged_in_client.get("/adhesion")
        assert resp.status_code == 302

    def test_admin_cannot_activate_without_approved_show(self, db, admin_client, normal_user):
        from models.models import Adhesion

        adhesion = Adhesion(
            user_id=normal_user.id,
            nom="Compagnie test",
            telephone="0600000000",
            email=normal_user.email,
            statut="pending",
        )
        db.session.add(adhesion)
        db.session.commit()

        resp = admin_client.post(
            f"/admin/adhesions/{adhesion.id}/statut",
            data={"statut": "activated"},
        )

        assert resp.status_code == 302
        db.session.refresh(adhesion)
        assert adhesion.statut == "pending"


class TestSitemap:
    """Tests for the XML sitemap."""

    def test_sitemap_returns_xml(self, client):
        resp = client.get("/sitemap.xml")
        assert resp.status_code == 200
        assert b"<?xml" in resp.data or b"<urlset" in resp.data


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_basic(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"

    def test_health_full(self, client):
        resp = client.get("/health/full")
        assert resp.status_code == 200


class Test404:
    """Tests for error handling."""

    def test_404_page(self, client):
        resp = client.get("/nonexistent-page-xyz-12345")
        assert resp.status_code in (404, 308)
        if resp.status_code == 308:
            resp = client.get(resp.headers["Location"])
            assert resp.status_code == 404


class TestDemandeAnimationPage:
    """Tests for the demande animation form."""

    def test_form_page_returns_200(self, client):
        resp = client.get("/demande_animation")
        assert resp.status_code == 200

    def test_form_contains_fields(self, client):
        resp = client.get("/demande_animation")
        html = resp.data.decode("utf-8")
        assert 'name="structure"' in html
        assert 'name="nom"' in html
        assert 'name="contact_email"' in html


class TestDemandesAnimationPages:
    """Tests for the public demandes animation pages."""

    def test_list_page_hides_map_button_from_anonymous_visitors(self, client):
        resp = client.get("/demandes-animation")
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "Carte de France" not in html

    def test_map_page_redirects_anonymous_visitors(self, client):
        resp = client.get("/demandes-animation/carte")
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/demandes-animation")

    def test_map_page_allows_accounts_created_before_cutoff(self, client, db):
        from datetime import datetime
        from models.models import User

        user = User(
            username="old-map-user",
            created_at=datetime(2026, 9, 11, 23, 59),
        )
        user.set_password("test-password")
        db.session.add(user)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["username"] = user.username

        resp = client.get("/demandes-animation/carte")
        assert resp.status_code == 200

    def test_map_page_allows_subscribers_created_after_cutoff(self, client, db):
        from datetime import datetime
        from models.models import User

        user = User(
            username="subscribed-map-user",
            created_at=datetime(2026, 9, 12),
            is_subscribed=True,
        )
        user.set_password("test-password")
        db.session.add(user)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["username"] = user.username

        resp = client.get("/demandes-animation/carte")
        assert resp.status_code == 200

    def test_map_page_denies_recent_unsubscribed_accounts(self, client, db):
        from datetime import datetime
        from models.models import User

        user = User(
            username="new-map-user",
            created_at=datetime(2026, 9, 12),
        )
        user.set_password("test-password")
        db.session.add(user)
        db.session.commit()
        with client.session_transaction() as sess:
            sess["username"] = user.username

        list_resp = client.get("/demandes-animation")
        assert "Carte de France" not in list_resp.data.decode("utf-8")
        map_resp = client.get("/demandes-animation/carte")
        assert map_resp.status_code == 302
        assert map_resp.headers["Location"].endswith("/demandes-animation")


class TestEvenementsPage:
    """Tests for the evenements page."""

    def test_evenements_returns_200(self, client):
        resp = client.get("/evenements")
        assert resp.status_code == 200
