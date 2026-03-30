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
