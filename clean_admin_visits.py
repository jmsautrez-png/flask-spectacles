"""
Purge les anciennes visites des admins dans visitor_log (SQL brut).
Usage : python clean_admin_visits.py
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

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("SELECT id, username FROM users WHERE is_admin = TRUE")
admins = cur.fetchall()
print("Admins detectes :", admins)
if not admins:
    print("Aucun admin -> rien a faire.")
    raise SystemExit(0)

admin_ids = tuple(a[0] for a in admins)

cur.execute("SELECT COUNT(*) FROM visitor_log WHERE user_id IN %s", (admin_ids,))
n = cur.fetchone()[0]
print(f"Visites admin trouvees : {n}")
if n == 0:
    raise SystemExit(0)

cur.execute("DELETE FROM visitor_log WHERE user_id IN %s", (admin_ids,))
conn.commit()
print(f"OK -- {cur.rowcount} entrees supprimees.")

cur.close()
conn.close()
