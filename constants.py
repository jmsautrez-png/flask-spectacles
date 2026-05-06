# constants.py — Taxonomies centralisées pour le matching spectacles / appels d'offre
# Chaque dictionnaire : clé = nom de l'accordéon, valeur = liste de choix

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
        # Humour / Personnages
        "Clown",
        "Humoriste et Imitateur",
        "Sosie",
        "Ventriloque",
        "Mascotte",
        # Jeunesse / Famille
        "Père Noël",
        "Conte",
        "Spectacle de Marionnettes",
        # Types de spectacle
        "Spectacle de Rue",
        "Spectacle Médiéval",
        "Spectacle Animalier",
        "Spectacle à Thèmes",
        "Spectacle Événementiel",
        "Spectacle de Cabaret",
        # Cirque / Visuel
        "Cirque",
        "Échassier",
        "Sculpteur de ballons",
        "Caricaturistes et Silhouettiste",
        # Ateliers / Animations
        "Atelier maquillage",
        "Atelier divers",
        # Stands / Fête
        "Manège",
        # Autres
        "Speaker",
    ],
    "Théâtre": [
        # Classique / Sérieux
        "Théâtre classique",
        "Théâtre contemporain",
        "Théâtre d'auteur",
        # Léger / Comique
        "Théâtre de comédie",
        "Théâtre de boulevard",
        "One-man-show",
        # Amateur
        "Théâtre amateur",
        "Théâtre d'improvisation",
        # Musical
        "Comédie musicale",
        # Jeunesse
        "Théâtre pour enfant",
    ],
    "Danse": [
        # Danse de scène
        "Spectacle de danse",
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
    "Musique": [
        # Genres musicaux
        "Chanson française",
        "Variété française",
        "Pop",
        "Rock",
        "Country",
        "Blues",
        "Folk",
        "Jazz",
        "Trio Jazz (Apéro / Cocktail)",
        "Soul",
        "R&B",
        "Rap",
        "Reggae",
        "Musique actuelle",
        "Musique Classique",
        "Musique électronique",
        "Musique / chant traditionnel",
        # Artistes solo
        "Musicien solo",
        "Accordéoniste",
        "Pianiste",
        "Auteur-Interprète",
        "Orgue de Barbarie",
        # Groupes / Ensembles
        "D.J. et Orchestre",
        "Chorale et Gospel",
        "Fanfare et Batucada",
        "Fanfare (Parade de rue / Défilé)",
        "Groupe folklorique",
        # Événements musicaux
        "Concert",
        "Concert pour enfants",
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
        "Fête de village / Fête locale",
        "Carnaval",
        "Halloween / Fête d'Halloween",
        "Fête de fin d'année",
        "Fête de la musique",
        "Bal populaire",
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
# AXE 3 — TYPES DE LIEUX ("Où je peux jouer")
# Utilisé sur : carte spectacle (compagnie) + appel d'offre (mairie)
# ═══════════════════════════════════════════════════════════════════
LIEUX = {
    "Salles municipales": [
        "Salle des fêtes",
        "Salle polyvalente",
        "Salle communale",
        "Salle des associations",
        "Foyer rural",
    ],
    "Salles de spectacle et Culture": [
        "Salle de spectacle équipée",
        "Salle de spectacle non équipée",
        "Théâtre",
        "Café-théâtre",
        "Cabaret",
        "Centre culturel",
        "Auditorium",
        "Bibliothèque / Médiathèque",
        "MJC / Centre social",
        "Musée",
        "Église",
    ],
    "Établissements scolaires": [
        "École maternelle",
        "École primaire",
        "Collège",
        "Lycée",
        "Cour d'école",
        "Préau d'école",
        "Centre de loisirs / Périscolaire",
        "Crèche / Halte-garderie",
    ],
    "Entreprises et Réceptions": [
        "Salle de conférence",
        "Salle de séminaire",
        "Entreprise / Entrepôt",
        "Hôtel (salle événementielle)",
        "Restaurant (salle privée)",
        "Café / Bar",
        "Domaine / Château / Lieu de réception",
        "Château ext/int",
        "Écurie / Château / Maison de maître",
        "Chapiteau / Tente événementielle",
    ],
    "Espaces extérieurs": [
        "Parc / Jardin public",
        "Place du village / Centre-ville",
        "Rue piétonne / Animation de rue",
        "Parvis / Esplanade",
        "Marché couvert / Halles",
        "Parking (événement extérieur)",
        "Gymnase",
        "Stade / Terrain de sport",
    ],
    "Espaces commerciaux": [
        "Centre commercial / Galerie marchande",
        "Parc des expositions",
        "Site de foire / Salon",
        "Camping / Base de loisirs",
    ],
    "Structures spécialisées": [
        "EHPAD / Maison de retraite",
        "Résidence seniors",
        "Salle de réunion",
    ],
}

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
        "requires": ["famille"],  # cocher enfants impose de cocher aussi une option famille
        "exclusive_subs": ["creche"],  # cocher crèche : aucune autre case (cat ou sous-option) ne peut être cochée
        "exclusive_compat": {"creche": ["mat"]},  # crèche peut se cumuler avec maternelle (et dispense aussi de la dépendance famille)
        "sous_options": [
            ("creche", "Crèche / Halte-garderie"),
            ("mat",  "Maternelle"),
            ("elem", "Élémentaire"),
            ("ado",  "Ado (collège / lycée)"),
        ],
    },
    {
        "code": "famille",
        "label": "Spectacle pour la famille (tous spectacles comprenant un public familial : enfants et adultes)",
        "icon": "",
        "single_select": True,  # une seule sous-option (Dès 3 ans OU Dès 6 ans)
        "sous_options": [
            ("fam_3", "Dès 3 ans"),
            ("fam_6", "Dès 6 ans"),
        ],
    },
    {
        "code": "adultes",
        "label": "Spectacle pour les adultes (public adultes seuls)",
        "icon": "",
        "sous_options": [
            ("ad_12", "Dès 12 ans"),
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
        "hint": "Kermesse, fête de quartier, fête de Noël, marché, spectacle / théâtre…",
        "sous_options": [
            ("fam_3", "Dès 3 ans (tout-petits accompagnés)"),
            ("fam_6", "Dès 6 ans (familles avec enfants scolarisés)"),
        ],
    },
    {
        "code": "adultes",
        "label": "Événement adulte (public adultes seuls)",
        "icon": "",
        "hint": "Bal, concert, spectacle / théâtre, soirée CSE, mariage, soirée d'entreprise…",
        "sous_options": [
            ("ad_12", "Dès 12 ans"),
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
