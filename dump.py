import sqlite3
import sys
conn = sqlite3.connect('garage.db')
with open('schema.txt', 'w', encoding='utf-8') as f:
    for line in conn.iterdump():
        f.write(line + '\n')
