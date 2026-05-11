"""Normalise les valeurs sales de users.region (anciennes regions, casse, etc).

Usage: python clean_user_regions.py
"""
import os
import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL manquante (cf .env)")
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Mapping: pattern (lowercase) -> region officielle 2016+
MAPPING = {
    "somme": "Hauts-de-France",
    "nord pas de calais": "Hauts-de-France",
    "nord-pas-de-calais": "Hauts-de-France",
    "basse-normandie": "Normandie",
    "basse normandie": "Normandie",
    "haute-normandie": "Normandie",
    "haute normandie": "Normandie",
    "picardie": "Hauts-de-France",
    "champagne-ardenne": "Grand Est",
    "lorraine": "Grand Est",
    "alsace": "Grand Est",
    "auvergne": "Auvergne-Rhône-Alpes",
    "rhone-alpes": "Auvergne-Rhône-Alpes",
    "rhône-alpes": "Auvergne-Rhône-Alpes",
    "bourgogne": "Bourgogne-Franche-Comté",
    "franche-comte": "Bourgogne-Franche-Comté",
    "franche-comté": "Bourgogne-Franche-Comté",
    "languedoc-roussillon": "Occitanie",
    "midi-pyrenees": "Occitanie",
    "midi-pyrénées": "Occitanie",
    "aquitaine": "Nouvelle-Aquitaine",
    "limousin": "Nouvelle-Aquitaine",
    "poitou-charentes": "Nouvelle-Aquitaine",
    "provence-alpes-cote d'azur": "Provence-Alpes-Côte d'Azur",
    "paca": "Provence-Alpes-Côte d'Azur",
    "ile-de-france": "Île-de-France",
    "ile de france": "Île-de-France",
}

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("SELECT id, region FROM users WHERE region IS NOT NULL AND region <> ''")
rows = cur.fetchall()
print(f"{len(rows)} utilisateurs avec region.")

updates = []
for uid, region in rows:
    key = (region or "").strip().lower()
    if key in MAPPING and MAPPING[key] != region:
        updates.append((uid, region, MAPPING[key]))

print(f"\nA normaliser : {len(updates)}")
for uid, old, new in updates:
    print(f"  user {uid}: '{old}' -> '{new}'")

if not updates:
    print("Rien a faire.")
    raise SystemExit(0)

confirm = input("\nAppliquer ? (oui/non) : ").strip().lower()
if confirm not in ("oui", "o", "yes", "y"):
    print("Annule.")
    raise SystemExit(0)

for uid, _old, new in updates:
    cur.execute("UPDATE users SET region = %s WHERE id = %s", (new, uid))
conn.commit()
print(f"OK -- {len(updates)} mises a jour.")

cur.close()
conn.close()
