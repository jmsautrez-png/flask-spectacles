"""SEO optimization utilities."""

SEO_CATEGORIES = {
    "marionnette": "marionnette",
    "magie": "magie",
    "clown": "clown",
    "theatre": "théâtre",
    "danse": "danse",
    "spectacle-enfant": "enfant",
    "enfant": "enfant",
    "atelier": "atelier",
    "concert": "concert",
    "cirque": "cirque",
    "spectacle-de-rue": "rue",
    "rue": "rue",
    "orchestre": "orchestre",
    "arbre-de-noel": "arbre de noël",
    "animation-ecole": "animation école",
    "fete-de-village": "fête de village",
    "une": "Spectacle à la une",
}


def optimize_title_seo(title: str, category: str = "", location: str = "", age_range: str = "") -> dict:
    if not title or not title.strip():
        return {
            "original": title,
            "optimized": title,
            "suggestions": [],
            "seo_score": 0,
            "improvements": ["⚠️ Le titre est vide"]
        }

    original = title.strip()
    optimized = original
    improvements = []
    suggestions = []
    seo_score = 50

    words_to_lowercase = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'pour', 'avec', 'sans'}
    words = optimized.split()
    capitalized_words = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in words_to_lowercase:
            capitalized_words.append(word.capitalize())
        else:
            capitalized_words.append(word.lower())
    if capitalized_words != words:
        optimized = ' '.join(capitalized_words)
        improvements.append("✓ Capitalisation optimisée")
        seo_score += 5

    title_lower = optimized.lower()
    context_keywords = []

    if category and category.lower() not in title_lower:
        if len(optimized) + len(category) + 3 < 80:
            context_keywords.append(category.capitalize())

    if age_range and 'enfant' not in title_lower and 'jeune' not in title_lower:
        if any(char.isdigit() for char in age_range):
            context_keywords.append("pour Enfants")
            seo_score += 10

    if location and location.lower() not in title_lower:
        if len(location) <= 25 and len(optimized) + len(location) + 3 < 90:
            if not any(sep in location.lower() for sep in ['france entière', 'toute la france']):
                suggestions.append(f"{optimized} - {location}")

    length = len(optimized)
    if length < 30:
        improvements.append("⚠️ Titre trop court (< 30 caractères) - Ajoutez des détails")
        seo_score -= 15
    elif length > 90:
        improvements.append("⚠️ Titre trop long (> 90 caractères) - Réduisez pour Google")
        seo_score -= 10
    else:
        improvements.append("✓ Longueur optimale pour le SEO")
        seo_score += 15

    essential_keywords = ['spectacle', 'animation', 'show', 'artiste', 'compagnie', 'théâtre', 'concert']
    has_essential = any(kw in title_lower for kw in essential_keywords)

    if not has_essential and category:
        suggestions.append(f"{category.capitalize()} : {optimized}")
        improvements.append("💡 Suggestion: Ajoutez le type de spectacle au début")
        seo_score -= 5
    else:
        improvements.append("✓ Mots-clés essentiels présents")
        seo_score += 10

    base_title = optimized
    if location and location not in base_title:
        suggestions.append(f"{base_title} à {location}")
        suggestions.append(f"{base_title} | {location}")
    if age_range and 'enfant' not in title_lower:
        suggestions.append(f"{base_title} - Spectacle pour Enfants")
    action_phrases = [
        f"{base_title} - Animation Professionnelle",
        f"{base_title} pour Écoles, Mairies et CSE",
        f"{base_title} | Artiste Professionnel",
    ]
    for phrase in action_phrases:
        if len(phrase) <= 85:
            suggestions.append(phrase)

    unique_words = len(set(words))
    total_words = len(words)
    if total_words > 0 and unique_words / total_words > 0.8:
        improvements.append("✓ Vocabulaire varié")
        seo_score += 5

    seo_score = max(0, min(100, seo_score))
    suggestions = list(dict.fromkeys(suggestions))[:5]

    return {
        "original": original,
        "optimized": optimized,
        "suggestions": suggestions,
        "seo_score": seo_score,
        "improvements": improvements
    }
