import sqlite3
conn = sqlite3.connect('todo.db')
# Add the username column to the existing table
try:
    conn.execute("ALTER TABLE todo ADD COLUMN username TEXT")
except:
    pass # Column already exists
conn.commit()
conn.close()
