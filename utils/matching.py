"""Matching engine: score spectacle companies against calls for tender."""

from constants import SPECIALITES, EVENEMENTS, LIEUX, REGIONS_FRANCE, REGIONS_VOISINES

# Nombre total d'options par axe (calculé une seule fois au chargement)
_TOTAL_SPECS = sum(len(v) for v in SPECIALITES.values())
_TOTAL_EVENTS = sum(len(v) for v in EVENEMENTS.values())
_TOTAL_LIEUX = sum(len(v) for v in LIEUX.values())
_TOTAL_REGIONS = len(REGIONS_FRANCE)


def _csv_to_set(value):
    """Convert a CSV string (or None) to a set of stripped, non-empty values."""
    if not value:
        return set()
    return {v.strip() for v in value.split(",") if v.strip()}


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

    Each axis yields a ratio [0..1] = (|intersection| / |demande tags|) × specificity.
    The specificity penalty penalises companies that check too many boxes:
      specificity = 1 - 0.5 × (n_checked / total_options)
    Region matching: exact region = 1.0, neighbour region = 0.5, else 0.
    """
    show_specs = _csv_to_set(show.specialites)
    show_events = _csv_to_set(show.evenements)
    show_lieux = _csv_to_set(show.lieux_intervention)
    show_regions = _csv_to_set(show.regions_intervention)

    dem_specs = _csv_to_set(demande.specialites_recherchees)
    dem_events = _csv_to_set(demande.evenements_contexte)
    dem_lieux = _csv_to_set(demande.lieux_souhaites)
    dem_region = (demande.region or "").strip()

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

    # -- Région (15%) --
    if dem_region and show_regions:
        if dem_region in show_regions:
            region_ratio = 1.0
        else:
            neighbours = set(REGIONS_VOISINES.get(dem_region, []))
            if show_regions & neighbours:
                region_ratio = 0.5
            else:
                region_ratio = 0.0
        # Pénalité de spécificité sur les régions aussi
        region_ratio *= _specificity(len(show_regions), _TOTAL_REGIONS)
    elif not dem_region:
        region_ratio = 0.5
    else:
        region_ratio = 0.0

    total = (spec_ratio * 40 + event_ratio * 25 + lieu_ratio * 20 + region_ratio * 15)

    return {
        "total": round(total, 1),
        "specialites": round(spec_ratio * 100, 1),
        "evenements": round(event_ratio * 100, 1),
        "lieux": round(lieu_ratio * 100, 1),
        "region": round(region_ratio * 100, 1),
        "matching_specs": show_specs & dem_specs,
        "matching_events": show_events & dem_events,
        "matching_lieux": show_lieux & dem_lieux,
    }


def find_matching_shows(demande, all_shows, min_score=1):
    """Return a list of (show, score_dict) sorted by total score desc.

    Only shows with total >= min_score are included.
    """
    results = []
    for show in all_shows:
        score = compute_score(show, demande)
        if score["total"] >= min_score:
            results.append((show, score))
    results.sort(key=lambda x: x[1]["total"], reverse=True)
    return results
