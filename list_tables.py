import sqlite3
conn = sqlite3.connect('backend/garage.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
for table in tables:
    print(f"--- {table[0]} ---")
    c.execute(f"PRAGMA table_info({table[0]})")
    cols = c.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
