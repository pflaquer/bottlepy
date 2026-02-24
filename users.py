import sqlite3
conn = sqlite3.connect('todo.db')
# Create a table for users
conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
# Add a test user
conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', '1234')")
conn.commit()
conn.close()
