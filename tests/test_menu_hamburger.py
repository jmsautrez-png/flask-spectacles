"""Menu hamburger : les deux actions principales (demande de spectacle, publication de spectacle)."""

import re

import pytest


def menu_links(html):
    menu = html.split('id="hamburger-menu"', 1)[1].split("</div>", 1)[0]
    return re.findall(r'<a href="([^"]*)" class="([^"]*)">([^<]*)</a>', menu)


@pytest.mark.parametrize("signed_in", [False, True])
def test_hamburger_offers_request_and_publish_buttons_before_catalogue(client, normal_user, signed_in):
    if signed_in:
        with client.session_transaction() as session:
            session["username"] = normal_user.username
    links = menu_links(client.get("/").get_data(as_text=True))
    classes = [css for _, css, _ in links]
    by_class = {css: (href, text) for href, css, text in links}

    assert by_class["menu-demande"][0] == "/demande_animation"
    assert "demande de spectacle" in by_class["menu-demande"][1]
    assert by_class["menu-publier"][0] == "/submit"
    assert "Publier mon spectacle" in by_class["menu-publier"][1]
    assert classes.index("menu-demande") < classes.index("menu-publier") < classes.index("menu-catalogue")
