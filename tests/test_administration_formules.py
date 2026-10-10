"""Local proposal for internally prepared date dossiers."""

from html.parser import HTMLParser

import pytest

from constants import ADMINISTRATION_FORMULES


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.append(dict(attrs).get("href"))


@pytest.mark.parametrize("signed_in", [False, True])
def test_offer_discovery_button_opens_public_list_without_subscription(
    client, normal_user, signed_in,
):
    if signed_in:
        with client.session_transaction() as session:
            session["username"] = normal_user.username
    html = client.get("/abonnement-compagnie/appels-offres").get_data(as_text=True)
    assert '<a class="offer-button" href="/demandes-animation">Découvrir les appels d\'offres</a>' in html
    assert client.get("/demandes-animation").status_code == 200


def test_company_service_entry_has_two_distinct_pages(client):
    response = client.get("/abonnement-compagnie")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    links = Links()
    links.feed(html)
    assert '<a href="/abonnement-compagnie" class="menu-abonnement">Nos services pour les compagnies</a>' in html
    assert links.hrefs.index("/abonnement-compagnie/appels-offres") < links.hrefs.index("/abonnement-compagnie/secretariat")
    assert "La mise en relation avec les organisateurs est au cœur de notre plateforme." in html
    assert "audience-choice-primary" in html
    assert "1 000 appels d'offres et 2 000 demandes de devis par an" in html
    assert "50 000 visites annuelles" in html
    assert 'class="pricing-panel"' not in html
    assert 'class="offer-section ao-offer"' not in html


def test_calls_for_offers_page_is_independent(client):
    response = client.get("/abonnement-compagnie/appels-offres")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<p class="offer-price">49 €</p>' in html
    assert "TTC la première année &mdash; puis 99 €/an." in html
    assert "Les appels d'offres : au cœur de votre activité sur la plateforme" in html
    assert "Découvrez les demandes des écoles, APE, mairies, médiathèques, CSE, CF et CLSH." in html
    assert "accès aux annonces complètes et aux coordonnées des organisateurs" in html
    assert "<strong>Ce qui reste gratuit :</strong> la publication de vos spectacles et la réception de demandes de devis." in html
    assert "sans commission sur votre prix initial" in html
    assert "LE CŒUR DE LA MISE EN RELATION" in html
    assert "<strong>1 000</strong><span>appels d'offres par an</span>" in html
    assert "<strong>2 000</strong><span>demandes de devis par an</span>" in html
    assert "<strong>50 000</strong><span>visites par an</span>" in html
    assert 'class="pricing-panel"' not in html
    assert 'class="payroll-option"' not in html
    links = Links()
    links.feed(html)
    assert "/abonnement-compagnie" in links.hrefs
    assert "/abonnement-compagnie/secretariat" in links.hrefs


def test_offer_page_has_three_prices_and_real_contact_buttons(client):
    response = client.get("/abonnement-compagnie/secretariat")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    links = Links()
    links.feed(html)
    for plan in ADMINISTRATION_FORMULES:
        assert f'id="formule-{plan["code"]}"' in html
        assert f'{plan["prix"]} €' in html
        assert any(
            href and f"formule={plan['code']}" in href
            and "sujet=administration" in href
            for href in links.hrefs
        )
    assert 'class="offer-note"' not in html
    assert "Une date de spectacle = un dossier." not in html
    assert "10 dossiers de dates" in html
    assert "20 dossiers de dates" in html
    assert "40 dossiers de dates" in html
    assert "illimités" not in html
    assert '<p class="offer-price">49 €</p>' not in html
    assert "220 €" not in html
    assert "16 € la fiche" not in html
    assert "générés" not in html
    assert "Aucun paiement ni abonnement" in html
    assert "Les appels d'offres ne sont pas inclus." in html
    assert 'class="offer-section ao-offer"' not in html
    assert "/abonnement-compagnie" in links.hrefs
    assert "/abonnement-compagnie/appels-offres" in links.hrefs
    assert "appels d'offres inclus" not in html
    assert "Accès aux appels d'offres</li>" not in html
    assert html.count('class="included-item"') == 6
    assert "<h3>Envoi et suivi de vos factures</h3>" in html
    assert "Envoi de vos factures aux organisateurs et suivi des règlements" in html
    assert "Calendrier de vos dates" not in html
    assert "Demander un devis personnalisé" in html
    assert "Secrétariat et accompagnement administratif des compagnies" in html
    assert html.index('class="included-grid"') < html.index('class="pricing-panel"')
    assert "<h3>Contrats de travail</h3>" in html
    assert "CDDU" not in html
    assert html.count('class="offer-card') == 4
    assert (
        html.index('aria-labelledby="ponctuel-title"')
        < html.index('aria-labelledby="formule-essentiel"')
        < html.index('aria-labelledby="formule-compagnie"')
        < html.index('aria-labelledby="formule-pro"')
    )
    assert html.index('aria-labelledby="ponctuel-title"') < html.index("Chaque dossier comprend")


@pytest.mark.parametrize("plan", ADMINISTRATION_FORMULES, ids=lambda p: p["code"])
def test_each_contact_choice_preserves_plan_and_dossier_unit(client, plan):
    response = client.get("/contact", query_string={
        "sujet": "administration", "formule": plan["code"],
    })
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f'Formule {plan["nom"]} : {plan["prix"]} € TTC / an' in html
    assert "Une date de spectacle compte comme un dossier." in html
    assert "Je suis intéressé par la formule" in html
    assert "Nombre de dates de spectacle prévues par an" in html
    assert "Nombre d'artistes et techniciens par date" in html
    assert f'jusqu\'à {plan["dossiers"]} dossiers de dates' in html
    assert "220 €" not in html
    assert "hors abonnement appels d'offres" in html
    assert "Les appels d'offres ne sont pas inclus" in html
    assert "appels d'offres inclus" not in html


def test_payroll_option_contact_requests_quote_without_old_prices(client):
    html = client.get("/contact?sujet=fiche-paie").get_data(as_text=True)
    assert "Paie et déclarations sociales : option sur devis" in html
    assert "Je souhaite un devis pour l'option paie et déclarations sociales" in html
    assert "Ce service n'est inclus ni dans les formules annuelles ni dans le dossier à 9,99 € TTC." in html
    assert "220 €" not in html
    assert "16 €" not in html
    assert "supprimé" not in html


def test_payroll_option_has_concise_offer_page_text(client):
    html = client.get("/abonnement-compagnie/secretariat").get_data(as_text=True)
    assert "Besoin d'un coup de main pour la paie ?" in html
    assert "Parlons de vos besoins pour préparer un devis adapté." not in html
    assert "Une option sur devis, en supplément" not in html
    assert html.index('class="pricing-panel"') < html.index('class="payroll-option"')
    assert "ne sont plus proposés" not in html
    links = Links()
    links.feed(html)
    assert any(href and "sujet=fiche-paie" in href for href in links.hrefs)


def test_invalid_plan_is_explicitly_rejected(client):
    assert client.get("/contact?sujet=administration&formule=unknown").status_code == 400


def test_donation_and_default_contact_are_preserved(client):
    default = client.get("/contact")
    donation = client.get("/contact?sujet=don")
    assert default.status_code == donation.status_code == 200
    assert "Je souhaite soutenir" in donation.get_data(as_text=True)
    assert "Je suis intéressé par la formule" not in default.get_data(as_text=True)


def test_registration_invitation_highlights_free_registration_not_free_subscription(client):
    response = client.get("/register")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "2 000 demandes de devis par an" in html
    assert "1 000 appels d'offres par an" in html
    assert "50 000 visites par an" in html
    assert 'class="registration-invitation"' in html
    assert "Publiez gratuitement vos spectacles et animations !" in html
    assert "Après inscription, découvrez aussi nos appels d'offres, les annonces complètes et les coordonnées des organisateurs d'événements." in html
    assert html.index("Publiez gratuitement vos spectacles") < html.index("Après inscription, découvrez")
    assert "réservé aux abonnés : 49 € TTC la première année, puis 99 €/an." not in html
    assert "Les champs marqués" in html
    assert "l'édition des contrats de cession, des feuilles de route, des contrats de travail et des factures" in html
    assert "le suivi de vos contrats dans leur intégralité" in html
    assert "contrats de travail et suivi des dates, sans paie" not in html


def test_ponctual_contact_requests_quote_without_annual_plan(client):
    response = client.get("/contact?sujet=administration")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Je souhaite un devis pour un accompagnement administratif ponctuel" in html
    assert "Les appels d'offres ne sont pas inclus" in html
    assert "Formule Essentiel" not in html


def test_without_subscription_offer_and_contact(client):
    page = client.get("/abonnement-compagnie/secretariat").get_data(as_text=True)
    assert "9,99 €" in page
    assert "TTC par dossier de date traité" in page
    assert "Chaque dossier comprend un contrat de cession, les contrats de travail associés, une feuille de route et le suivi des factures." in page
    assert "plusieurs contrats de cession" not in page
    links = Links()
    links.feed(page)
    assert any(href and "formule=ponctuel" in href for href in links.hrefs)
    response = client.get("/contact?sujet=administration&formule=ponctuel")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Sans abonnement : 9,99 € TTC par dossier de date traité" in html
    assert "Je souhaite faire traiter un dossier de date à 9,99 € TTC" in html
    assert "un contrat de cession, les contrats de travail associés, une feuille de route et le suivi des factures" in html
    assert "plusieurs contrats de cession" not in html
    assert "hors abonnement appels d'offres" in html
    assert "9,99 € TTC par an" not in html


@pytest.mark.parametrize("path", ["/", "/register"])
def test_public_presentations_no_longer_promote_payroll(client, path):
    response = client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "URSSAF" not in html
    assert "fiches de salaire" not in html.lower()
    if path == "/":
        assert "sans paie" in html
    else:
        assert "des contrats de travail et des factures" in html
    assert "CDDU" not in html


def test_services_entry_offers_two_distinct_paths(client):
    response = client.get("/qui-sommes-nous")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    links = Links()
    links.feed(html)
    assert "/nos-services/organisateurs" in links.hrefs
    assert "/nos-services/compagnies" in links.hrefs
    assert "Vous organisez un événement" in html
    assert "Vous êtes artiste ou compagnie" in html
    assert "Nos critères de sélection" not in html
    assert "Deux services indépendants" not in html


@pytest.mark.parametrize("path,own,other", [
    ("/nos-services/organisateurs", "Nos critères de sélection", "Deux services indépendants"),
    ("/nos-services/compagnies", "Deux services indépendants", "Nos critères de sélection"),
])
def test_services_pages_separate_audiences(client, path, own, other):
    response = client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert own in html
    assert other not in html
    assert "CDDU" not in html
    links = Links()
    links.feed(html)
    assert "/qui-sommes-nous" in links.hrefs
    if path.endswith("compagnies"):
        assert "ainsi que l'envoi et le suivi de vos factures" in html
        assert '<a class="about-title-link" href="/abonnement-compagnie">Nos services pour les artistes et compagnies</a>' in html
        assert "/register" in links.hrefs
        assert "/demandes-animation" in links.hrefs
        assert "/abonnement-compagnie" in links.hrefs
    else:
        assert "/catalogue" in links.hrefs
        assert "/demande_animation" in links.hrefs
        assert "/contact" in links.hrefs


def test_selected_plan_message_reaches_internal_contact_without_activation(
    app, client, monkeypatch,
):
    from tests.test_offre_delivery import FakeMail
    from models.models import Adhesion

    mail = FakeMail()
    monkeypatch.setattr(app, "mail", mail)
    response = client.post("/contact?sujet=administration&formule=compagnie", data={
        "nom": "Test company", "email": "company@example.test",
        "message": "Formule Compagnie 149 EUR, 20 dossiers",
    })
    assert response.status_code == 200
    assert len(mail.messages) == 1
    assert "Formule Compagnie 149 EUR, 20 dossiers" in mail.messages[0].body
    assert "Formule Compagnie : 149 € TTC / an" in response.get_data(as_text=True)
    assert Adhesion.query.count() == 0
