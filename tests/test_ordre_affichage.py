"""Ordre d'affichage des cartes : enregistrement de la liste complète et mise en tête d'une carte."""
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


def test_saving_full_list_renumbers_everything(admin_client, db):
    shows = _make_shows(db, 4)
    a, b, c, d = shows

    # Enregistrement de toute la liste : on inverse tout l'ordre.
    response = admin_client.post(
        "/admin/shows/update-orders",
        json={"ids": [d.id, c.id, b.id, a.id]},
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    final = [s.title for s in Show.query.order_by(Show.display_order.asc(), Show.created_at.desc()).all()]
    assert final == [d.title, c.title, b.title, a.title]
    assert [Show.query.get(s.id).display_order for s in (d, c, b, a)] == [10, 20, 30, 40]


def test_ordre_affichage_top_button_moves_show_to_global_first(admin_client, db):
    shows = _make_shows(db, 4)
    a, b, c, d = shows

    # Bouton jaune sur d : envoyé seul, il passe en tête de toute la liste.
    response = admin_client.post(
        "/admin/shows/update-orders",
        json={"ids": [d.id]},
    )

    assert response.get_json()["success"] is True
    final = [s.title for s in Show.query.order_by(Show.display_order.asc(), Show.created_at.desc()).all()]
    assert final == [d.title, a.title, b.title, c.title]


def test_ordre_affichage_renders_whole_list_for_search(admin_client, db):
    _make_shows(db, 60)

    response = admin_client.get("/admin/ordre-affichage")

    html = response.data.decode("utf-8")
    assert html.count('class="sortable-item"') == 60  # toutes les cartes, pas seulement la page 1
    assert 'id="recherche-compagnie"' in html
    assert 'data-recherche="Spectacle 0 Compagnie"' in html
