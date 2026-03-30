import sqlite3

DB_PATH = 'instance/spectacles.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print('Tables présentes dans la base :')
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table';"):
    print('-', row[0])

conn.close()
