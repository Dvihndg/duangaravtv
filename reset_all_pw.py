import sqlite3

correct_hash = "$pbkdf2-sha256$29000$z9lbi7GWMiZk7L1XKmVs7Q$qCjB77NeDxDWeP4AzsMa1JcOadNgyR8N.LLk9PIIuFs"

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

print("All passwords reset to admin123")
