"""Search and text normalization utilities."""
import unicodedata
import re


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


# Dictionnaire de mots avec variantes accentuées
_ACCENT_WORDS: dict[str, list[str]] = {
    "pere": ["père"],
    "noel": ["noël"],
    "theatre": ["théâtre"],
    "magie": ["magie"],
    "fee": ["fée"],
    "ecole": ["école"],
    "evenement": ["événement"],
    "eveilleur": ["éveilleur"],
    "etrange": ["étrange"],
    "ete": ["été"],
    "etoile": ["étoile"],
    "general": ["général"],
    "conte": ["conte"],
    "comedie": ["comédie"],
    "danse": ["danse"],
    "cirque": ["cirque"],
    "marionnette": ["marionnette"],
    "clown": ["clown"],
}


def generate_accent_variants(query: str) -> set[str]:
    """Génère des variantes accentuées d'une requête de recherche.

    Exemple : "pere noel" → {"père noel", "pere noël", "père noël", "pere noel"}
    """
    words = query.lower().split()
    variants: list[list[str]] = []
    for word in words:
        word_variants = [word]
        if word in _ACCENT_WORDS:
            word_variants.extend(_ACCENT_WORDS[word])
        variants.append(word_variants)

    # Produit cartésien de toutes les variantes de mots
    result: set[str] = set()
    from itertools import product as _product
    for combo in _product(*variants):
        result.add(" ".join(combo))
    return result
