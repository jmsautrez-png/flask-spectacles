"""Ordre d'affichage des cartes : une page renvoyée ne doit pas casser l'ordre des autres pages."""
from datetime import datetime, timedelta

from models.models import Show, User


def _make_shows(db, count):
    owner = User(username="ordre_owner", is_admin=False, email="ordre@test.com")
    owner.set_password("ordrepass")
    db.session.add(owner)
    db.session.commit()
    base = datetime(2024, 1, 1)
    shows = []
    for i in range(count):
        # Le plus récent en premier : created_at décroissant à l'affichage.
        show = Show(
            title=f"Spectacle {i}",
            raison_sociale="Compagnie",
            user_id=owner.id,
            approved=True,
            display_order=0,
            created_at=base - timedelta(minutes=i),
        )
        db.session.add(show)
        shows.append(show)
    db.session.commit()
    return shows


def test_reordering_second_page_keeps_first_page_intact(admin_client, db):
    shows = _make_shows(db, 4)  # ordre d'affichage initial : shows[0..3]
    a, b, c, d = shows

    # Page 2 (offset 2) : on inverse c et d.
    response = admin_client.post(
        "/admin/shows/update-orders",
        json={"ids": [d.id, c.id], "offset": 2},
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    final = [s.title for s in Show.query.order_by(Show.display_order.asc(), Show.created_at.desc()).all()]
    assert final == [a.title, b.title, d.title, c.title]
    assert [Show.query.get(s.id).display_order for s in (a, b, d, c)] == [10, 20, 30, 40]


def test_ordre_affichage_top_button_moves_show_to_global_first(admin_client, db):
    shows = _make_shows(db, 4)
    a, b, c, d = shows

    # Bouton jaune sur d (ex. page 2) : envoyé seul, à l'offset 0 = tête de toute la liste.
    response = admin_client.post(
        "/admin/shows/update-orders",
        json={"ids": [d.id], "offset": 0},
    )

    assert response.get_json()["success"] is True
    final = [s.title for s in Show.query.order_by(Show.display_order.asc(), Show.created_at.desc()).all()]
    assert final == [d.title, a.title, b.title, c.title]


def test_ordre_affichage_renders_company_search_data(admin_client, db):
    _make_shows(db, 2)

    response = admin_client.get("/admin/ordre-affichage")

    html = response.data.decode("utf-8")
    assert 'id="recherche-compagnie"' in html
    assert 'data-compagnie="Compagnie"' in html
