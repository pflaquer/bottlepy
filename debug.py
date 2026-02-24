import sqlite3

def debug_admin_send():
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    
    # 1. VERIFY TABLE SCHEMA
    print("--- 1. Checking Schema ---")
    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current columns in 'messages': {columns}")
    
    # Logic: Your /messages route uses 'receiver', so this must be in the list
    if 'receiver' not in columns:
        print("CRITICAL ERROR: Your table is missing the 'receiver' column!")
        return

    # 2. TEST THE INSERT
    print("\n--- 2. Attempting Insert to 'admin' ---")
    try:
        # Hardcoding 'admin' as the receiver for this debug test
        cursor.execute("""
            INSERT INTO messages (sender, receiver, body, is_read) 
            VALUES ('DEBUG_USER', 'admin', 'This is a test message to admin', 0)
        """, )
        conn.commit()
        print("SUCCESS: Message saved to database.")
    except Exception as e:
        print(f"FAILED: {e}")
        return

    # 3. VERIFY THE DATA
    print("\n--- 3. Verifying in Inbox ---")
    cursor.execute("SELECT * FROM messages WHERE receiver='admin' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"VERIFIED: The admin's latest message is: {row}")
    else:
        print("ERROR: Insert seemed to work, but the message isn't there.")

    conn.close()

if __name__ == "__main__":
    debug_admin_send()
