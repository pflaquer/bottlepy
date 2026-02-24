import sqlite3

# This creates 'todo.db' in your current folder
conn = sqlite3.connect('todo.db')
conn.execute("CREATE TABLE todo (id INTEGER PRIMARY KEY, task CHAR(100) NOT NULL)")
conn.execute("INSERT INTO todo (task) VALUES ('Learn Bottle')")
conn.commit()
conn.close()
