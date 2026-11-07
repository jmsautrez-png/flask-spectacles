from datetime import datetime

NOW = datetime(2026, 12, 15, 12, 0, 0)


def make_user(db, username, created_at, is_admin=False, **fields):
    from models.models import User

    user = User(
        username=username, email=f"{username}@test.com", is_admin=is_admin,
        created_at=created_at, **fields,
    )
    user.set_password("userpass123")
    db.session.add(user)
    db.session.commit()
    return user


def test_date_fin_gratuite_un_an_apres_creation():
    from alertes_fin_gratuite import date_fin_gratuite

    assert date_fin_gratuite(datetime(2026, 1, 10, 9, 30)) == datetime(2027, 1, 10, 9, 30)
    assert date_fin_gratuite(datetime(2028, 2, 29)) == datetime(2029, 2, 28)


def test_traiter_alerte_30_jours_avant_fin_une_seule_fois(db):
    from alertes_fin_gratuite import traiter
    from models.models import User

    user = make_user(db, "ancien", datetime(2026, 1, 10))
    user_id = user.id
    envois = []

    def fake_envoi(to, sujet, html):
        envois.append((to, sujet))
        return True

    stats = traiter(NOW, apply=True, envoyer=fake_envoi, admin_addr="admin@test.com")
    assert stats == {"alertes": 1, "deja_passes": 0}
    assert len(envois) == 1
    assert envois[0][0] == "admin@test.com"
    assert "ancien" in envois[0][1] and "10/01/2027" in envois[0][1]

    assert db.session.get(User, user_id).fin_gratuite_alerte_sent_for == datetime(2027, 1, 10)

    envois.clear()
    stats = traiter(NOW, apply=True, envoyer=fake_envoi, admin_addr="admin@test.com")
    assert stats == {"alertes": 0, "deja_passes": 0}
    assert envois == []


def test_traiter_no_alert_more_than_30_days_before_end(db):
    from alertes_fin_gratuite import traiter

    make_user(db, "ancien", datetime(2026, 1, 20))  # fin le 20/01/2027, soit 36 jours après NOW
    envois = []

    stats = traiter(NOW, apply=True, envoyer=lambda *a: envois.append(a) or True, admin_addr="admin@test.com")
    assert stats == {"alertes": 0, "deja_passes": 0}
    assert envois == []


def test_traiter_dry_run_changes_nothing(db):
    from alertes_fin_gratuite import traiter
    from models.models import User

    user = make_user(db, "ancien", datetime(2026, 1, 10))
    user_id = user.id
    envois = []

    stats = traiter(NOW, apply=False, envoyer=lambda *a: envois.append(a) or True, admin_addr="admin@test.com")
    assert stats == {"alertes": 1, "deja_passes": 0}
    assert envois == []
    assert db.session.get(User, user_id).fin_gratuite_alerte_sent_for is None


def test_traiter_failed_send_is_not_recorded(db):
    from alertes_fin_gratuite import traiter
    from models.models import User

    user = make_user(db, "ancien", datetime(2026, 1, 10))
    user_id = user.id

    traiter(NOW, apply=True, envoyer=lambda *a: False, admin_addr="admin@test.com")
    assert db.session.get(User, user_id).fin_gratuite_alerte_sent_for is None


def test_traiter_ignores_new_accounts_admins_and_already_passed(db):
    from alertes_fin_gratuite import traiter

    make_user(db, "nouveau", datetime(2026, 10, 1))  # modèle payant : hors périmètre
    make_user(db, "admin", datetime(2026, 1, 10), is_admin=True)
    make_user(db, "tres_ancien", datetime(2025, 3, 1))  # fin déjà passée : listé, non alerté
    envois = []

    stats = traiter(NOW, apply=True, envoyer=lambda *a: envois.append(a) or True, admin_addr="admin@test.com")
    assert stats == {"alertes": 0, "deja_passes": 1}
    assert envois == []
