"""Pytest configuration and shared fixtures for flask-spectacles tests."""
import os
import sys
import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def app():
    """Provide the Flask application configured for testing."""
    os.environ["FLASK_ENV"] = "testing"
    os.environ["SECRET_KEY"] = "test-secret-key-for-ci"
    os.environ["ADMIN_USERNAME"] = "testadmin"
    os.environ["ADMIN_PASSWORD"] = "testpass123"

    import app as app_module
    application = app_module.app
    application.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SERVER_NAME": "localhost",
    })

    # Force SQLAlchemy to recreate engine with the new sqlite URI
    from models import db as _db
    with application.app_context():
        _db.engine.dispose()

    yield application


@pytest.fixture(scope="function")
def client(app):
    """Flask test client with fresh DB per test."""
    from models import db as _db

    ctx = app.app_context()
    ctx.push()
    _db.session.remove()
    _db.drop_all()
    _db.create_all()

    with app.test_client() as c:
        yield c

    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture
def db(app):
    """Provide the db instance within app context."""
    from models import db as _db
    ctx = app.app_context()
    ctx.push()
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    from models.models import User
    user = User(username="testadmin", is_admin=True, email="admin@test.com")
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    yield user


@pytest.fixture
def normal_user(db):
    """Create a regular user."""
    from models.models import User
    user = User(username="testuser", is_admin=False, email="user@test.com")
    user.set_password("userpass123")
    db.session.add(user)
    db.session.commit()
    yield user


@pytest.fixture
def logged_in_client(client, normal_user):
    """A test client already logged in as a normal user."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    yield client


@pytest.fixture
def admin_client(client, admin_user):
    """A test client already logged in as admin."""
    with client.session_transaction() as sess:
        sess["username"] = "testadmin"
    yield client
