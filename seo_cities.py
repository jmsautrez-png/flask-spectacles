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
