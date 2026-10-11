"""Page piège : noindex, jeton stable par visiteur, visites journalisées, lien caché."""

import logging
import re

JETON = re.compile(r"Réf\. archive ([0-9A-F]{4}-[0-9A-F]{4})-1")
PAGE = "/archives/spectacles-2019"


def _jeton(html):
    return JETON.search(html).group(1)


def test_page_piege_noindex_et_fiches(client):
    rep = client.get(PAGE)
    assert rep.status_code == 200
    html = rep.get_data(as_text=True)
    assert 'content="noindex, nofollow"' in html
    assert "Compagnie Les Lanternes Imaginaires" in html
    assert "@archives.invalid" in html


def test_jeton_propre_a_chaque_visiteur_et_stable(client):
    bot_a = {"User-Agent": "BotA/1.0"}
    premier = _jeton(client.get(PAGE, headers=bot_a).get_data(as_text=True))
    autre = _jeton(client.get(PAGE, headers={"User-Agent": "BotB/1.0"}).get_data(as_text=True))
    assert premier != autre
    assert _jeton(client.get(PAGE, headers=bot_a).get_data(as_text=True)) == premier


def test_visite_journalisee_avec_jeton(client, caplog):
    with caplog.at_level(logging.WARNING):
        html = client.get(PAGE, headers={"User-Agent": "BotC/2.0"}).get_data(as_text=True)
    jeton = _jeton(html)
    assert any("[PIEGE]" in r.getMessage() and jeton in r.getMessage() for r in caplog.records)


def test_lien_cache_dans_le_pied_de_page(client):
    html = client.get("/").get_data(as_text=True)
    assert f'href="{PAGE}"' in html
    assert 'aria-hidden="true"' in html
