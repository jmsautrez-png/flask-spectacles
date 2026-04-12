"""
Test de la normalisation de recherche pour démontrer la tolérance aux accents et ponctuation
"""
import unicodedata
import re

def normalize_search_text(text: str) -> str:
    """Normalise le texte pour une recherche tolérante aux accents et ponctuation.
    
    Transformations:
    - Supprime les accents (père -> pere)
    - Supprime la ponctuation (père-noël -> pere noel)
    - Met en minuscules
    - Normalise les espaces
    
    Exemples:
    - 'Père Noël' -> 'pere noel'
    - 'père-noël' -> 'pere noel'
    - 'pére noel' -> 'pere noel'
    """
    if not text:
        return ""
    
    # Mettre en minuscules
    text = text.lower()
    
    # Supprimer les accents
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Remplacer la ponctuation et caractères spéciaux par des espaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    
    # Normaliser les espaces multiples
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

# Tests de démonstration
test_cases = [
    "Père Noël",
    "père-noël",
    "père noël",
    "pére noel",
    "PÈRE NOËL",
    "Pere-Noel",
    "père  noël",  # Double espace
    "marionnette",
    "marionnétte",  # Faute d'accent
    "théâtre",
    "théatre",  # Sans accent
    "magie",
    "magïe",  # Accent bizarre
    "spectacle d'été",
    "spectacle d ete",
]

print("=" * 60)
print("TEST DE NORMALISATION DE RECHERCHE")
print("=" * 60)
print("\nToutes ces variantes seront trouvées comme équivalentes:\n")

for test in test_cases:
    normalized = normalize_search_text(test)
    print(f"'{test}' → '{normalized}'")

print("\n" + "=" * 60)
print("GROUPES ÉQUIVALENTS:")
print("=" * 60)

# Grouper par résultat normalisé
from collections import defaultdict
groups = defaultdict(list)
for test in test_cases:
    groups[normalize_search_text(test)].append(test)

for normalized, originals in groups.items():
    if len(originals) > 1:
        print(f"\n✓ '{normalized}' trouvera:")
        for original in originals:
            print(f"  - '{original}'")
