import sqlite3
conn = sqlite3.connect('todo.db')
conn.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        to_addr TEXT, 
        subject TEXT, 
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
conn.commit()
conn.close()
