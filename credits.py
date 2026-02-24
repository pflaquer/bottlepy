import sqlite3
conn = sqlite3.connect('todo.db')
try:
    # Add credits column with a default of 10
    conn.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 10")
except:
    pass 
conn.commit()
conn.close()
