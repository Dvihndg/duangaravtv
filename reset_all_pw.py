import sqlite3
import os

from passlib.hash import pbkdf2_sha256
new_password = os.getenv("RESET_ALL_PASSWORD", "").strip()
if not new_password:
    raise SystemExit("Set RESET_ALL_PASSWORD before resetting passwords.")
correct_hash = pbkdf2_sha256.hash(new_password)

# Update for backend/garage.db
try:
    conn = sqlite3.connect('backend/garage.db')
    c = conn.cursor()
    c.execute("UPDATE users SET hashed_password = ?", (correct_hash,))
    conn.commit()
    conn.close()
except:
    pass

# Update for root garage.db
try:
    conn = sqlite3.connect('garage.db')
    c = conn.cursor()
    c.execute("UPDATE users SET hashed_password = ?", (correct_hash,))
    conn.commit()
    conn.close()
except:
    pass

print("All user passwords reset successfully.")
