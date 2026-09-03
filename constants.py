# constants.py — Taxonomies centralisées pour le matching spectacles / appels d'offre
# Chaque dictionnaire : clé = nom de l'accordéon, valeur = liste de choix

# ═══════════════════════════════════════════════════════════════════
# INTERRUPTEUR — Affichage des coordonnées directes sur la fiche spectacle
# Mettre à True pour MASQUER l'email et le site internet (le visiteur passe
# alors par le formulaire « Demander un devis » → boîte Spectacle'ment Vôtre).
# Le téléphone reste affiché. Repasser à False pour tout réafficher à tout moment.
# Aucune donnée n'est supprimée : seul l'affichage est masqué.
# ═══════════════════════════════════════════════════════════════════
MASQUER_COORDONNEES_DIRECTES = True

# ═══════════════════════════════════════════════════════════════════
# AXE 1 — SPÉCIALITÉS ARTISTIQUES ("Ce que je fais")
# Utilisé sur : carte spectacle (compagnie) + appel d'offre (mairie)
# ═══════════════════════════════════════════════════════════════════
SPECIALITES = {
    "Spectacle et Animation": [
        # Magie / Illusion
        "Magie et Magicien",
        "Prestidigitateur",
        "Mentaliste",
        "Close-up",
        # Humour / Personnages
        "Clown",
        "Clown suiveur",
        "Humoriste et Imitateur",
        "Sosie",
        "Ventriloque",
        "Mascotte",
        # Jeunesse / Famille
        "Père Noël",
        "Conteuse Conteur",
        "Conte théâtralisé",
        "Spectacle tiré d'un livre jeunesse",
        "Spectacle burlesque",
        "Spectacle de Marionnettes",
        "Spectacle de Marionnettes contemporaines",
        # Types de spectacle
        "Spectacle d'animation enfant",
        "Spectacle d'animation EHPAD",
        "Spectacle d'animation adulte",
        "Spectacle pour adulte",
        "Spectacle adulte clownesque",
        "Spectacle pour enfant",
        "Spectacle pour la petite enfance",
        "Spectacle enfant avec de la magie",
        "Spectacle enfant avec des chansons",
        "Spectacle enfant avec de la danse",
        "Spectacle enfant avec du cirque",
        "Spectacle enfant clownesque",
        "Spectacle enfant avec de l'épée",
        "Spectacle enfant avec interactivité",
        "Spectacle de Rue",
        "Parade de rue / Déambulation",
        "Spectacle en roulotte",
        "Spectacle Médiéval",
        "Spectacle Animalier",
        "Spectacle à Thèmes",
        "Spectacle écologie et nature",
        "Spectacle champêtre",
        "Spectacle Halloween",
        "Spectacle de Pirate",
        "Spectacle de Cabaret",
        "Numéro Cabaret | Cirque",
        # Cirque / Visuel
        "Cirque",
        "Cirque nouveau",
        "Cracheur de feu",
        "Spectacle de feu",
        "Échassier",
        "Sculpteur de ballons",
        "Caricaturistes et Silhouettiste",
        "Cascadeur",
        # Ateliers / Animations
        "Atelier maquillage",
        "Atelier divers",
        # Stands / Fête
        "Manège",
        # Noël
        "Spectacle thématique de Noël",
        # Autres
        "Speaker",
    ],
    "Théâtre": [
        # Classique / Sérieux
        "Théâtre classique",
        "Théâtre contemporain",
        "Théâtre d'auteur",
        "Théâtre sur tréteaux",
        # Léger / Comique
        "Théâtre de comédie",
        "Théâtre de boulevard",
        "Café-théâtre",
        "One-man-show",
        "Stand-up",
        "Seul en scène",
        # Arts du geste
        "Mime",
        "Travail du masque / Commedia dell'arte",
        # Engagé
        "Théâtre engagé",
        "Conférence gesticulée",
        # Amateur
        "Théâtre amateur",
        "Théâtre d'improvisation",
        "Théâtre participatif",
        # Musical
        "Comédie musicale",
        "Comédie musicale pour enfant",
        # Jeunesse
        "Théâtre pour la famille",
        "Théâtre pour enfant",
        "Spectacle de comptines et de théâtre",
    ],
    "Danse": [
        # Danse de scène
        "Spectacle de danse contemporaine",
        "Spectacle de danse pour enfant",
        "Revue Cabaret et Danse",
        "Danse contemporaine",
        "Danse classique",
        "Danse K-pop (coréen)",
        # Danse traditionnelle
        "Flamenco",
        "Tango",
        "Danse Traditionnelle",
    ],
    # AXE MUSIQUE — STYLE : le genre musical et la formation/effectif
    "Musique — Styles & formations": [
        # Genres musicaux
        "Chanson française",
        "Variété française",
        "Pop",
        "Pop latino",
        "Musique latino",
        "Rock",
        "Country",
        "Blues",
        "Folk",
        "Jazz",
        "Trio Jazz (Apéro / Cocktail)",
        "Musique tzigane / Jazz manouche",
        "Soul",
        "R&B",
        "Rap",
        "Reggae",
        "Musique actuelle",
        "Musique Classique",
        "Musique électronique",
        "Musique / chant traditionnel",
        "Musique traditionnelle africaine",
        "Musique du monde",
        # Artistes solo
        "Musicien solo",
        "Accordéoniste",
        "Pianiste",
        "Auteur-Interprète",
        "Orgue de Barbarie",
        # Groupes / Ensembles
        "Orchestre",
        "DJ",
        "Chorale et Gospel",
        "Fanfare et Batucada",
        "Fanfare (Parade de rue / Défilé)",
        "Groupe folklorique",
    ],
    # AXE MUSIQUE — FORMAT : la forme de la prestation proposée
    "Musique — Formats de prestation": [
        # Concerts
        "Concert",
        "Concert de reprises (covers)",
        "Concert d'auteur-interprète",
        "Concert acoustique / Intimiste",
        "Concert pour enfants",
        # Bals & soirées dansantes
        "Orchestre de bal",
        "Bal grande production",
        "Bal folk / trad",
        "Thé dansant",
        "Soirée dansante / Piste de danse",
        "Animation mariage (cérémonie + soirée)",
        # Ambiance & déambulation
        "Apéro-concert / Cocktail musical",
        "Musique d'ambiance / Lounge",
        "Déambulation musicale",
        # Spectacles musicaux
        "Spectacle Musical",
        "Spectacle Musical pour enfant",
        "Animation Musicale",
        "Tribute",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# AXE 2 — TYPES D'ÉVÉNEMENTS ("Pour quel événement")
# Utilisé sur : carte spectacle (compagnie) + appel d'offre (mairie)
# ═══════════════════════════════════════════════════════════════════
EVENEMENTS = {
    "Fêtes traditionnelles": [
        "Arbre de Noël",
        "Marché de Noël",
        "Fête des aînés",
        "Fête de village / Fête locale",
        "Carnaval",
        "Halloween / Fête d'Halloween",
        "Fête de fin d'année",
        "Fête de la musique",
        "Bal populaire",
        "Thé dansant",
        "Soirée dansante",
        "Soirée à thème",
        "Gala",
    ],
    "Scolaire et Jeunesse": [
        "Kermesse d'école",
        "Spectacle de fin d'année",
        "Anniversaire enfant",
        "Animation estivale",
        "Centre de loisirs / Périscolaire",
        "Crèche / Halte-garderie",
        "Boum pour enfant",
    ],
    "Entreprise": [
        "Comité d'entreprise / CSE",
        "Séminaire d'entreprise",
        "Animation commerciale",
        "Inauguration / Événement officiel",
        "Journée portes ouvertes",
        "Événementiel",
    ],
    "Culture et Festivals": [
        "Festival",
        "Festival de rue",
        "Concert",
        "Théâtre",
        "Animation de rue",
        "Spectacle de rue",
        "Cinéma plein air",
        "Salon du livre / Dédicaces",
        "Programmation culturelle",
    ],
    "Marchés et Foires": [
        "Foire / Salon",
        "Vide-grenier / Brocante",
        "Marché artisanal",
        "Marché nocturne",
        "Fête foraine",
    ],
    "Officiel et Patrimoine": [
        "Vœux du maire",
        "Commémoration officielle",
        "Journée du patrimoine",
        "Remise de prix / Cérémonie",
        "Conférence / Rencontre publique",
    ],
    "Sports et Loisirs": [
        "Journée sportive / Olympiades",
        "Course / Marathon / Trail",
        "Tournoi sportif",
        "Loto / Super loto",
        "Tombola",
    ],
    "Privé et Caritatif": [
        "Mariage",
        "Anniversaire adulte",
        "EVJF / EVG",
        "Collecte caritative / Événement solidaire",
        "Téléthon / Événement humanitaire",
        "Fête des associations",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# AXE 3 — TYPES DE LIEUX ("Où je peux jouer")  —  version simplifiée (5 choix)
# Utilisé sur : carte spectacle (compagnie) + appel d'offre (mairie)
# Objectif : ne garder que l'essentiel pour ne pas encombrer les formulaires.
#   • Tout terrain                     → joue partout (matche tous les lieux)
#   • Extérieur                        → plein air (place, parc, rue, cour…)
#   • Salle équipée                    → scène + son & lumière fournis (théâtre, auditorium…)
#   • Salle de classe ou équivalent    → petite salle (classe, réunion, séminaire, crèche…)
#   • Salle des fêtes non équipée      → grande salle polyvalente sans matériel scénique
# ═══════════════════════════════════════════════════════════════════
LIEU_EXTERIEUR = "Extérieur"
LIEU_SALLE_EQUIPEE = "Salle équipée"
LIEU_SALLE_CLASSE = "Salle de classe ou équivalent"
LIEU_SALLE_FETES = "Salle des fêtes non équipée"
LIEU_TOUT_TERRAIN = "Tout terrain"

LIEUX = {
    "Terrain de jeu proposé": [
        LIEU_TOUT_TERRAIN,
        LIEU_EXTERIEUR,
        LIEU_SALLE_EQUIPEE,
        LIEU_SALLE_CLASSE,
        LIEU_SALLE_FETES,
    ],
}

# Version organisateur (côté demande) : SANS « Tout terrain ».
# L'organisateur propose un espace précis à disposition — il ne « joue pas
# partout ». « Tout terrain » reste réservé aux artistes (LIEUX ci-dessus).
LIEUX_ORGANISATEUR = {
    "Terrain de jeu proposé": [
        LIEU_EXTERIEUR,
        LIEU_SALLE_EQUIPEE,
        LIEU_SALLE_CLASSE,
        LIEU_SALLE_FETES,
    ],
}

# Conversion automatique des anciens libellés (avant simplification) vers les
# 4 nouveaux buckets. Permet de ne PAS perdre les choix déjà saisis par les
# artistes / organisateurs : la normalisation est appliquée au matching et à
# l'affichage des formulaires. Clés en minuscules.
_LIEUX_LEGACY_MAP = {
    # → Extérieur
    "cour d'école": LIEU_EXTERIEUR,
    "parc / jardin public": LIEU_EXTERIEUR,
    "place du village / centre-ville": LIEU_EXTERIEUR,
    "rue piétonne / animation de rue": LIEU_EXTERIEUR,
    "parvis / esplanade": LIEU_EXTERIEUR,
    "parking (événement extérieur)": LIEU_EXTERIEUR,
    "stade / terrain de sport": LIEU_EXTERIEUR,
    "camping / base de loisirs": LIEU_EXTERIEUR,
    # → Salle équipée (scène + son & lumière)
    "salle de spectacle équipée": LIEU_SALLE_EQUIPEE,
    "salle équipée": LIEU_SALLE_EQUIPEE,
    "théâtre": LIEU_SALLE_EQUIPEE,
    "café-théâtre": LIEU_SALLE_EQUIPEE,
    "cabaret": LIEU_SALLE_EQUIPEE,
    "centre culturel": LIEU_SALLE_EQUIPEE,
    "auditorium": LIEU_SALLE_EQUIPEE,
    # → Salle de classe ou équivalent (petites salles)
    "école maternelle": LIEU_SALLE_CLASSE,
    "école primaire": LIEU_SALLE_CLASSE,
    "collège": LIEU_SALLE_CLASSE,
    "lycée": LIEU_SALLE_CLASSE,
    "préau d'école": LIEU_SALLE_CLASSE,
    "centre de loisirs / périscolaire": LIEU_SALLE_CLASSE,
    "crèche / halte-garderie": LIEU_SALLE_CLASSE,
    "salle de conférence": LIEU_SALLE_CLASSE,
    "salle de séminaire": LIEU_SALLE_CLASSE,
    "salle de réunion": LIEU_SALLE_CLASSE,
    "bibliothèque / médiathèque": LIEU_SALLE_CLASSE,
    "mjc / centre social": LIEU_SALLE_CLASSE,
    "musée": LIEU_SALLE_CLASSE,
    # → Salle des fêtes non équipée (grandes salles polyvalentes sans matériel)
    "salle des fêtes": LIEU_SALLE_FETES,
    "salle polyvalente": LIEU_SALLE_FETES,
    "salle communale": LIEU_SALLE_FETES,
    "salle des associations": LIEU_SALLE_FETES,
    "foyer rural": LIEU_SALLE_FETES,
    "salle de spectacle non équipée": LIEU_SALLE_FETES,
    "église": LIEU_SALLE_FETES,
    "entreprise / entrepôt": LIEU_SALLE_FETES,
    "hôtel (salle événementielle)": LIEU_SALLE_FETES,
    "restaurant (salle privée)": LIEU_SALLE_FETES,
    "café / bar": LIEU_SALLE_FETES,
    "domaine / château / lieu de réception": LIEU_SALLE_FETES,
    "château ext/int": LIEU_SALLE_FETES,
    "écurie / château / maison de maître": LIEU_SALLE_FETES,
    "chapiteau / tente événementielle": LIEU_SALLE_FETES,
    "marché couvert / halles": LIEU_SALLE_FETES,
    "gymnase": LIEU_SALLE_FETES,
    "centre commercial / galerie marchande": LIEU_SALLE_FETES,
    "parc des expositions": LIEU_SALLE_FETES,
    "site de foire / salon": LIEU_SALLE_FETES,
    "ehpad / maison de retraite": LIEU_SALLE_FETES,
    "résidence seniors": LIEU_SALLE_FETES,
    # ancien bucket intermédiaire → salle des fêtes non équipée
    "salle simple / polyvalente": LIEU_SALLE_FETES,
}

# Libellés « nouveaux » (déjà normalisés) : lookup case-insensitive.
_LIEUX_NEW_LOWER = {b.lower(): b for group in LIEUX.values() for b in group}


def normalize_lieu(value):
    """Convertit un libellé de lieu (ancien ou nouveau) vers l'un des 4 buckets.

    Retourne None si la valeur est vide. Les valeurs inconnues retombent sur
    « Salle des fêtes non équipée » (le cas couvert générique le plus fréquent).
    """
    if not value:
        return None
    v = value.strip().lower()
    if not v:
        return None
    if v in _LIEUX_NEW_LOWER:
        return _LIEUX_NEW_LOWER[v]
    return _LIEUX_LEGACY_MAP.get(v, LIEU_SALLE_FETES)


def normalize_lieux_list(values):
    """Normalise une liste de libellés → liste de buckets uniques (ordre stable)."""
    out = []
    for val in values or []:
        bucket = normalize_lieu(val)
        if bucket and bucket not in out:
            out.append(bucket)
    return out


def normalize_lieux_csv(csv_value):
    """Normalise une chaîne CSV de lieux → liste de buckets uniques."""
    if not csv_value:
        return []
    return normalize_lieux_list(csv_value.split(","))

# ═══════════════════════════════════════════════════════════════════
# RÉGIONS — pour le multi-sélection d'intervention
# ═══════════════════════════════════════════════════════════════════
REGIONS_FRANCE = [
    "Auvergne-Rhône-Alpes",
    "Bourgogne-Franche-Comté",
    "Bretagne",
    "Centre-Val de Loire",
    "Corse",
    "Grand Est",
    "Hauts-de-France",
    "Île-de-France",
    "Normandie",
    "Nouvelle-Aquitaine",
    "Occitanie",
    "Pays de la Loire",
    "Provence-Alpes-Côte d'Azur",
    "Guadeloupe",
    "Guyane",
    "La Réunion",
    "Martinique",
    "Mayotte",
]

REGIONS_VOISINES = {
    "Auvergne-Rhône-Alpes": ["Bourgogne-Franche-Comté", "Île-de-France", "Occitanie", "Provence-Alpes-Côte d'Azur", "Nouvelle-Aquitaine"],
    "Bourgogne-Franche-Comté": ["Auvergne-Rhône-Alpes", "Grand Est", "Île-de-France", "Centre-Val de Loire"],
    "Bretagne": ["Pays de la Loire", "Normandie"],
    "Centre-Val de Loire": ["Île-de-France", "Bourgogne-Franche-Comté", "Pays de la Loire", "Nouvelle-Aquitaine", "Normandie"],
    "Corse": ["Provence-Alpes-Côte d'Azur"],
    "Grand Est": ["Bourgogne-Franche-Comté", "Île-de-France", "Hauts-de-France"],
    "Hauts-de-France": ["Île-de-France", "Grand Est", "Normandie"],
    "Île-de-France": ["Hauts-de-France", "Grand Est", "Bourgogne-Franche-Comté", "Centre-Val de Loire", "Normandie"],
    "Normandie": ["Bretagne", "Pays de la Loire", "Centre-Val de Loire", "Île-de-France", "Hauts-de-France"],
    "Nouvelle-Aquitaine": ["Pays de la Loire", "Centre-Val de Loire", "Auvergne-Rhône-Alpes", "Occitanie"],
    "Occitanie": ["Nouvelle-Aquitaine", "Auvergne-Rhône-Alpes", "Provence-Alpes-Côte d'Azur"],
    "Pays de la Loire": ["Bretagne", "Normandie", "Centre-Val de Loire", "Nouvelle-Aquitaine"],
    "Provence-Alpes-Côte d'Azur": ["Auvergne-Rhône-Alpes", "Occitanie", "Corse"],
}

# ═══════════════════════════════════════════════════════════════════
# AXE 4 — PUBLIC CIBLE (1 case obligatoire à cocher)
# Utilisé sur : carte spectacle + demande d'animation + filtre catalogue
# ═══════════════════════════════════════════════════════════════════
PUBLICS = [
    ("jp_0_3",   "Jeune public ou familial 0/3 ans"),
    ("jp_4_8",   "Jeune public ou familial 4/8 ans"),
    ("jp_7_11",  "Jeune public ou familial 7/11 ans"),
    ("jp_des_3", "Jeune public ou familial dès 3 ans"),
    ("anim_div", "Animations diverses"),
    ("ad_12",    "Spectacle adulte à partir de 12 ans"),
    ("ad_16",    "Spectacle adulte à partir de 16 ans"),
]

# Détail / exemples affichés en tooltip pour certaines catégories
PUBLICS_TOOLTIPS = {
    "anim_div": "Inclut : parade de rue, apéro concert, bal, concert, atelier",
}

# Mapping pour rétrocompatibilité (anciennes valeurs → libellé d'affichage)
PUBLICS_LEGACY_LABELS = {
    "enfant":       "Enfant (ancien format)",
    "enfant_2_6":   "Enfant 2/6 ans (ancien format)",
    "enfant_5_10":  "Enfant 5/10 ans (ancien format)",
    "enfants_2_10": "Enfants 2/10 ans (ancien format)",
    "familial":     "Familial (ancien format)",
    "tout public":  "Tout public (ancien format)",
    "adulte":       "Adulte (ancien format)",
    "fam_2":        "Toute la famille à partir de 2 ans (ancien format)",
    "fam_3":        "Familial à partir de 3 ans (ancien format)",
    "fam_8":        "Familial à partir de 8 ans (ancien format)",
    "jp_8_11":      "Jeune public 5/11 ans (ancien format)",
}


# ═══════════════════════════════════════════════════════════════════
# AXE 4-bis — PUBLIC CIBLE v2 (catégories + sous-options) — pour matching
# Côté ARTISTE : 1 ou plusieurs catégories, avec règle d'incompatibilité
#   - "enfants" et "adultes" sont mutuellement exclusifs
#   - "famille" peut se cumuler avec "enfants" OU "adultes"
# Sous-options : multi-sélection à l'intérieur d'une catégorie
# ═══════════════════════════════════════════════════════════════════
PUBLIC_CIBLE_CATEGORIES = [
    {
        "code": "enfants",
        "label": "Spectacle pour enfants (public d'enfants seuls)",
        "icon": "",
        # Pas de "requires" : l'artiste peut cocher uniquement "enfants" (Maternelle/Élémentaire/Ado)
        # sans être obligé de cocher aussi "famille".
        "exclusive_subs": ["creche"],  # cocher crèche : aucune autre case (cat ou sous-option) ne peut être cochée
        "exclusive_compat": {"creche": ["mat", "fam_pe"]},  # crèche peut se cumuler avec maternelle ET avec famille petite enfance
        "sous_options": [
            ("creche", "Crèche / Halte-garderie"),
            ("mat",  "Maternelle"),
            ("elem", "Élémentaire"),
            ("ado",  "Ado (collège / lycée)"),
        ],
    },
    {
        "code": "famille",
        "label": "Spectacle ou événement pour la famille (tous événements comprenant un public familial : enfants et adultes — concert, atelier, spectacle de rue, carnaval, parade, défilé, etc.)",
        "icon": "",
        "single_select": True,  # une seule sous-option (Petite enfance OU Dès 3 ans OU Dès 6 ans)
        "sub_requires": {"fam_pe": "creche"},  # « petite enfance » n'est cochable que si la sous-option « crèche » est aussi cochée
        "sous_options": [
            ("fam_pe", "Petite enfance (0-3 ans accompagnés)"),
            ("fam_3", "Dès 3 ans"),
            ("fam_6", "Dès 6 ans"),
            ("fam_8", "Dès 8 ans"),
            ("fam_10", "Dès 10 ans"),
            ("fam_12", "Dès 12 ans"),
            ("fam_16", "Dès 16 ans"),
        ],
    },
    {
        "code": "adultes",
        "label": "Spectacle pour les adultes (public adultes seuls, dès 16 ans)",
        "icon": "",
        "sous_options": [
            ("ad_16", "Dès 16 ans"),
        ],
    },
]

# Côté MAIRIE / ORGANISATEUR : vocabulaire « événement »
# Mapping : catégorie organisateur → catégorie artiste correspondante
PUBLIC_CIBLE_ORGANISATEUR = [
    {
        "code": "enfants",  # même code que côté artiste pour matching direct
        "label": "Événement scolaire / pour enfants (public d'enfants seuls)",
        "icon": "",
        "hint": "Spectacle, animation, atelier",
        "exclusive_subs": ["creche"],
        "exclusive_compat": {"creche": ["mat", "fam_pe"]},
        "sous_options": [
            ("creche", "Crèche / Halte-garderie"),
            ("mat",  "Maternelle"),
            ("elem", "Élémentaire"),
            ("ado",  "Collège / Lycée"),
        ],
    },
    {
        "code": "famille",
        "label": "Événement public / familial (enfants et adultes ensemble)",
        "icon": "",
        "hint": "Kermesse, fête de quartier, fête de Noël, marché, concert, spectacle / théâtre, parade, défilé, spectacle de rue…",
        "single_select": True,
        "sub_requires": {"fam_pe": "creche"},
        "sous_options": [
            ("fam_pe", "Petite enfance (0-3 ans accompagnés)"),
            ("fam_3", "Dès 3 ans (tout-petits accompagnés)"),
            ("fam_6", "Dès 6 ans (familles avec enfants scolarisés)"),
            ("fam_8", "Dès 8 ans"),
            ("fam_10", "Dès 10 ans"),
            ("fam_12", "Dès 12 ans"),
            ("fam_16", "Dès 16 ans"),
        ],
    },
    {
        "code": "adultes",
        "label": "Événement adulte (public adultes seuls, dès 16 ans)",
        "icon": "",
        "hint": "Bal, concert, spectacle / théâtre, soirée CSE, mariage, soirée d'entreprise…",
        "sous_options": [
            ("ad_16", "Dès 16 ans (contenu adulte)"),
        ],
    },
]

# Codes valides (pour validation backend)
PUBLIC_CIBLE_CODES_VALIDES = {
    cat["code"]: [opt[0] for opt in cat["sous_options"]]
    for cat in PUBLIC_CIBLE_CATEGORIES
}

# Catégories incompatibles entre elles
# Format : (cat_a, cat_b, [bypass_cats])  (bypass = [] : strict, aucune exception)
#   - famille ↔ adultes : bloqué (famille couvre déjà le public adulte mixte)
#   - enfants ↔ adultes : bloqué (deux publics purs séparés = incohérent, utiliser « famille »)
PUBLIC_CIBLE_INCOMPATIBLES = [
    ("enfants", "adultes", []),
    ("famille", "adultes", []),
]

# Version PERMISSIVE pour l'admin : aucune contrainte (single_select, exclusive_subs,
# exclusive_compat, sub_requires, requires) — l'admin peut tout cocher librement.
PUBLIC_CIBLE_ADMIN = [
    {k: v for k, v in cat.items()
     if k not in ("single_select", "exclusive_subs", "exclusive_compat",
                  "sub_requires", "requires")}
    for cat in PUBLIC_CIBLE_ORGANISATEUR
]

# Structures spécialisées (exemple)
STRUCTURES_SPECIALISEES = [
    ("ehpad", "EHPAD / Résidence senior"),
    ("ime", "IME / Institut médico-éducatif"),
    ("foyer", "Foyer de vie / MAS"),
    ("hopital", "Hôpital spécialisé"),
]

# ═══════════════════════════════════════════════════════════════════
# LABELS QUALITÉ — réservés à l'admin (jusqu'à 2 par spectacle)
# Stockés en CSV dans Show.labels (codes séparés par des virgules)
# Affichés en badge public + bonus de score (matching)
#
# Les labels « qualité » (premium, incontournable, pro_verifie, coup_de_coeur)
# valorisent le spectacle et donnent un bonus de matching.
# Le label « neutre » (edition_libre) est purement informatif : il signale que
# le spectacle est publié en accès libre, HORS sélection Spectacle'ment.
# Il n'apporte AUCUN bonus de matching et s'affiche en gris.
# ═══════════════════════════════════════════════════════════════════
LABELS_QUALITE = [
    ("premium",        "💎 Premium"),
    ("incontournable", "🌟 Incontournable"),
    ("pro_verifie",    "🛡️ Cie Pro"),
    ("coup_de_coeur",  "💜 Coup de cœur"),
    ("jeune_public",   "🧒 Spécialiste JP"),
    ("edition_libre",  "📖 Édition libre"),
]

# Labels neutres : informatifs, sans bonus de matching, style gris
LABELS_QUALITE_NEUTRES = {"edition_libre"}

# Codes valides (pour validation backend)
LABELS_QUALITE_CODES = {code for code, _ in LABELS_QUALITE}

# Mapping code → libellé d'affichage (avec emoji)
LABELS_QUALITE_LABELS = dict(LABELS_QUALITE)

# Mapping code → description (infobulle affichée au survol du badge)
LABELS_QUALITE_DESCRIPTIONS = {
    "premium":        "Spectacle d'exception, sélectionné et mis en avant par Spectacle'ment pour sa qualité remarquable.",
    "incontournable": "Une valeur sûre plébiscitée par les organisateurs : un spectacle à ne pas manquer.",
    "pro_verifie":    "Compagnie professionnelle dont la qualité a été approuvée par Spectacle'ment Vôtre.",
    "coup_de_coeur":  "Le coup de cœur de l'équipe Spectacle'ment : un spectacle que nous avons particulièrement apprécié.",
    "jeune_public":   "Compagnie professionnelle spécialisée dans les spectacles pour le jeune public (crèches, écoles, familles).",
    "edition_libre":  "Cette compagnie publie sa fiche en accès libre. Nos équipes n'ont pas encore eu l'occasion d'en apprécier le parcours.",
}
