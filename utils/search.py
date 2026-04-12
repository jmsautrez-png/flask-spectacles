"""Search and text normalization utilities."""
import unicodedata
import re
from itertools import product


def normalize_search_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(
        c for c in normalized
        if unicodedata.category(c) != 'Mn'
    )
    lowered = without_accents.lower()
    cleaned = re.sub(r"[''`]", " ", lowered)
    cleaned = re.sub(r'[^\w\s-]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# Variantes accentuées courantes en français par mot
_ACCENT_WORDS = {
    "pere": ["père"],
    "mere": ["mère"],
    "noel": ["noël"],
    "fete": ["fête"],
    "foret": ["forêt"],
    "chateau": ["château"],
    "theatre": ["théâtre", "théatre"],
    "cote": ["côte", "côté"],
    "ecole": ["école"],
    "creche": ["crèche"],
    "feerique": ["féerique"],
    "feerie": ["féerie", "féérie"],
    "fee": ["fée"],
    "enchante": ["enchanté", "enchantée"],
    "anime": ["animé", "animée"],
    "deguise": ["déguisé", "déguisée"],
    "conte": ["conté"],
    "epee": ["épée"],
    "etoile": ["étoile"],
    "etincelle": ["étincelle"],
    "evenement": ["événement", "évènement"],
    "spectacle": ["spectacle"],
    "marionnette": ["marionnette"],
    "magie": ["magie"],
    "magicien": ["magicien"],
    "clown": ["clown"],
    "anniversaire": ["anniversaire"],
    "enfant": ["enfant"],
}


def generate_accent_variants(query: str) -> set:
    """Génère des variantes accentuées d'une requête de recherche.

    Exemple: 'pere noel' → {'pere noel', 'père noel', 'pere noël', 'père noël'}
    """
    normalized = normalize_search_text(query)
    words = normalized.split()
    if not words:
        return {query}

    variants = {query, normalized}

    # Pour chaque mot, collecter ses variantes accentuées
    word_options = []
    for w in words:
        options = [w]
        if w in _ACCENT_WORDS:
            options.extend(_ACCENT_WORDS[w])
        # Aussi chercher la version avec accent enlevé en tant que variante
        word_options.append(options)

    # Produit cartésien (limité à 32 combinaisons max pour la perf)
    count = 1
    for opts in word_options:
        count *= len(opts)
    if count <= 32:
        for combo in product(*word_options):
            variants.add(" ".join(combo))

    return variants
