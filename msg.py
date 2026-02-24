import sqlite3
conn = sqlite3.connect('todo.db')
conn.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, 
        sender TEXT, 
        receiver TEXT, 
        body TEXT
    )""")
    
try:
    conn.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
    print("Column 'is_read' added successfully.")
except sqlite3.OperationalError:
    print(

"Column 'is_read' already exists.")
    
conn.commit()
conn.close()
