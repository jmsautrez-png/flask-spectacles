#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de vérification de l'environnement de production
Vérifie que toutes les variables critiques sont configurées
"""
import os
import sys

print("=" * 70)
print("VÉRIFICATION ENVIRONNEMENT PRODUCTION")
print("=" * 70)

# Variables critiques à vérifier
critical_vars = {
    'SECRET_KEY': 'Clé secrète Flask (sécurité sessions)',
    'DATABASE_URL': 'URL de connexion PostgreSQL',
    'ADMIN_USERNAME': 'Identifiant administrateur',
    'ADMIN_PASSWORD': 'Mot de passe administrateur',
}

# Variables S3 (optionnelles mais recommandées)
s3_vars = {
    'S3_BUCKET': 'Nom du bucket S3',
    'S3_KEY': 'AWS Access Key ID',
    'S3_SECRET': 'AWS Secret Access Key',
    'S3_REGION': 'Région AWS (ex: eu-west-1)',
}

# Variables optionnelles
optional_vars = {
    'FLASK_ENV': 'Environnement Flask (production/development)',
    'LOG_LEVEL': 'Niveau de log (info/debug/warning/error)',
}

errors = []
warnings = []
ok = []

print("\n🔴 Variables CRITIQUES (obligatoires):")
for var, description in critical_vars.items():
    value = os.environ.get(var)
    if not value:
        errors.append(f"✗ {var} : NON DÉFINIE")
        print(f"   ✗ {var}")
        print(f"      → {description}")
    elif value in ['dev-secret-key', 'admin', 'password', 'test']:
        warnings.append(f"⚠️  {var} : Valeur par défaut détectée (non sécurisé)")
        print(f"   ⚠️  {var} : Valeur par défaut (changer pour sécurité)")
    else:
        ok.append(var)
        # Afficher un aperçu masqué
        if len(value) > 20:
            display = value[:8] + "..." + value[-4:]
        else:
            display = "***"
        print(f"   ✓ {var} : {display}")

print("\n🟡 Variables S3 (upload fichiers):")
s3_configured = 0
for var, description in s3_vars.items():
    value = os.environ.get(var)
    if not value:
        warnings.append(f"⚠️  {var} : Non configurée (uploads en local)")
        print(f"   ⚠️  {var} : Non définie")
    else:
        s3_configured += 1
        if len(value) > 20:
            display = value[:8] + "..." + value[-4:]
        else:
            display = value
        print(f"   ✓ {var} : {display}")

if s3_configured == 0:
    warnings.append("⚠️  S3 non configuré : uploads stockés localement (éphémères sur Render)")
elif s3_configured < 4:
    warnings.append(f"⚠️  S3 partiellement configuré ({s3_configured}/4 variables)")

print("\n🟢 Variables OPTIONNELLES:")
for var, description in optional_vars.items():
    value = os.environ.get(var)
    if not value:
        print(f"   - {var} : Non définie (valeur par défaut utilisée)")
    else:
        print(f"   ✓ {var} : {value}")

# Vérification spécifique DATABASE_URL
print("\n🗄️  Vérification Base de Données:")
db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    if 'postgresql' in db_url:
        print("   ✓ PostgreSQL détecté (recommandé pour production)")
    elif 'sqlite' in db_url:
        warnings.append("⚠️  SQLite détecté (éphémère sur Render, utiliser PostgreSQL)")
        print("   ⚠️  SQLite (non recommandé pour production)")
    else:
        print(f"   ? Type de base inconnu: {db_url.split('://')[0]}")
else:
    errors.append("✗ DATABASE_URL non définie")

# Test de connexion
print("\n🔗 Test de connexion base de données:")
try:
    from app import app, db
    from sqlalchemy import text
    
    with app.app_context():
        db.session.execute(text("SELECT 1"))
        print("   ✓ Connexion réussie")
        
        # Vérifier les tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"   ✓ {len(tables)} tables détectées: {', '.join(sorted(tables))}")
        else:
            warnings.append("⚠️  Aucune table détectée, exécuter: python init_db.py")
            print("   ⚠️  Aucune table détectée")
            
except Exception as e:
    errors.append(f"✗ Erreur connexion DB: {e}")
    print(f"   ✗ Erreur: {e}")

# Test de l'application
print("\n🌐 Test de l'application Flask:")
try:
    from app import app
    print(f"   ✓ Application créée avec succès")
    print(f"   ✓ Debug mode: {app.debug}")
    print(f"   ✓ Testing mode: {app.testing}")
except Exception as e:
    errors.append(f"✗ Erreur création app: {e}")
    print(f"   ✗ Erreur: {e}")

# Résumé final
print("\n" + "=" * 70)
print("RÉSUMÉ")
print("=" * 70)

if errors:
    print(f"\n❌ ERREURS CRITIQUES ({len(errors)}):")
    for error in errors:
        print(f"   {error}")

if warnings:
    print(f"\n⚠️  AVERTISSEMENTS ({len(warnings)}):")
    for warning in warnings:
        print(f"   {warning}")

if ok:
    print(f"\n✅ OK ({len(ok)}):")
    print(f"   {', '.join(ok)}")

print("\n" + "=" * 70)

if errors:
    print("❌ CONFIGURATION INCOMPLÈTE - Corriger les erreurs ci-dessus")
    print("\n💡 Définir les variables manquantes dans:")
    print("   - Render Dashboard → Environment → Environment Variables")
    sys.exit(1)
elif warnings:
    print("⚠️  CONFIGURATION FONCTIONNELLE mais améliorable")
    print("   L'application peut démarrer mais certaines fonctionnalités sont limitées")
    sys.exit(0)
else:
    print("✅ CONFIGURATION OPTIMALE - Prêt pour la production")
    sys.exit(0)
