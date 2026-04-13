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


def generate_fuzzy_variants(word):
    """
    Génère des variantes d'un mot pour tolérer les fautes de frappe courantes:
    - Lettres doublées (noel -> noeel)
    - Lettres manquantes (noel -> nol)
    - Inversion de lettres adjacentes (noel -> nole)
    - Version normalisée (sans accents)
    """
    if not word or len(word) < 3:
        return {word}
    
    variants = {word}
    word_lower = word.lower()
    
    # Version normalisée (sans accents)
    normalized = normalize_search_text(word)
    if normalized != word_lower:
        variants.add(normalized)
    
    # Lettres doublées (chaque lettre)
    for i in range(len(word_lower)):
        doubled = word_lower[:i+1] + word_lower[i] + word_lower[i+1:]
        variants.add(doubled)
    
    # Lettres manquantes (retirer chaque lettre tour à tour)
    for i in range(len(word_lower)):
        missing = word_lower[:i] + word_lower[i+1:]
        if len(missing) >= 2:
            variants.add(missing)
    
    # Inversion de lettres adjacentes
    for i in range(len(word_lower) - 1):
        swapped = list(word_lower)
        swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
        variants.add(''.join(swapped))
    
    # Ajouter les versions accentuées connues
    if normalized in _ACCENT_WORDS:
        variants.update(_ACCENT_WORDS[normalized])
    if word_lower in _ACCENT_WORDS:
        variants.update(_ACCENT_WORDS[word_lower])
    
    return variants


def generate_search_patterns(query, max_variants=50):
    """
    Génère des patterns de recherche avec tolérance aux fautes.
    Retourne une liste de mots/patterns à chercher dans la base.
    """
    if not query:
        return []
    
    # Normaliser la requête
    normalized_query = normalize_search_text(query)
    words = normalized_query.split()
    
    patterns = set()
    # Ajouter la requête originale et normalisée
    patterns.add(query)
    patterns.add(normalized_query)
    
    # Pour chaque mot, générer des variantes
    for word in words:
        if len(word) >= 3:  # Ignorer les mots trop courts
            word_variants = generate_fuzzy_variants(word)
            # Limiter le nombre de variantes par mot
            for variant in list(word_variants)[:10]:
                patterns.add(variant)
    
    # Limiter le nombre total de patterns
    return list(patterns)[:max_variants]
