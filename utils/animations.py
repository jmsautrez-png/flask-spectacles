"""Secteur « Animations » : aides partagées par les routes et les templates."""
from constants import ANIMATIONS, normalize_lieux_csv

ANIMATIONS_LABELS = frozenset(label for items in ANIMATIONS.values() for label in items)

MSG_DEMANDE_MIXTE = (
    "Une demande porte soit sur un spectacle, soit sur une animation. "
    "Faites une demande pour chacun : après l'envoi, un bouton reprend vos informations."
)
MSG_FICHE_MIXTE = (
    "Une fiche porte soit sur un spectacle, soit sur une animation (un seul prix « à partir de », "
    "une seule vitrine). Créez une fiche pour chacun : après la publication, un bouton reprend vos informations."
)


def animations_visibles_demandeurs(config, user=None) -> bool:
    """Faut-il montrer l'accordéon Animations côté demandeurs (demande, catalogue) ?

    Ouvert par défaut ; interrupteur de secours ANIMATIONS_OUVERT_DEMANDEURS=0 (config.py,
    variable d'environnement) pour le masquer. L'admin voit toujours le bloc ; côté artistes
    (publication et modification de fiche), il est toujours visible.
    """
    if config.get("ANIMATIONS_OUVERT_DEMANDEURS"):
        return True
    return bool(user is not None and getattr(user, "is_admin", False))


def contains_animation(values) -> bool:
    """True si au moins une des cases données appartient à la liste ANIMATIONS."""
    return any((v or "").strip() in ANIMATIONS_LABELS for v in (values or []))


def sector_of(values) -> str:
    """Secteur d'une demande d'après ses cases : "" (aucune), "animation", "spectacle" ou "mixte".

    Une case absente des deux listes (ancien libellé) compte comme « spectacle ».
    """
    names = [(v or "").strip() for v in (values or []) if (v or "").strip()]
    if not names:
        return ""
    flags = [name in ANIMATIONS_LABELS for name in names]
    if all(flags):
        return "animation"
    if not any(flags):
        return "spectacle"
    return "mixte"


def autre_secteur(values, animations_visibles=True) -> str:
    """Secteur à proposer pour une seconde demande : l'autre que celui des cases données.

    "" si le secteur est indéterminé (aucune case, mélange) ou si le secteur Animations
    n'est pas visible pour le demandeur (interrupteur de secours fermé).
    """
    secteur = sector_of(values)
    if secteur == "spectacle":
        return "animation" if animations_visibles else ""
    if secteur == "animation":
        return "spectacle"
    return ""


def reprise_depuis(demande):
    """Copie jetable (non enregistrée) des informations réutilisables d'une demande déjà envoyée.

    Reprend le contact, le lieu, les dates, la jauge, le public et l'accessibilité ; laisse vides
    ce qui dépend du secteur (cases, budget, intitulé, contraintes techniques). Les valeurs absentes
    deviennent des chaînes vides : le formulaire imprime les valeurs telles quelles (sinon « None »).
    """
    from types import SimpleNamespace

    def texte(valeur):
        return valeur or ""

    return SimpleNamespace(
        id=None,
        structure=texte(demande.structure), civilite=texte(demande.civilite), nom=texte(demande.nom),
        telephone=texte(demande.telephone), contact_email=texte(demande.contact_email),
        lieu_ville=texte(demande.lieu_ville), code_postal=texte(demande.code_postal),
        region=texte(demande.region), departement=texte(demande.departement),
        date_debut=texte(demande.date_debut), date_fin=texte(demande.date_fin),
        dates_horaires=texte(demande.dates_horaires),
        jauge=texte(demande.jauge), age_range=texte(demande.age_range),
        public_categories=texte(demande.public_categories),
        public_sous_options=texte(demande.public_sous_options),
        lieux_souhaites=texte(demande.lieux_souhaites), accessibilite=texte(demande.accessibilite),
        portee_nationale=True if demande.portee_nationale is None else bool(demande.portee_nationale),
        intitule="", specialites_recherchees="", budget="", contraintes="",
    )


def fiche_reprise_depuis(show):
    """Copie jetable (non enregistrée) des informations réutilisables d'une fiche pour en créer une seconde.

    Reprend la raison sociale, le contact, la localisation, les régions et lieux d'intervention et le
    public ; laisse vides ce qui fait la vitrine ou dépend du secteur (titre, description, photos,
    prix, spécialités, intervenants). Les valeurs absentes deviennent des chaînes vides ou des listes vides.
    """
    from types import SimpleNamespace

    def texte(valeur):
        return valeur or ""

    def liste(csv):
        return [v.strip() for v in (csv or "").split(",") if v.strip()]

    return SimpleNamespace(
        titre_source=texte(show.title),
        raison_sociale=texte(show.raison_sociale), contact_email=texte(show.contact_email),
        contact_phone=texte(show.contact_phone), location=texte(show.location),
        code_postal=texte(show.code_postal), region=texte(show.region), departement=texte(show.departement),
        regions=liste(show.regions_intervention),
        lieux=normalize_lieux_csv(show.lieux_intervention),
        public_categories=liste(show.public_categories),
        public_sous_options=liste(show.public_sous_options),
    )
