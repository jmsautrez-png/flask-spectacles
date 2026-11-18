"""Limite de cartes par compte compagnie : 6 sans abonnement, 10 avec abonnement."""

from datetime import datetime, timedelta

from tests.test_fiche_secteur import make_show, no_upload, page_text, publish  # noqa: F401


def cartes_de(user):
    from models.models import Show

    return Show.query.filter_by(user_id=user.id).count()


def remplir(user, n):
    for i in range(n):
        make_show(user, title=f"Carte {i}")


def abonner(user, jours=365):
    from models import db

    user.is_subscribed = True
    user.subscribed_until = datetime.utcnow() + timedelta(days=jours)
    db.session.commit()


def test_non_abonne_bloque_la_septieme_carte(logged_in_client, normal_user):
    remplir(normal_user, 6)

    response = publish(logged_in_client, ["Cirque"], title="Septième")

    assert cartes_de(normal_user) == 6
    assert "Limite atteinte : 6 cartes maximum" in page_text(response)


def test_non_abonne_peut_publier_la_sixieme_carte(logged_in_client, normal_user):
    remplir(normal_user, 5)

    publish(logged_in_client, ["Cirque"], title="Sixième")

    assert cartes_de(normal_user) == 6


def test_abonne_bloque_la_onzieme_carte(logged_in_client, normal_user):
    abonner(normal_user)
    remplir(normal_user, 10)

    response = publish(logged_in_client, ["Cirque"], title="Onzième")

    assert cartes_de(normal_user) == 10
    assert "Limite atteinte : 10 cartes maximum" in page_text(response)


def test_abonnement_expire_revient_a_la_limite_de_six(logged_in_client, normal_user):
    abonner(normal_user, jours=-1)
    remplir(normal_user, 6)

    publish(logged_in_client, ["Cirque"], title="Septième")

    assert cartes_de(normal_user) == 6


def test_ouverture_du_formulaire_avertit_la_limite_atteinte(logged_in_client, normal_user):
    remplir(normal_user, 6)

    html = page_text(logged_in_client.get("/submit"))

    assert "Vous avez atteint la limite de 6 cartes" in html


def test_ouverture_du_formulaire_affiche_le_compteur(logged_in_client, normal_user):
    remplir(normal_user, 2)

    html = page_text(logged_in_client.get("/submit"))

    assert "Vous avez 2 carte(s) sur 6 autorisées." in html
