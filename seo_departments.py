"""Liste des départements français métropolitains pour le SEO département.

Format : code INSEE → dict{name, slug, region}.

Utilisée par la route /spectacles-departement/<slug> pour créer des pages
de niveau département (ex: "spectacle Ille-et-Vilaine", "animation Corrèze").
"""

FRENCH_DEPARTMENTS = [
    {"code": "01", "name": "Ain", "slug": "ain", "region": "Auvergne-Rhône-Alpes"},
    {"code": "02", "name": "Aisne", "slug": "aisne", "region": "Hauts-de-France"},
    {"code": "03", "name": "Allier", "slug": "allier", "region": "Auvergne-Rhône-Alpes"},
    {"code": "04", "name": "Alpes-de-Haute-Provence", "slug": "alpes-de-haute-provence", "region": "Provence-Alpes-Côte d'Azur"},
    {"code": "05", "name": "Hautes-Alpes", "slug": "hautes-alpes", "region": "Provence-Alpes-Côte d'Azur"},
    {"code": "06", "name": "Alpes-Maritimes", "slug": "alpes-maritimes", "region": "Provence-Alpes-Côte d'Azur"},
    {"code": "07", "name": "Ardèche", "slug": "ardeche", "region": "Auvergne-Rhône-Alpes"},
    {"code": "08", "name": "Ardennes", "slug": "ardennes", "region": "Grand Est"},
    {"code": "09", "name": "Ariège", "slug": "ariege", "region": "Occitanie"},
    {"code": "10", "name": "Aube", "slug": "aube", "region": "Grand Est"},
    {"code": "11", "name": "Aude", "slug": "aude", "region": "Occitanie"},
    {"code": "12", "name": "Aveyron", "slug": "aveyron", "region": "Occitanie"},
    {"code": "13", "name": "Bouches-du-Rhône", "slug": "bouches-du-rhone", "region": "Provence-Alpes-Côte d'Azur"},
    {"code": "14", "name": "Calvados", "slug": "calvados", "region": "Normandie"},
    {"code": "15", "name": "Cantal", "slug": "cantal", "region": "Auvergne-Rhône-Alpes"},
    {"code": "16", "name": "Charente", "slug": "charente", "region": "Nouvelle-Aquitaine"},
    {"code": "17", "name": "Charente-Maritime", "slug": "charente-maritime", "region": "Nouvelle-Aquitaine"},
    {"code": "18", "name": "Cher", "slug": "cher", "region": "Centre-Val de Loire"},
    {"code": "19", "name": "Corrèze", "slug": "correze", "region": "Nouvelle-Aquitaine"},
    {"code": "2A", "name": "Corse-du-Sud", "slug": "corse-du-sud", "region": "Corse"},
    {"code": "2B", "name": "Haute-Corse", "slug": "haute-corse", "region": "Corse"},
    {"code": "21", "name": "Côte-d'Or", "slug": "cote-d-or", "region": "Bourgogne-Franche-Comté"},
    {"code": "22", "name": "Côtes-d'Armor", "slug": "cotes-d-armor", "region": "Bretagne"},
    {"code": "23", "name": "Creuse", "slug": "creuse", "region": "Nouvelle-Aquitaine"},
    {"code": "24", "name": "Dordogne", "slug": "dordogne", "region": "Nouvelle-Aquitaine"},
    {"code": "25", "name": "Doubs", "slug": "doubs", "region": "Bourgogne-Franche-Comté"},
    {"code": "26", "name": "Drôme", "slug": "drome", "region": "Auvergne-Rhône-Alpes"},
    {"code": "27", "name": "Eure", "slug": "eure", "region": "Normandie"},
    {"code": "28", "name": "Eure-et-Loir", "slug": "eure-et-loir", "region": "Centre-Val de Loire"},
    {"code": "29", "name": "Finistère", "slug": "finistere", "region": "Bretagne"},
    {"code": "30", "name": "Gard", "slug": "gard", "region": "Occitanie"},
    {"code": "31", "name": "Haute-Garonne", "slug": "haute-garonne", "region": "Occitanie"},
    {"code": "32", "name": "Gers", "slug": "gers", "region": "Occitanie"},
    {"code": "33", "name": "Gironde", "slug": "gironde", "region": "Nouvelle-Aquitaine"},
    {"code": "34", "name": "Hérault", "slug": "herault", "region": "Occitanie"},
    {"code": "35", "name": "Ille-et-Vilaine", "slug": "ille-et-vilaine", "region": "Bretagne"},
    {"code": "36", "name": "Indre", "slug": "indre", "region": "Centre-Val de Loire"},
    {"code": "37", "name": "Indre-et-Loire", "slug": "indre-et-loire", "region": "Centre-Val de Loire"},
    {"code": "38", "name": "Isère", "slug": "isere", "region": "Auvergne-Rhône-Alpes"},
    {"code": "39", "name": "Jura", "slug": "jura", "region": "Bourgogne-Franche-Comté"},
    {"code": "40", "name": "Landes", "slug": "landes", "region": "Nouvelle-Aquitaine"},
    {"code": "41", "name": "Loir-et-Cher", "slug": "loir-et-cher", "region": "Centre-Val de Loire"},
    {"code": "42", "name": "Loire", "slug": "loire", "region": "Auvergne-Rhône-Alpes"},
    {"code": "43", "name": "Haute-Loire", "slug": "haute-loire", "region": "Auvergne-Rhône-Alpes"},
    {"code": "44", "name": "Loire-Atlantique", "slug": "loire-atlantique", "region": "Pays de la Loire"},
    {"code": "45", "name": "Loiret", "slug": "loiret", "region": "Centre-Val de Loire"},
    {"code": "46", "name": "Lot", "slug": "lot", "region": "Occitanie"},
    {"code": "47", "name": "Lot-et-Garonne", "slug": "lot-et-garonne", "region": "Nouvelle-Aquitaine"},
    {"code": "48", "name": "Lozère", "slug": "lozere", "region": "Occitanie"},
    {"code": "49", "name": "Maine-et-Loire", "slug": "maine-et-loire", "region": "Pays de la Loire"},
    {"code": "50", "name": "Manche", "slug": "manche", "region": "Normandie"},
    {"code": "51", "name": "Marne", "slug": "marne", "region": "Grand Est"},
    {"code": "52", "name": "Haute-Marne", "slug": "haute-marne", "region": "Grand Est"},
    {"code": "53", "name": "Mayenne", "slug": "mayenne", "region": "Pays de la Loire"},
    {"code": "54", "name": "Meurthe-et-Moselle", "slug": "meurthe-et-moselle", "region": "Grand Est"},
    {"code": "55", "name": "Meuse", "slug": "meuse", "region": "Grand Est"},
    {"code": "56", "name": "Morbihan", "slug": "morbihan", "region": "Bretagne"},
    {"code": "57", "name": "Moselle", "slug": "moselle", "region": "Grand Est"},
    {"code": "58", "name": "Nièvre", "slug": "nievre", "region": "Bourgogne-Franche-Comté"},
    {"code": "59", "name": "Nord", "slug": "nord", "region": "Hauts-de-France"},
    {"code": "60", "name": "Oise", "slug": "oise", "region": "Hauts-de-France"},
    {"code": "61", "name": "Orne", "slug": "orne", "region": "Normandie"},
    {"code": "62", "name": "Pas-de-Calais", "slug": "pas-de-calais", "region": "Hauts-de-France"},
    {"code": "63", "name": "Puy-de-Dôme", "slug": "puy-de-dome", "region": "Auvergne-Rhône-Alpes"},
    {"code": "64", "name": "Pyrénées-Atlantiques", "slug": "pyrenees-atlantiques", "region": "Nouvelle-Aquitaine"},
    {"code": "65", "name": "Hautes-Pyrénées", "slug": "hautes-pyrenees", "region": "Occitanie"},
    {"code": "66", "name": "Pyrénées-Orientales", "slug": "pyrenees-orientales", "region": "Occitanie"},
    {"code": "67", "name": "Bas-Rhin", "slug": "bas-rhin", "region": "Grand Est"},
    {"code": "68", "name": "Haut-Rhin", "slug": "haut-rhin", "region": "Grand Est"},
    {"code": "69", "name": "Rhône", "slug": "rhone", "region": "Auvergne-Rhône-Alpes"},
    {"code": "70", "name": "Haute-Saône", "slug": "haute-saone", "region": "Bourgogne-Franche-Comté"},
    {"code": "71", "name": "Saône-et-Loire", "slug": "saone-et-loire", "region": "Bourgogne-Franche-Comté"},
    {"code": "72", "name": "Sarthe", "slug": "sarthe", "region": "Pays de la Loire"},
    {"code": "73", "name": "Savoie", "slug": "savoie", "region": "Auvergne-Rhône-Alpes"},
    {"code": "74", "name": "Haute-Savoie", "slug": "haute-savoie", "region": "Auvergne-Rhône-Alpes"},
    {"code": "75", "name": "Paris", "slug": "paris-75", "region": "Île-de-France"},
    {"code": "76", "name": "Seine-Maritime", "slug": "seine-maritime", "region": "Normandie"},
    {"code": "77", "name": "Seine-et-Marne", "slug": "seine-et-marne", "region": "Île-de-France"},
    {"code": "78", "name": "Yvelines", "slug": "yvelines", "region": "Île-de-France"},
    {"code": "79", "name": "Deux-Sèvres", "slug": "deux-sevres", "region": "Nouvelle-Aquitaine"},
    {"code": "80", "name": "Somme", "slug": "somme", "region": "Hauts-de-France"},
    {"code": "81", "name": "Tarn", "slug": "tarn", "region": "Occitanie"},
    {"code": "82", "name": "Tarn-et-Garonne", "slug": "tarn-et-garonne", "region": "Occitanie"},
    {"code": "83", "name": "Var", "slug": "var", "region": "Provence-Alpes-Côte d'Azur"},
    {"code": "84", "name": "Vaucluse", "slug": "vaucluse", "region": "Provence-Alpes-Côte d'Azur"},
    {"code": "85", "name": "Vendée", "slug": "vendee", "region": "Pays de la Loire"},
    {"code": "86", "name": "Vienne", "slug": "vienne", "region": "Nouvelle-Aquitaine"},
    {"code": "87", "name": "Haute-Vienne", "slug": "haute-vienne", "region": "Nouvelle-Aquitaine"},
    {"code": "88", "name": "Vosges", "slug": "vosges", "region": "Grand Est"},
    {"code": "89", "name": "Yonne", "slug": "yonne", "region": "Bourgogne-Franche-Comté"},
    {"code": "90", "name": "Territoire de Belfort", "slug": "territoire-de-belfort", "region": "Bourgogne-Franche-Comté"},
    {"code": "91", "name": "Essonne", "slug": "essonne", "region": "Île-de-France"},
    {"code": "92", "name": "Hauts-de-Seine", "slug": "hauts-de-seine", "region": "Île-de-France"},
    {"code": "93", "name": "Seine-Saint-Denis", "slug": "seine-saint-denis", "region": "Île-de-France"},
    {"code": "94", "name": "Val-de-Marne", "slug": "val-de-marne", "region": "Île-de-France"},
    {"code": "95", "name": "Val-d'Oise", "slug": "val-d-oise", "region": "Île-de-France"},
]


def get_department_by_slug(slug: str) -> dict | None:
    """Retrouve un département par son slug URL."""
    slug = (slug or "").strip().lower()
    for dept in FRENCH_DEPARTMENTS:
        if dept["slug"] == slug:
            return dept
    return None


def get_department_by_code(code: str) -> dict | None:
    """Retrouve un département par son code INSEE."""
    code = (code or "").strip().upper()
    for dept in FRENCH_DEPARTMENTS:
        if dept["code"] == code:
            return dept
    return None


def get_all_department_slugs() -> list[str]:
    """Liste tous les slugs de département pour le sitemap."""
    return [d["slug"] for d in FRENCH_DEPARTMENTS]
