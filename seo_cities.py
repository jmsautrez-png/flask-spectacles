# Liste des grandes villes françaises pour le SEO géolocalisé
# Format: {"name": "Nom de la ville", "slug": "slug-url", "region": "Région", "department": "XX"}

FRENCH_CITIES = [
    # Grandes métropoles (300k+ habitants)
    {"name": "Paris", "slug": "paris", "region": "Île-de-France", "department": "75"},
    {"name": "Marseille", "slug": "marseille", "region": "Provence-Alpes-Côte d'Azur", "department": "13"},
    {"name": "Lyon", "slug": "lyon", "region": "Auvergne-Rhône-Alpes", "department": "69"},
    {"name": "Toulouse", "slug": "toulouse", "region": "Occitanie", "department": "31"},
    {"name": "Nice", "slug": "nice", "region": "Provence-Alpes-Côte d'Azur", "department": "06"},
    {"name": "Nantes", "slug": "nantes", "region": "Pays de la Loire", "department": "44"},
    {"name": "Montpellier", "slug": "montpellier", "region": "Occitanie", "department": "34"},
    {"name": "Strasbourg", "slug": "strasbourg", "region": "Grand Est", "department": "67"},
    {"name": "Bordeaux", "slug": "bordeaux", "region": "Nouvelle-Aquitaine", "department": "33"},
    {"name": "Lille", "slug": "lille", "region": "Hauts-de-France", "department": "59"},
    {"name": "Rennes", "slug": "rennes", "region": "Bretagne", "department": "35"},
    {"name": "Reims", "slug": "reims", "region": "Grand Est", "department": "51"},
    {"name": "Saint-Étienne", "slug": "saint-etienne", "region": "Auvergne-Rhône-Alpes", "department": "42"},
    {"name": "Le Havre", "slug": "le-havre", "region": "Normandie", "department": "76"},
    {"name": "Toulon", "slug": "toulon", "region": "Provence-Alpes-Côte d'Azur", "department": "83"},
    {"name": "Grenoble", "slug": "grenoble", "region": "Auvergne-Rhône-Alpes", "department": "38"},
    {"name": "Dijon", "slug": "dijon", "region": "Bourgogne-Franche-Comté", "department": "21"},
    {"name": "Angers", "slug": "angers", "region": "Pays de la Loire", "department": "49"},
    {"name": "Nîmes", "slug": "nimes", "region": "Occitanie", "department": "30"},
    {"name": "Villeurbanne", "slug": "villeurbanne", "region": "Auvergne-Rhône-Alpes", "department": "69"},
    {"name": "Clermont-Ferrand", "slug": "clermont-ferrand", "region": "Auvergne-Rhône-Alpes", "department": "63"},
    {"name": "Aix-en-Provence", "slug": "aix-en-provence", "region": "Provence-Alpes-Côte d'Azur", "department": "13"},
    
    # Villes moyennes (100k-300k habitants)
    {"name": "Le Mans", "slug": "le-mans", "region": "Pays de la Loire", "department": "72"},
    {"name": "Brest", "slug": "brest", "region": "Bretagne", "department": "29"},
    {"name": "Tours", "slug": "tours", "region": "Centre-Val de Loire", "department": "37"},
    {"name": "Amiens", "slug": "amiens", "region": "Hauts-de-France", "department": "80"},
    {"name": "Limoges", "slug": "limoges", "region": "Nouvelle-Aquitaine", "department": "87"},
    {"name": "Annecy", "slug": "annecy", "region": "Auvergne-Rhône-Alpes", "department": "74"},
    {"name": "Perpignan", "slug": "perpignan", "region": "Occitanie", "department": "66"},
    {"name": "Metz", "slug": "metz", "region": "Grand Est", "department": "57"},
    {"name": "Besançon", "slug": "besancon", "region": "Bourgogne-Franche-Comté", "department": "25"},
    {"name": "Orléans", "slug": "orleans", "region": "Centre-Val de Loire", "department": "45"},
    {"name": "Rouen", "slug": "rouen", "region": "Normandie", "department": "76"},
    {"name": "Mulhouse", "slug": "mulhouse", "region": "Grand Est", "department": "68"},
    {"name": "Caen", "slug": "caen", "region": "Normandie", "department": "14"},
    {"name": "Saint-Denis", "slug": "saint-denis", "region": "Île-de-France", "department": "93"},
    {"name": "Nancy", "slug": "nancy", "region": "Grand Est", "department": "54"},
    {"name": "Argenteuil", "slug": "argenteuil", "region": "Île-de-France", "department": "95"},
    {"name": "Montreuil", "slug": "montreuil", "region": "Île-de-France", "department": "93"},
    {"name": "Roubaix", "slug": "roubaix", "region": "Hauts-de-France", "department": "59"},
    {"name": "Tourcoing", "slug": "tourcoing", "region": "Hauts-de-France", "department": "59"},
    {"name": "Nanterre", "slug": "nanterre", "region": "Île-de-France", "department": "92"},
    {"name": "Vitry-sur-Seine", "slug": "vitry-sur-seine", "region": "Île-de-France", "department": "94"},
    {"name": "Avignon", "slug": "avignon", "region": "Provence-Alpes-Côte d'Azur", "department": "84"},
    {"name": "Créteil", "slug": "creteil", "region": "Île-de-France", "department": "94"},
    {"name": "Poitiers", "slug": "poitiers", "region": "Nouvelle-Aquitaine", "department": "86"},
    {"name": "Pau", "slug": "pau", "region": "Nouvelle-Aquitaine", "department": "64"},
    {"name": "La Rochelle", "slug": "la-rochelle", "region": "Nouvelle-Aquitaine", "department": "17"},
    {"name": "Calais", "slug": "calais", "region": "Hauts-de-France", "department": "62"},
    {"name": "Cannes", "slug": "cannes", "region": "Provence-Alpes-Côte d'Azur", "department": "06"},
    {"name": "Versailles", "slug": "versailles", "region": "Île-de-France", "department": "78"},
    {"name": "Troyes", "slug": "troyes", "region": "Grand Est", "department": "10"},
]


def get_city_by_slug(slug: str) -> dict | None:
    """
    Récupère les informations d'une ville par son slug URL.
    
    Args:
        slug (str): Le slug de la ville (ex: "toulouse", "paris")
    
    Returns:
        dict | None: Les données de la ville ou None si non trouvée
    """
    for city in FRENCH_CITIES:
        if city["slug"] == slug:
            return city
    return None


def get_all_city_slugs() -> list[str]:
    """
    Retourne la liste de tous les slugs de villes disponibles.
    
    Returns:
        list[str]: Liste des slugs (ex: ["paris", "toulouse", "lyon", ...])
    """
    return [city["slug"] for city in FRENCH_CITIES]


def get_neighbor_cities(city: dict, limit: int = 6) -> list[dict]:
    """
    Retourne les villes voisines (même région), en excluant la ville donnée.
    Utile pour le maillage interne SEO.
    """
    if not city:
        return []
    region = city.get("region")
    slug = city.get("slug")
    return [
        c for c in FRENCH_CITIES
        if c.get("region") == region and c.get("slug") != slug
    ][:limit]


# ---------------------------------------------------------------
# Données SEO enrichies par ville (pour éviter le contenu dupliqué)
# ---------------------------------------------------------------
# Chaque ville peut avoir des informations spécifiques utilisées
# dans les paragraphes SEO afin de rendre chaque page unique.
CITY_SEO_DATA = {
    "paris": {
        "tagline": "capitale française et plus grande métropole culturelle du pays",
        "venues": "salles parisiennes, théâtres privés, comités d'entreprise du CAC 40, mairies d'arrondissement",
        "events": "Fête de la Musique, Nuit Blanche, fêtes de quartier, arbres de Noël d'entreprise",
    },
    "marseille": {
        "tagline": "cité phocéenne, deuxième ville de France",
        "venues": "MPCA, salles municipales, CSE portuaires et industriels",
        "events": "Marsatac, Festival de Marseille, animations estivales sur le Vieux-Port",
    },
    "lyon": {
        "tagline": "capitale des Gaules, troisième aire urbaine de France",
        "venues": "salles de la Part-Dieu, Confluence, théâtres lyonnais, écoles privées",
        "events": "Fête des Lumières, Nuits Sonores, marchés de Noël",
    },
    "toulouse": {
        "tagline": "ville rose, métropole d'Occitanie",
        "venues": "Zénith, salles municipales, CE d'Airbus et de l'aéronautique",
        "events": "Rio Loco, Festival Occitania, animations enfants au Capitole",
    },
    "nice": {
        "tagline": "perle de la Côte d'Azur",
        "venues": "Palais Nikaïa, hôtels de la Promenade, mairies de la Métropole",
        "events": "Carnaval de Nice, Nice Jazz Festival, animations estivales",
    },
    "nantes": {
        "tagline": "métropole de Loire-Atlantique au riche patrimoine",
        "venues": "Cité des Congrès, salles municipales, CSE de Saint-Nazaire et alentours",
        "events": "Voyage à Nantes, Folle Journée, animations de Noël",
    },
    "bordeaux": {
        "tagline": "capitale de la Nouvelle-Aquitaine, classée au patrimoine mondial",
        "venues": "Palais des Congrès, salles de quartier, châteaux du Médoc pour événements privés",
        "events": "Bordeaux Fête le Vin, FAB, marchés de Noël place Pey-Berland",
    },
    "lille": {
        "tagline": "capitale des Flandres, cœur de la métropole européenne",
        "venues": "Grand Palais, Zénith Arena, salles communales du Nord",
        "events": "Braderie de Lille, lille3000, marchés de Noël",
    },
    "strasbourg": {
        "tagline": "capitale européenne et alsacienne",
        "venues": "Zénith, Palais des Congrès, salles municipales, écoles bilingues",
        "events": "Marché de Noël de Strasbourg, Festival Musica, fêtes de quartier",
    },
    "rennes": {
        "tagline": "capitale de la Bretagne, ville étudiante dynamique",
        "venues": "Couvent des Jacobins, salles municipales, CSE rennais",
        "events": "Trans Musicales, Tombées de la Nuit, fêtes celtiques",
    },
    "montpellier": {
        "tagline": "métropole méditerranéenne, ville étudiante du Sud",
        "venues": "Corum, Zénith Sud, salles de quartier",
        "events": "Festival Radio France, Comédie du Livre, animations Place de la Comédie",
    },
}


def get_city_seo_data(city: dict) -> dict:
    """
    Retourne les informations SEO enrichies pour une ville.
    Si la ville n'a pas de données spécifiques, renvoie un fallback générique
    construit à partir de la région et du département.
    """
    if not city:
        return {}
    slug = city.get("slug", "")
    if slug in CITY_SEO_DATA:
        return CITY_SEO_DATA[slug]
    # Fallback automatique : reste varié grâce à region + département
    return {
        "tagline": f"ville du département {city.get('department', '')} en {city.get('region', '')}",
        "venues": f"salles municipales, écoles, CSE et associations de {city.get('name', '')} et alentours",
        "events": f"animations communales, fêtes de quartier, événements privés en {city.get('region', '')}",
    }


# ---------------------------------------------------------------
# Données SEO enrichies par catégorie / thème de spectacle
# Permet de générer un contenu unique par page ville×catégorie
# ---------------------------------------------------------------
CATEGORY_SEO_DATA = {
    "magie": {
        "intro": "spectacle de magie et d'illusion, alliant prestidigitation, mentalisme et numéros visuels",
        "occasions": "anniversaires d'enfants, arbres de Noël, séminaires d'entreprise, mariages, animations commerciales",
        "audience": "tous publics, particulièrement apprécié des enfants à partir de 4 ans et des adultes amateurs de mystère",
        "duration": "30 à 90 minutes selon le format (close-up, salon ou grande scène)",
    },
    "marionnette": {
        "intro": "spectacle de marionnettes (à fils, à gaine, géantes ou de table)",
        "occasions": "écoles maternelles et primaires, crèches, médiathèques, fêtes de quartier, anniversaires",
        "audience": "très jeunes enfants (2-8 ans) et familles",
        "duration": "30 à 50 minutes en moyenne",
    },
    "clown": {
        "intro": "spectacle de clown et d'humour visuel, mêlant gags, jonglerie et interaction avec le public",
        "occasions": "anniversaires, kermesses, hôpitaux pédiatriques, EHPAD, fêtes de village",
        "audience": "enfants de 3 à 12 ans, familles, public hospitalier",
        "duration": "30 à 60 minutes",
    },
    "theatre": {
        "intro": "pièce de théâtre (classique, contemporaine, comédie, boulevard ou jeune public)",
        "occasions": "salles communales, médiathèques, lycées, comités d'entreprise, festivals locaux",
        "audience": "tous publics selon la pièce, du jeune public à la programmation adulte",
        "duration": "60 à 120 minutes selon la création",
    },
    "danse": {
        "intro": "spectacle de danse (contemporaine, classique, traditionnelle ou cabaret)",
        "occasions": "galas, festivals, animations municipales, événements d'entreprise",
        "audience": "tous publics, programmable selon le style choisi",
        "duration": "45 à 90 minutes",
    },
    "cirque": {
        "intro": "spectacle de cirque alliant acrobatie, jonglerie, équilibre et numéros aériens",
        "occasions": "fêtes de village, grands événements municipaux, festivals, anniversaires en plein air",
        "audience": "familles, enfants, tous âges",
        "duration": "45 à 90 minutes",
    },
    "concert": {
        "intro": "concert live (musiques actuelles, jazz, classique, chanson française, etc.)",
        "occasions": "soirées privées, mariages, festivals, comités d'entreprise, animations municipales",
        "audience": "selon le style musical, du jeune public aux mélomanes adultes",
        "duration": "60 à 180 minutes (sets ou showcase)",
    },
    "atelier": {
        "intro": "atelier d'animation participative (maquillage, création, sculpture sur ballon, magie, etc.)",
        "occasions": "écoles, centres de loisirs, anniversaires, animations commerciales",
        "audience": "enfants principalement, déclinable adultes",
        "duration": "1 à 3 heures avec rotation des participants",
    },
    "spectacle-de-rue": {
        "intro": "spectacle de rue, déambulatoire ou en représentation fixe en plein air",
        "occasions": "festivals, fêtes de village, marchés de Noël, inaugurations, ouvertures de festival",
        "audience": "tout public, passants",
        "duration": "20 à 60 minutes en boucle ou unique",
    },
    "spectacle-enfant": {
        "intro": "spectacle conçu spécialement pour le jeune public (3-12 ans)",
        "occasions": "écoles, crèches, centres de loisirs, anniversaires, arbres de Noël",
        "audience": "enfants de 3 à 12 ans selon le format",
        "duration": "30 à 50 minutes",
    },
    "enfant": {
        "intro": "spectacle pour enfants (théâtre, musique, conte, magie, marionnettes…)",
        "occasions": "écoles, crèches, centres de loisirs, anniversaires, arbres de Noël",
        "audience": "enfants de 3 à 12 ans selon le format",
        "duration": "30 à 50 minutes",
    },
    "arbre-de-noel": {
        "intro": "spectacle d'arbre de Noël adapté aux comités d'entreprise, mairies et associations",
        "occasions": "arbres de Noël CSE, mairies, écoles, marchés de Noël",
        "audience": "enfants des salariés et des administrés (3-10 ans typiquement)",
        "duration": "45 à 60 minutes, souvent suivis du goûter et du Père Noël",
    },
    "animation-ecole": {
        "intro": "animation pédagogique et artistique adaptée au cadre scolaire",
        "occasions": "écoles maternelles, primaires, collèges, fêtes de fin d'année, semaines thématiques",
        "audience": "élèves de la maternelle au collège",
        "duration": "45 minutes en moyenne (format scolaire)",
    },
    "fete-de-village": {
        "intro": "spectacle pour fête de village, fête patronale ou kermesse municipale",
        "occasions": "fêtes communales, 14 juillet, fêtes patronales, marchés de Noël",
        "audience": "tout public, familial",
        "duration": "45 à 90 minutes",
    },
    "orchestre": {
        "intro": "orchestre ou ensemble musical pour bal, concert ou cérémonie",
        "occasions": "bals, mariages, cérémonies officielles, soirées dansantes",
        "audience": "tout public, particulièrement plébiscité par les seniors et les amateurs de bal",
        "duration": "2 à 4 heures (set complet de bal)",
    },
    "rue": {
        "intro": "spectacle ou animation de rue en extérieur",
        "occasions": "festivals, fêtes de village, marchés de Noël, animations commerciales",
        "audience": "tout public, passants",
        "duration": "20 à 60 minutes",
    },
    # Nouveaux thèmes longue traîne
    "conte": {
        "intro": "spectacle de contes (traditionnels, musicaux, illustrés ou interactifs)",
        "occasions": "médiathèques, écoles, centres de loisirs, festivals jeune public, EHPAD",
        "audience": "enfants à partir de 3 ans, familles, public adulte selon le répertoire",
        "duration": "30 à 60 minutes",
    },
    "conteur": {
        "intro": "intervention d'un conteur ou d'une conteuse professionnelle",
        "occasions": "médiathèques, écoles, festivals, soirées privées, EHPAD",
        "audience": "enfants, familles, adultes selon le répertoire",
        "duration": "30 à 60 minutes",
    },
    "mentaliste": {
        "intro": "spectacle de mentalisme (lecture de pensée, prédictions, hypnose de scène)",
        "occasions": "soirées d'entreprise, séminaires, galas, mariages, événements privés haut de gamme",
        "audience": "adultes principalement, ados et adultes",
        "duration": "45 à 90 minutes",
    },
    "humoriste": {
        "intro": "one-man-show, stand-up ou spectacle d'humoriste professionnel",
        "occasions": "soirées d'entreprise, mariages, anniversaires adulte, festivals d'humour",
        "audience": "ados et adultes",
        "duration": "45 à 90 minutes",
    },
    "ventriloque": {
        "intro": "spectacle de ventriloque avec marionnette, alliant humour et illusion",
        "occasions": "anniversaires, arbres de Noël, soirées d'entreprise, fêtes communales",
        "audience": "enfants, familles, adultes",
        "duration": "30 à 60 minutes",
    },
    "mascotte": {
        "intro": "animation par mascotte costumée (héros pour enfants, personnages de fiction)",
        "occasions": "anniversaires d'enfants, arbres de Noël, animations commerciales, parcs",
        "audience": "enfants de 2 à 10 ans",
        "duration": "1 à 3 heures de présence",
    },
    "pere-noel": {
        "intro": "intervention d'un Père Noël professionnel (costume de qualité, distribution de cadeaux)",
        "occasions": "arbres de Noël CSE, magasins, marchés de Noël, mairies, écoles",
        "audience": "enfants principalement (2-10 ans)",
        "duration": "1 à 3 heures de présence sur site",
    },
    "echassier": {
        "intro": "déambulation ou numéro d'échassiers (pour parade, accueil ou mise en scène)",
        "occasions": "festivals, parades, inaugurations, mariages, animations commerciales",
        "audience": "tout public",
        "duration": "30 à 90 minutes en déambulation",
    },
    "sculpteur-ballons": {
        "intro": "atelier de sculpture sur ballons (animaux, chapeaux, personnages)",
        "occasions": "anniversaires d'enfants, kermesses, animations commerciales, marchés de Noël",
        "audience": "enfants de 3 à 12 ans",
        "duration": "1 à 3 heures avec rotation",
    },
    "caricaturiste": {
        "intro": "caricaturiste ou silhouettiste pour animation événementielle",
        "occasions": "mariages, soirées d'entreprise, salons, vernissages",
        "audience": "tout public, dessins individuels",
        "duration": "2 à 4 heures de présence",
    },
    "maquillage": {
        "intro": "atelier de maquillage artistique pour enfants (animaux, super-héros, princesses)",
        "occasions": "anniversaires, kermesses, fêtes d'école, animations commerciales",
        "audience": "enfants de 3 à 12 ans",
        "duration": "1 à 3 heures avec rotation",
    },
    "one-man-show": {
        "intro": "one-man-show comique ou théâtral d'un humoriste professionnel",
        "occasions": "soirées d'entreprise, mariages, festivals, salles de spectacle",
        "audience": "ados et adultes",
        "duration": "60 à 90 minutes",
    },
    "comedie-musicale": {
        "intro": "comédie musicale ou spectacle musical théâtralisé",
        "occasions": "salles de spectacle, festivals, comités d'entreprise, événements municipaux",
        "audience": "tout public, familial",
        "duration": "75 à 120 minutes",
    },
    "chorale-gospel": {
        "intro": "chorale, ensemble vocal ou groupe de gospel",
        "occasions": "mariages, cérémonies, concerts, fêtes religieuses, événements caritatifs",
        "audience": "tout public",
        "duration": "45 à 90 minutes",
    },
    "fanfare": {
        "intro": "fanfare, batucada ou parade musicale pour animation festive",
        "occasions": "défilés, fêtes de village, inaugurations, festivals, mariages",
        "audience": "tout public, déambulation",
        "duration": "30 à 90 minutes en déambulation ou fixe",
    },
    "dj-orchestre": {
        "intro": "DJ ou orchestre professionnel pour soirée dansante",
        "occasions": "mariages, soirées d'entreprise, anniversaires, bals municipaux",
        "audience": "tout public, ambiance dansante",
        "duration": "3 à 6 heures (set complet)",
    },
    "jazz": {
        "intro": "trio, quartet ou ensemble jazz pour cocktail, dîner ou concert",
        "occasions": "vernissages, cocktails d'entreprise, mariages, festivals jazz",
        "audience": "adultes, mélomanes, ambiance feutrée",
        "duration": "2 à 4 heures (sets fractionnés)",
    },
    "musique-classique": {
        "intro": "ensemble de musique classique (quatuor à cordes, pianiste, ensemble baroque…)",
        "occasions": "mariages, cérémonies, vernissages, concerts, événements protocolaires",
        "audience": "adultes, mélomanes",
        "duration": "60 à 120 minutes",
    },
    "chanson-francaise": {
        "intro": "concert de chanson française (variété, chanson à texte, reprises)",
        "occasions": "soirées d'entreprise, mariages, festivals, animations municipales",
        "audience": "tout public, familial",
        "duration": "60 à 120 minutes",
    },
    "spectacle-medieval": {
        "intro": "spectacle médiéval (combats, jonglerie, fauconnerie, musique d'époque)",
        "occasions": "fêtes médiévales, châteaux, festivals historiques, animations touristiques",
        "audience": "tout public, familial",
        "duration": "30 à 90 minutes",
    },
    "spectacle-animalier": {
        "intro": "spectacle animalier ou intervention pédagogique avec animaux",
        "occasions": "écoles, fêtes de village, festivals, animations dans des parcs",
        "audience": "enfants, familles",
        "duration": "30 à 60 minutes",
    },
    "cabaret": {
        "intro": "spectacle de cabaret (revue, danseuses, chanteurs, illusion)",
        "occasions": "soirées privées, casinos, mariages, repas-spectacle",
        "audience": "adultes, public adulte averti",
        "duration": "60 à 120 minutes",
    },
}


def get_category_seo_data(category_slug: str) -> dict:
    """
    Retourne les informations SEO enrichies pour un thème de spectacle.
    Fournit un fallback générique si le slug n'a pas de données dédiées.
    """
    if category_slug in CATEGORY_SEO_DATA:
        return CATEGORY_SEO_DATA[category_slug]
    return {
        "intro": "spectacle vivant professionnel",
        "occasions": "anniversaires, fêtes de village, événements municipaux, soirées d'entreprise",
        "audience": "tout public, programmable selon l'âge",
        "duration": "30 à 90 minutes selon le format",
    }
