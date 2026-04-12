"""Search and text normalization utilities."""
import unicodedata
import re
from itertools import product as _product


def normalize_search_text(text):
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text)
    without_accents = "".join(
        c for c in normalized
        if unicodedata.category(c) != "Mn"
    )
    lowered = without_accents.lower()
    cleaned = re.sub(r"[''`]", ' ', lowered)
    cleaned = re.sub(r'[^\w\s-]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


_ACCENT_WORDS = {
    "pere": ["père"],
    "noel": ["noël"],
    "theatre": ["théâtre"],
    "fee": ["fée"],
    "ecole": ["école"],
    "evenement": ["événement"],
    "eveilleur": ["éveilleur"],
    "etrange": ["étrange"],
    "ete": ["été"],
    "etoile": ["étoile"],
    "general": ["général"],
    "comedie": ["comédie"],
    "magie": ["magie"],
    "conte": ["conte"],
    "danse": ["danse"],
    "cirque": ["cirque"],
    "marionnette": ["marionnette"],
    "clown": ["clown"],
}


def generate_accent_variants(query):
    words = query.lower().split()
    variants = []
    for word in words:
        word_variants = [word]
        if word in _ACCENT_WORDS:
            word_variants.extend(_ACCENT_WORDS[word])
        variants.append(word_variants)
    result = set()
    for combo in _product(*variants):
        result.add(" ".join(combo))
    return result
