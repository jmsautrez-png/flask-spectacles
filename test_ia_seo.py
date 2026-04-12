"""
Test de l'Intelligence Artificielle SEO pour l'optimisation des titres
Démontre comment l'IA améliore automatiquement les titres des spectacles et appels d'offre
"""
import sys
import os

# Ajouter le chemin du projet pour les imports
sys.path.insert(0, os.path.dirname(__file__))

# Import de la fonction d'optimisation SEO
from app import optimize_title_seo

print("=" * 80)
print("🤖 INTELLIGENCE ARTIFICIELLE SEO - TEST DE L'OPTIMISATION DES TITRES")
print("=" * 80)
print()

# Cas de test réalistes
test_cases = [
    {
        "title": "spectacle de magie",
        "category": "Magie",
        "location": "Paris",
        "age_range": "4-10 ans"
    },
    {
        "title": "père noël pour enfants",
        "category": "Père Noël",
        "location": "Lyon",
        "age_range": "3-8 ans"
    },
    {
        "title": "MARIONNETTES EDUCATIVES HISTOIRE DE L EAU ET ENVIRONNEMENT",
        "category": "Marionnette",
        "location": "Marseille",
        "age_range": "6-12 ans"
    },
    {
        "title": "Spectacle musical interactif pour tout-petits avec chansons et comptines traditionnelles françaises",
        "category": "Concert",
        "location": "Toulouse",
        "age_range": "0-3 ans"
    },
    {
        "title": "animation",
        "category": "Animation",
        "location": "Bordeaux",
        "age_range": ""
    },
    {
        "title": "Spectacle de Noël Professionnel pour Mairies et CSE",
        "category": "Père Noël",
        "location": "Lille",
        "age_range": "3-10 ans"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"📊 CAS DE TEST #{i}")
    print(f"{'='*80}")
    
    print(f"\n📝 ENTRÉE:")
    print(f"   Titre: '{test['title']}'")
    print(f"   Catégorie: {test['category']}")
    print(f"   Localisation: {test['location']}")
    print(f"   Âge: {test['age_range']}")
    
    # Appliquer l'optimisation IA
    result = optimize_title_seo(
        test['title'],
        test['category'],
        test['location'],
        test['age_range']
    )
    
    print(f"\n🤖 ANALYSE IA:")
    print(f"   Score SEO: {result['seo_score']}/100 ", end="")
    if result['seo_score'] >= 80:
        print("🟢 EXCELLENT")
    elif result['seo_score'] >= 60:
        print("🟡 BON")
    else:
        print("🔴 À AMÉLIORER")
    
    print(f"\n✨ TITRE OPTIMISÉ:")
    print(f"   '{result['optimized']}'")
    
    if result['optimized'] != result['original']:
        print(f"   → AMÉLIORÉ automatiquement")
    else:
        print(f"   → Déjà optimal")
    
    print(f"\n💡 AMÉLIORATIONS APPLIQUÉES:")
    for improvement in result['improvements']:
        print(f"   {improvement}")
    
    if result['suggestions']:
        print(f"\n🎯 SUGGESTIONS ALTERNATIVES:")
        for j, suggestion in enumerate(result['suggestions'], 1):
            print(f"   {j}. {suggestion}")
    
    print()

print("=" * 80)
print("📈 RÉSUMÉ DE L'INTELLIGENCE ARTIFICIELLE SEO")
print("=" * 80)
print("""
L'IA SEO analyse et optimise automatiquement:
✓ Capitalisation intelligente des mots
✓ Longueur optimale pour Google (40-70 caractères)
✓ Présence des mots-clés essentiels
✓ Ajout contextuel de localisation
✓ Mention du public cible (enfants, écoles, CSE)
✓ Suggestions alternatives pertinentes
✓ Score SEO avec recommandations

🚀 INTÉGRATION:
- API REST: POST /api/seo-suggest
- Suggestions en temps réel dans les formulaires
- Optimisation automatique lors de la saisie
- Compatible avec tous les types de spectacles
""")
print("=" * 80)
