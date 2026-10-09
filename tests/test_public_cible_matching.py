"""Exact public matching and multi-age form regression tests."""

from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader

from constants import (
    PUBLIC_CIBLE_ADMIN,
    PUBLIC_CIBLE_CATEGORIES,
    PUBLIC_CIBLE_INCOMPATIBLES,
    PUBLIC_CIBLE_ORGANISATEUR,
)
from utils.matching import _public_cible_compatible, compute_score, find_matching_shows


FAMILY_AGES = ("fam_pe", "fam_3", "fam_6", "fam_8", "fam_10", "fam_12", "fam_16")


def public(cats="famille", subs=""):
    return SimpleNamespace(public_categories=cats, public_sous_options=subs)


@pytest.mark.parametrize("show_age", FAMILY_AGES)
@pytest.mark.parametrize("request_age", FAMILY_AGES)
def test_only_identical_checked_ages_match(show_age, request_age):
    assert _public_cible_compatible(
        public(subs=show_age), public(subs=request_age)
    ) == (show_age == request_age, True)


@pytest.mark.parametrize(
    "show_subs,request_subs,expected",
    [
        ("fam_3,fam_10", "fam_10", True),
        ("fam_10,fam_12,fam_16", "fam_16", True),
        ("fam_12", "fam_10,fam_12,fam_16", True),
        ("fam_3,fam_6", "fam_10,fam_16", False),
        ("fam_16", "fam_10,fam_12", False),
        (" FAM_10 , fam_16 ", "fam_10", True),
    ],
)
def test_multiple_ages_use_or(show_subs, request_subs, expected):
    assert _public_cible_compatible(
        public(subs=show_subs), public(subs=request_subs)
    ) == (expected, True)


@pytest.mark.parametrize(
    "show,demande,expected",
    [
        (public("adultes", "ad_16"), public("famille", "fam_16"), False),
        (public("enfants", "mat"), public("enfants", "elem"), False),
        (public("enfants", "mat,elem"), public("enfants", "elem"), True),
        (
            public("enfants,famille", "elem,fam_10"),
            public("enfants", "fam_10,ado"),
            False,
        ),
        (public("famille"), public("famille", "fam_10"), True),
        (public("famille", "fam_10"), public("famille"), True),
        (public(""), public("famille", "fam_10"), False),
    ],
)
def test_category_filters_and_existing_unspecified_age_behavior(show, demande, expected):
    assert _public_cible_compatible(show, demande) == (expected, True)


def test_legacy_request_still_uses_legacy_matching():
    assert _public_cible_compatible(public(subs="fam_10"), public("")) == (True, False)


def test_final_matching_excludes_other_ages_and_keeps_score():
    request = public(subs="fam_10")
    request.specialites_recherchees = ""
    request.lieux_souhaites = ""
    request.region = ""
    shows = []
    for subs in ("fam_3", "fam_10", "fam_12", "fam_16", "fam_3,fam_10"):
        show = public(subs=subs)
        show.specialites = ""
        show.lieux_intervention = ""
        show.regions_intervention = ""
        shows.append(show)

    result = find_matching_shows(request, shows, min_score=10)

    assert {show.public_sous_options for show, _ in result} == {
        "fam_10", "fam_3,fam_10",
    }
    for _, score in result:
        assert score["age_compatible"] is True
        assert score["age_bonus"] == 10.0
        assert score["total"] == 60.0
    assert compute_score(shows[2], request)["age_compatible"] is False


class CheckedInputs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and "checked" in attrs:
            self.values.append(attrs.get("value"))


@pytest.mark.parametrize(
    "categories",
    [PUBLIC_CIBLE_CATEGORIES, PUBLIC_CIBLE_ORGANISATEUR, PUBLIC_CIBLE_ADMIN],
)
def test_form_keeps_all_saved_ages_without_single_select(categories):
    env = Environment(
        loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "templates"),
        autoescape=True,
    )
    template = env.get_template("_accordion_checkboxes.html").module
    html = str(template.accordion_public_cible(
        categories, ["famille"], ["fam_3", "fam_10", "fam_16"],
        PUBLIC_CIBLE_INCOMPATIBLES,
    ))
    inputs = CheckedInputs()
    inputs.feed(html)

    assert inputs.values == ["famille", "fam_3", "fam_10", "fam_16"]
    assert "data-single-select" not in html
    assert "data-single-select" not in str(template.public_cible_js())
    assert all(not cat.get("single_select") for cat in categories)
