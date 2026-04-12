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
