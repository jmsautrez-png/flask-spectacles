"""Règle d'affichage du téléphone du demandeur selon le compte."""

from types import SimpleNamespace

import pytest

from utils.offres import telephone_visible


@pytest.mark.parametrize(
    "user, attendu",
    [
        (None, False),
        (SimpleNamespace(is_admin=True, is_subscribed=False, formule_abonnement=None), True),
        (SimpleNamespace(is_admin=False, is_subscribed=False, formule_abonnement=None), False),
        (SimpleNamespace(is_admin=False, is_subscribed=False, formule_abonnement="99"), False),
        (SimpleNamespace(is_admin=False, is_subscribed=True, formule_abonnement="49"), False),
        (SimpleNamespace(is_admin=False, is_subscribed=True, formule_abonnement="99"), True),
        (SimpleNamespace(is_admin=False, is_subscribed=True, formule_abonnement=None), False),
    ],
)
def test_telephone_visible_selon_formule(user, attendu):
    assert telephone_visible(user) is attendu
