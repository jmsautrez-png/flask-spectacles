"""Matching engine: score spectacle companies against calls for tender."""

from constants import (
    SPECIALITES, EVENEMENTS, LIEUX, REGIONS_FRANCE, REGIONS_VOISINES,
    PUBLIC_CIBLE_CODES_VALIDES,
)
from utils.geo import distance_km, distance_score

# Nombre total d'options par axe (calculé une seule fois au chargement)
_TOTAL_SPECS = sum(len(v) for v in SPECIALITES.values())
_TOTAL_EVENTS = sum(len(v) for v in EVENEMENTS.values())
_TOTAL_LIEUX = sum(len(v) for v in LIEUX.values())
_TOTAL_REGIONS = len(REGIONS_FRANCE)

# Lookup case-insensitive pour REGIONS_VOISINES
_REGIONS_VOISINES_LOWER = {k.lower(): [r.lower() for r in v] for k, v in REGIONS_VOISINES.items()}

# --- Compatibilité tranche d'âge ---
# Groupes incompatibles : adulte vs enfant*  →  exclusion totale
_GROUPE_ADULTE = {"adulte", "ad_12", "ad_16"}
_GROUPE_ENFANT = {"enfant", "enfant_2_6", "enfant_5_10", "enfants_2_10",
                  "jp_0_3", "jp_4_8", "jp_7_11", "jp_8_11", "jp_des_3"}
# Valeurs neutres : acceptées avec tout le monde
_GROUPE_NEUTRE = {"familial", "tout public", "fam_2", "fam_3", "fam_8"}
# Groupe "animations diverses" : strict, ne matche qu'avec lui-même
_GROUPE_ANIM_DIV = {"anim_div"}

# Tranches proches (chevauchement partiel)  →  boost doux
_AGE_PROCHES = {
    # Ancien format
    "enfant_2_6":   {"enfant_5_10", "enfants_2_10", "enfant", "jp_0_3", "jp_4_8", "jp_des_3"},
    "enfant_5_10":  {"enfant_2_6",  "enfants_2_10", "enfant", "jp_4_8", "jp_7_11", "jp_8_11", "jp_des_3"},
    "enfants_2_10": {"enfant_2_6",  "enfant_5_10",  "enfant", "jp_4_8", "jp_7_11", "jp_8_11", "jp_des_3"},
    "enfant":       {"enfant_2_6",  "enfant_5_10",  "enfants_2_10", "jp_4_8", "jp_des_3"},
    # Nouveau format (jeune public ou familial)
    "jp_0_3":       {"jp_4_8", "enfant_2_6"},
    "jp_4_8":       {"jp_0_3", "jp_7_11", "jp_8_11", "jp_des_3", "enfant", "enfant_2_6", "enfant_5_10", "enfants_2_10"},
    "jp_7_11":      {"jp_4_8", "jp_8_11", "jp_des_3", "enfant_5_10", "enfants_2_10"},
    "jp_8_11":      {"jp_4_8", "jp_7_11", "jp_des_3", "enfant_5_10", "enfants_2_10"},
    "jp_des_3":     {"jp_4_8", "jp_7_11", "jp_8_11", "enfant", "enfant_2_6", "enfant_5_10", "enfants_2_10"},
    # Ancien format (familial à partir de X / toute la famille)
    "fam_2":        {"jp_0_3", "jp_4_8", "jp_7_11", "jp_8_11", "jp_des_3", "enfant", "familial"},
    "fam_3":        {"fam_8", "fam_2", "jp_des_3"},
    "fam_8":        {"fam_3", "fam_2"},
    # Nouveau format (adulte)
    "ad_12":        {"ad_16", "adulte"},
    "ad_16":        {"ad_12", "adulte"},
    "adulte":       {"ad_12", "ad_16"},
}


def _age_score(show_age_raw, dem_age_raw):
    """Retourne (compatible: bool, bonus: float 0-10).

    compatible=False  →  le spectacle doit être exclu.
    bonus             →  points ajoutés au total (max 10).
    """
    show_age = (show_age_raw or "").strip().lower()
    dem_age  = (dem_age_raw  or "").strip().lower()

    # Si l'un des deux n'est pas renseigné → pas d'exclusion, pas de bonus
    if not show_age or not dem_age:
        return True, 0.0

    # Animations diverses : strict, doit matcher exactement
    if dem_age in _GROUPE_ANIM_DIV or show_age in _GROUPE_ANIM_DIV:
        if show_age == dem_age:
            return True, 10.0
        return False, 0.0

    # Valeurs neutres → toujours compatible, bonus neutre
    if dem_age in _GROUPE_NEUTRE or show_age in _GROUPE_NEUTRE:
        return True, 5.0

    # Incompatibilité adulte ↔ enfant
    if dem_age in _GROUPE_ADULTE and show_age in _GROUPE_ENFANT:
        return False, 0.0
    if dem_age in _GROUPE_ENFANT and show_age in _GROUPE_ADULTE:
        return False, 0.0

    # Correspondance exacte
    if show_age == dem_age:
        return True, 10.0

    # Tranches proches
    if show_age in _AGE_PROCHES.get(dem_age, set()):
        return True, 5.0

    # Même groupe mais pas de correspondance précise → neutre
    return True, 0.0


def _csv_to_set(value):
    """Convert a CSV string (or None) to a set of stripped, lower-cased, non-empty values."""
    if not value:
        return set()
    return {v.strip().lower() for v in value.split(",") if v.strip()}


def _public_cible_compatible(show, demande):
    """Matching strict Public Cible v2.

    Retourne (compatible: bool, has_data: bool).
    - has_data=False  → la demande n'utilise pas le nouveau format ; l'appelant
                        retombera sur l'ancien filtre age_range.
    - compatible=True → au moins 1 catégorie commune ET au moins 1 sous-option
                        commune (parmi les sous-options des catégories communes).
    """
    dem_cats = _csv_to_set(getattr(demande, "public_categories", None))
    if not dem_cats:
        return True, False  # ancien format, pas de filtre v2
    show_cats = _csv_to_set(getattr(show, "public_categories", None))
    if not show_cats:
        return False, True  # demande v2 mais show pas migré → exclu
    common_cats = dem_cats & show_cats
    if not common_cats:
        return False, True

    dem_subs = _csv_to_set(getattr(demande, "public_sous_options", None))
    show_subs = _csv_to_set(getattr(show, "public_sous_options", None))

    # Restreindre les sous-options aux catégories communes
    allowed_subs = set()
    for cat_code in common_cats:
        for sub in PUBLIC_CIBLE_CODES_VALIDES.get(cat_code, []):
            allowed_subs.add(sub.lower())

    dem_subs_in_common = dem_subs & allowed_subs
    show_subs_in_common = show_subs & allowed_subs

    # Si la demande n'a pas précisé de sous-options pour les catégories communes,
    # la catégorie commune suffit
    if not dem_subs_in_common:
        return True, True
    # Sinon il faut au moins 1 sous-option commune
    if dem_subs_in_common & show_subs_in_common:
        return True, True
    return False, True


def _specificity(n_checked, n_total):
    """Pénalité de spécificité : plus on coche, plus le score est dilué.

    Retourne un coefficient entre 0.5 (tout coché) et 1.0 (très ciblé).
    Formule : 1 - 0.5 × (n_checked / n_total)
    """
    if n_total == 0:
        return 1.0
    return 1.0 - 0.5 * (n_checked / n_total)


def compute_score(show, demande):
    """Return a dict with per-axis scores and a total score (0-100).

    Axes:
      - specialites  (weight 40)
      - evenements   (weight 25)
      - lieux        (weight 20)
      - region       (weight 15)
      + age_range    bonus +0/+5/+10 (hors pondération principale)

    Each axis yields a ratio [0..1] = (|intersection| / |demande tags|) × specificity.
    The specificity penalty penalises companies that check too many boxes:
      specificity = 1 - 0.5 × (n_checked / total_options)
    Region matching: exact region = 1.0, neighbour region = 0.5, else 0.
    Age range: incompatible → excluded (returns compatible=False); exact → +10; proche → +5.
    """
    show_specs = _csv_to_set(show.specialites)
    show_events = _csv_to_set(show.evenements)
    show_lieux = _csv_to_set(show.lieux_intervention)
    show_regions = _csv_to_set(show.regions_intervention)

    dem_specs = _csv_to_set(demande.specialites_recherchees)
    dem_events = _csv_to_set(demande.evenements_contexte)
    dem_lieux = _csv_to_set(demande.lieux_souhaites)
    dem_region = (demande.region or "").strip().lower()

    # -- Tranche d'âge (filtre dur + bonus hors pondération) --
    age_compatible, age_bonus = _age_score(
        getattr(show, "age_range", None),
        getattr(demande, "age_range", None),
    )

    # -- Public Cible v2 (matching strict catégories + sous-options) --
    public_compatible, public_v2_used = _public_cible_compatible(show, demande)
    if public_v2_used:
        # Le format v2 est utilisé sur la demande : il prend le pas sur age_range
        age_compatible = public_compatible
        if public_compatible:
            age_bonus = 10.0
        else:
            age_bonus = 0.0

    # -- Spécialités (40%) --
    if dem_specs:
        match_ratio = len(show_specs & dem_specs) / len(dem_specs)
        spec_ratio = match_ratio * _specificity(len(show_specs), _TOTAL_SPECS)
    else:
        spec_ratio = 1.0 if show_specs else 0.5

    # -- Événements (25%) --
    if dem_events:
        match_ratio = len(show_events & dem_events) / len(dem_events)
        event_ratio = match_ratio * _specificity(len(show_events), _TOTAL_EVENTS)
    else:
        event_ratio = 0.0

    # -- Lieux (20%) --
    if dem_lieux:
        match_ratio = len(show_lieux & dem_lieux) / len(dem_lieux)
        lieu_ratio = match_ratio * _specificity(len(show_lieux), _TOTAL_LIEUX)
    else:
        lieu_ratio = 0.0

    # -- Région / Distance (15%) --
    # Strategie hybride :
    # 1) Si on a les CP demandeur ET cie  -> score base sur la distance km (Haversine).
    # 2) Sinon, fallback sur la region native de la cie (User.region) avec regle stricte.
    # 3) Sinon, fallback sur regions_intervention (ancien comportement, score divise).
    show_location = (getattr(show, "location", None) or "").strip().lower()
    show_couvre_france = (
        "toute la france" in show_location
        or "france entiere" in show_location
        or "france entière" in show_location
    )

    portee_nationale = getattr(demande, "portee_nationale", True)
    region_compatible = True

    # Recuperer les CP des deux cotes (compagnie via show.user)
    dem_cp = (getattr(demande, "code_postal", None) or "").strip() or None
    show_user = getattr(show, "user", None)
    cie_cp = (getattr(show_user, "code_postal", None) or "").strip() if show_user else None
    cie_region = (getattr(show_user, "region", None) or "").strip().lower() if show_user else ""
    # Fallback: si pas de region utilisateur (orphelin ou compte incomplet),
    # on utilise la region renseignee directement sur le spectacle.
    if not cie_region:
        cie_region = (getattr(show, "region", None) or "").strip().lower()

    distance = None
    if dem_cp and cie_cp:
        distance = distance_km(dem_cp, cie_cp)

    if show_couvre_france:
        # Le spectacle se deplace partout : score regional max
        region_ratio = 1.0
    elif distance is not None:
        # Cas ideal : score distance pur, pas de penalite de specificite
        region_ratio = distance_score(distance)
        # Filtre dur "regional uniquement" : > 200 km -> exclu
        if portee_nationale is False and distance > 200:
            region_compatible = False
    elif cie_region and dem_region:
        # Fallback region native : strict si meme region, sinon voisine = 0.5
        if cie_region == dem_region:
            region_ratio = 1.0
        else:
            neighbours = set(_REGIONS_VOISINES_LOWER.get(dem_region, []))
            region_ratio = 0.5 if cie_region in neighbours else 0.0
        # Filtre dur "regional uniquement" : region differente -> exclu
        if portee_nationale is False and cie_region != dem_region:
            region_compatible = False
    elif show_regions and dem_region:
        # Dernier recours : ancien comportement avec regions_intervention CSV
        if dem_region in show_regions:
            region_ratio = 1.0
        else:
            neighbours = set(_REGIONS_VOISINES_LOWER.get(dem_region, []))
            region_ratio = 0.5 if (show_regions & neighbours) else 0.0
        region_ratio *= _specificity(len(show_regions), _TOTAL_REGIONS)
        if portee_nationale is False and dem_region not in show_regions:
            region_compatible = False
    elif not dem_region:
        region_ratio = 0.5
    else:
        # Aucune info geo cote cie -> score nul ; exclu si regional uniquement
        region_ratio = 0.0
        if portee_nationale is False:
            region_compatible = False

    total = (spec_ratio * 40 + event_ratio * 25 + lieu_ratio * 20 + region_ratio * 15)
    # Bonus tranche d'âge (hors pondération principale, max +10)
    total = min(100.0, total + age_bonus)

    return {
        "total": round(total, 1),
        "specialites": round(spec_ratio * 100, 1),
        "evenements": round(event_ratio * 100, 1),
        "lieux": round(lieu_ratio * 100, 1),
        "region": round(region_ratio * 100, 1),
        "distance_km": round(distance, 1) if distance is not None else None,
        "age_compatible": age_compatible,
        "age_bonus": age_bonus,
        "region_compatible": region_compatible,
        "matching_specs": show_specs & dem_specs,
        "matching_events": show_events & dem_events,
        "matching_lieux": show_lieux & dem_lieux,
    }


def find_matching_shows(demande, all_shows, min_score=1):
    """Return a list of (show, score_dict) sorted by total score desc.

    Only shows with total >= min_score are included.
    If the demande specifies specialites, shows with 0% specialites match
    are excluded (they matched only on generic criteria like events/lieux).
    """
    dem_specs = _csv_to_set(demande.specialites_recherchees)
    results = []
    for show in all_shows:
        score = compute_score(show, demande)
        # Exclure les shows incompatibles avec la tranche d'âge
        if not score["age_compatible"]:
            continue
        # Exclure les shows hors région si l'organisateur veut du régional uniquement
        if not score.get("region_compatible", True):
            continue
        if score["total"] >= min_score:
            # Exclure les shows sans aucun match sur les spécialités
            # quand la demande en spécifie (critère principal à 40%)
            if dem_specs and score["specialites"] == 0:
                continue
            results.append((show, score))
    results.sort(key=lambda x: x[1]["total"], reverse=True)
    return results
