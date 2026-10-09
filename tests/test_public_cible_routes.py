"""Multi-age persistence through artist and admin editing routes."""

import pytest


@pytest.mark.parametrize("admin_edit", [False, True])
def test_edit_preserves_multiple_checked_ages(
    app, client, normal_user, admin_user, admin_edit,
):
    from models import db
    from models.models import Show

    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    show = Show(
        title="Multi-age test",
        user_id=normal_user.id,
        public_categories="famille",
        public_sous_options="fam_3",
    )
    db.session.add(show)
    db.session.commit()
    show_id = show.id
    user = admin_user if admin_edit else normal_user
    with client.session_transaction() as session:
        session["username"] = user.username

    endpoint = "show_edit" if admin_edit else "show_edit_self"
    from flask import url_for
    with app.test_request_context():
        url = url_for(endpoint, show_id=show_id)
    response = client.post(url, data={
        "title": "Multi-age test",
        "specialites": ["Clown"],
        "regions_intervention": ["Bretagne"],
        "public_categories": ["famille"],
        "public_sous_options": ["fam_3", "fam_10", "fam_16"],
        "nb_comediens": "1",
    })

    assert response.status_code == (302 if admin_edit else 200)
    db.session.expire_all()
    saved = db.session.get(Show, show_id)
    assert saved.public_categories == "famille"
    assert saved.public_sous_options == "fam_3,fam_10,fam_16"
