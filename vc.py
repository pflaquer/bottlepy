import sqlite3
conn = sqlite3.connect('todo.db')
# Create a table for users
conn.execute("CREATE TABLE IF NOT EXISTS vc (firm TEXT PRIMARY KEY, location TEXT)")
# Add a test user
conn.execute("INSERT OR IGNORE INTO vc (firm, location) VALUES ('Sequoia', 'New York, NY')")
conn.commit()
conn.close()
