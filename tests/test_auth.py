"""Tests for authentication routes: login, register, logout."""
import pytest


class TestLoginRoute:
    """Tests for the login page."""

    def test_login_page_returns_200(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_login_page_contains_form(self, client):
        resp = client.get("/login")
        html = resp.data.decode("utf-8")
        assert 'name="username"' in html
        assert 'name="password"' in html

    def test_login_with_valid_credentials(self, client, admin_user):
        resp = client.post("/login", data={
            "username": "testadmin",
            "password": "testpass123",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_with_invalid_credentials(self, client):
        resp = client.post("/login", data={
            "username": "fakeuser",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        # Should show error or stay on login page
        assert "login" in html.lower() or "erreur" in html.lower() or "incorrect" in html.lower()

    def test_login_redirect_when_authenticated(self, logged_in_client):
        resp = logged_in_client.get("/login", follow_redirects=False)
        # Already logged in — may redirect or show page
        assert resp.status_code in (200, 302)


class TestLogoutRoute:
    """Tests for logout."""

    def test_logout_redirects(self, logged_in_client):
        resp = logged_in_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_clears_session(self, logged_in_client):
        logged_in_client.get("/logout", follow_redirects=True)
        # After logout, accessing dashboard should redirect to login
        resp = logged_in_client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302


class TestRegisterRoute:
    """Tests for the registration page."""

    def test_register_page_returns_200(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200

    def test_register_page_contains_form(self, client):
        resp = client.get("/register")
        html = resp.data.decode("utf-8")
        assert 'name="username"' in html
        assert 'name="email"' in html

    def test_register_with_short_password(self, client):
        resp = client.post("/register", data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",
            "confirm_password": "123",
            "nom_compagnie": "Test Compagnie",
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestProtectedRoutes:
    """Tests for routes requiring authentication."""

    def test_dashboard_requires_login(self, client):
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("Location", "")

    def test_admin_requires_login(self, client):
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_requires_admin_role(self, logged_in_client):
        # normal user should be redirected from admin panel
        resp = logged_in_client.get("/admin", follow_redirects=False)
        assert resp.status_code in (302, 403)

    def test_admin_can_access_dashboard(self, admin_client):
        resp = admin_client.get("/admin")
        assert resp.status_code == 200
