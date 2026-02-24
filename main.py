import sqlite3
import subprocess
from bottle import route, run, request, redirect, response

MY_SECRET = 'super-secret-123'

# --- 1. SIGN UP ROUTE ---
@route('/signup')
def signup_page():
    return '''
        <center>
            <h2>Create New Account</h2>
            <form action="/signup" method="post">
                Username: <input name="username" type="text" required/><br><br>
                Password: <input name="password" type="password" required/><br><br>
                <input value="Create Account" type="submit" />
            </form>
            <br><a href="/login">Back to Login</a>
        </center>
    '''

@route('/signup', method='POST')
def do_signup():
    username = request.forms.get('username')
    password = request.forms.get('password')
    
    conn = sqlite3.connect('todo.db')
    try:
        # Save the new user to the database
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return f"Account created for {username}! <a href='/login'>Login here</a>"
    except sqlite3.IntegrityError:
        return "Username already exists! <a href='/signup'>Try another</a>"

# --- 2. LOGIN LOGIC ---
@route('/login')
def login_page():
    return '''
        <center>
            <h2>Login</h2>
            <form action="/login" method="post">
                Username: <input name="username" type="text" /><br><br>
                Password: <input name="password" type="password" /><br><br>
                <input value="Login" type="submit" />
            </form>
            <p>Don't have an account? <a href="/signup">Sign up here</a></p>
        </center>
    '''

@route('/login', method='POST')
def do_login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username=? AND password=?", (username, password))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        response.set_cookie("account", username, secret=MY_SECRET)
        return redirect('/')
    return "Invalid login! <a href='/login'>Try again</a>"

# --- 3. THE PRIVATE LIST ---
@route('/')
def todo_list():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    # ONLY fetch tasks for the logged-in user
    cursor.execute("SELECT id, task FROM todo WHERE username=?", (user,))
    # Get user credits
    cursor.execute("SELECT credits FROM users WHERE username=?", (user,))
    #cursor.execute("SELECT firm FROM vc WHERE firm=?", (user,))
    # NEW: Check for unread messages
    credits = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM messages WHERE receiver=? AND is_read=0", (user,))
    unread_count = cursor.fetchone()[0]
    result = cursor.fetchall()
    conn.close()

    # The 98.css library makes it look like Windows 95 instantly
    state = 0
    badge = f'<span class="badge">[<strong>NEW</strong> {unread_count}]</span>' if unread_count > 0 else ""
    
    #badge = f'<code>NEW</code>' if state > 0 else ""
    output = f'''
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com">
        <style>
            body {{ background-color: #008080; padding: 50px; font-family: "MS Sans Serif", Arial; }}
            .window {{ width: 400px; margin: auto; }}
        </style>
    </head>
    <body>
        <div class="window">
            <div class="title-bar">
                <div class="title-bar-text">Task Manager - {user}</div>
                <div class="title-bar-controls">
                    <button aria-label="Minimize"></button>
                    <button aria-label="Maximize"></button>
                    <button aria-label="Close" onclick="location.href='/logout'"></button>
                </div>
            </div>
            <div class="window-body">
                <p>Welcome back, {user}! Here are your items:</p>
                <ul class="tree-view">
    '''
    
    for row in result:
        output += f"<li>{row[1]} <a href='/delete/{row[0]}' style='float:right;'>[Delete]</a></li>"
    
    output += f'''
                </ul>
                <hr>
                <form action="/add" method="POST">
                    <div class="field-row-stacked">
                        <label>New Task Description:</label>
                        <input type="text" name="task_name" required>
                    </div>
                    <div class="field-row" style="justify-content: flex-end;">
                        <button type="submit">Add to List</button>
                        <button type="button" onclick="location.href='/logout'">Log Off...</button>
                    </div>
                </form>
            </div>
            <hr>
    <div class="field-row" style="justify-content: flex-start;">
        <button onclick="location.href='/messages'">📬 View My Mail {badge}</button>
        <button onclick="location.href='/contact'">🏁 Pitch</button>
        <button onclick="location.href='/logs'">📬 Logs</button>
        <button onclick="location.href='/profile'">📬 Profile</button>
        <button onclick="location.href='/logout'">🏁 Logout</button>
    </div>
            <div class="status-bar">
                <p class="status-bar-field">Status: Online</p>
                <p class="status-bar-field">User: {user}</p>
                <p class="status-bar-field">CPU: 100%</p>
                <p class="status-bar-field">Credits: {credits}</p>
            </div>
        </div>
    </body>
    </html>
    '''
    return output

# --- 4. DATA ACTIONS ---
@route('/add', method='POST')
def add_task():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')
    
    new_task = request.forms.get('task_name')
    conn = sqlite3.connect('todo.db')
    conn.execute("INSERT INTO todo (task, username) VALUES (?, ?)", (new_task, user))
    conn.commit()
    conn.close()
    return redirect('/')

@route('/delete/<id:int>')
def delete_task(id):
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')
        
    conn = sqlite3.connect('todo.db')
    # Extra security: Check ID and Username
    conn.execute("DELETE FROM todo WHERE id=? AND username=?", (id, user))
    conn.commit()
    conn.close()
    return redirect('/')

@route('/logout')
def logout():
    response.delete_cookie("account")
    return redirect('/login')
    

# --- VIEW MESSAGES ---

@route('/messages')
def view_messages():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    # 1. Handle User Search Logic (SSR style)
    search_term = request.query.get('search_user', '').strip()
    search_results = []
    
    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()

    if search_term:
        # Search for other users (excluding yourself)
        cursor.execute("SELECT username FROM users WHERE username LIKE ? AND username != ? LIMIT 5", 
                       (f"%{search_term}%", user))
        search_results = cursor.fetchall()

    # 2. Fetch Inbox Messages
    cursor.execute("SELECT id, sender, body, is_read FROM messages WHERE receiver=?", (user,))
    inbox = cursor.fetchall()
    conn.close()

    # --- Start Output Generation ---
    output = f"<h1>{user}'s Inbox</h1>"

    # 3. User Directory Section
    output += f'''
        <div style="border: 1px solid #000; padding: 10px; background: #dfdfdf; margin-bottom: 20px;">
            <h3>User Directory</h3>
            <form action="/messages" method="GET">
                <input type="text" name="search_user" placeholder="Search for users..." value="{search_term}">
                <button type="submit">Search</button>
            </form>
    '''
    if search_results:
        output += "<ul>"
        for (found_user,) in search_results:
            # We use the same 'Select' logic you mastered for the Reply button
            output += f"<li>{found_user} <button onclick=\"document.getElementById('usernameto').value='{found_user}'\">Select</button></li>"
        output += "</ul>"
    elif search_term:
        output += "<p>No users found.</p>"
    output += "</div><hr>"

    # 4. Message List Section
    output += "<ul>"
    for msg in inbox:
        msg_id, sender, body, is_read = msg
        
        read_link = f" <a href='/read_msg/{msg_id}' style='color:blue;'>[Mark Read]</a>" if is_read == 0 else ""
        status_prefix = "<b>[NEW]</b> " if is_read == 0 else ""

        output += f"""
            <li>
                {status_prefix}<b>From {sender}:</b> {body} 
                <a href='/reply/{sender}'>[Reply]</a> 
                <a style="cursor:pointer; color:blue; text-decoration:underline;" 
                   onclick="document.getElementById('usernameto').value='{sender}';document.getElementById('bodyto').value='re:{body}'">
                   [Reply On Page]
                </a> 
                <a href='/delete_msg/{msg_id}' onclick="return confirm('Permanent delete?');" style='color:red;'>[Delete]</a>
                {read_link}
            </li>"""
    
    # 5. Send Message Form (Now with 'bodyto' ID)
    output += '''
        </ul><hr>
        <h3>Send a Message</h3>
        <form action="/send" method="POST">
            To (Username): <input type="text" name="to_user" id="usernameto" required><br>
            Message: <input type="text" name="msg_body" id="bodyto" required>
            <input type="submit" value="Send">
        </form>
        <br><a href="/">Back to Tasks</a>
    '''
    return output
    




@route('/delete_msg/<id:int>')
def delete_msg(id):
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    # SECURITY: Only delete if the ID matches AND you are the receiver
    conn.execute("DELETE FROM messages WHERE id=? AND receiver=?", (id, user))
    conn.commit()
    conn.close()
    
    return redirect('/messages')
    
@route('/read_msg/<id:int>')
def read_msg(id):
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    # SECURITY: Only delete if the ID matches AND you are the receiver
    conn.execute("UPDATE messages SET is_read=1 WHERE id=? AND receiver=?", (id, user))
    conn.commit()
    conn.close()
    
    return redirect('/messages')


"""#OLD SEND ROUTE?
@route('/send', method='POST')
def send_msg():
    # 1. Identity Check
    sender = request.get_cookie("account", secret=MY_SECRET)
    if not sender: return redirect('/login')

    # 2. Get Form Data (matching your input names 'to_user' and 'msg_body')
    receiver = request.forms.get('to_user')
    body = request.forms.get('msg_body')

    # 3. Insert into Database
    conn = sqlite3.connect('todo.db')
    try:
        # We include is_read=0 so it shows up as [NEW] in your inbox logic
        conn.execute("INSERT INTO messages (sender, receiver, body, subject, is_read) VALUES (?, ?, ?, ?, 0)", 
                     (user, to_addr, body, subject))
        conn.commit()
    except Exception as e:
        return f"Database Error: {str(e)} <a href='/messages'>Back</a>"
    finally:
        conn.close()

    return "Message Sent! <a href='/messages'>Back to Inbox</a>"

"""

    
    
@route('/reply/<to_user>')
def reply_page(to_user):
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    return f'''
        <h3>Replying to {to_user}</h3>
        <form action="/send" method="POST">
            <!-- We hardcode the receiver so the user doesn't have to type it -->
            To: <input type="text" name="to_user" value="{to_user}" readonly><br><br>
            Message: <input type="text" name="msg_body" autofocus required>
            <input type="submit" value="Send Reply">
        </form>
        <br><a href="/messages">Cancel</a>
    '''

@route('/contact')
def contact_page():
    return '''
        <center>
            <h2>📧 Send a System Email</h2>
            <form action="/send" method="POST">
                To: <input type="text" name="to_addr" placeholder="non@aol.com"><br><br>
                Subject: <input type="text" name="subject" required><br><br>
                Message:<br>
                <textarea name="body" rows="5" cols="30"></textarea><br><br>
                <input type="submit" value="Dispatch via Sendmail">
            </form>
            <a href="/">Back to Home</a>
        </center>
    '''

@route('/send', method='POST')
def handle_email():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    
       

    # --- 3. SEND THE EMAIL ---
    to_addr = request.forms.get('to_addr')
    subject = request.forms.get('subject')
    body = request.forms.get('body')
    
    
   
    
    conn.execute("INSERT INTO messages (sender, receiver, body, subject, is_read) VALUES (?, ?, ?, ?, 0)", 
                 (user, to_addr, body, subject))
    conn.execute("UPDATE users SET credits = credits - 10 WHERE username=?", (user,))
    conn.commit() # Save the deduction before sending!
    
    
    conn.close()
    

    return f"Pitch Dispatched! 10 credits used. <a href='/'>Home</a>"


@route('/logs')
def view_logs():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    # SECURITY: Only show logs belonging to the logged-in user
    cursor.execute("SELECT to_addr, subject, sent_at FROM email_logs WHERE username=? ORDER BY sent_at DESC", (user,))
    history = cursor.fetchall()
    conn.close()

    output = f"<h1>{user}'s Outbox History</h1><table border='1' cellpadding='5'>"
    output += "<tr><th>To</th><th>Subject</th><th>Timestamp</th></tr>"
    
    for log in history:
        output += f"<tr><td>{log[0]}</td><td>{log[1]}</td><td>{log[2]}</td></tr>"
    
    output += "</table><br><a href='/'>Back to Home</a>"
    return output

@route('/credits')
def credits_page():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM users WHERE username=?", (user,))
    bal = cursor.fetchone()[0]
    conn.close()

    return f'''
        <center>
            <h2>💰 Credit Balance: {bal}</h2>
            <p>Each pitch costs 10 credits.</p>
            <form action="/replenish" method="POST">
                <input type="submit" value="Buy 100 Credits ($10.00)">
            </form>
            <br><a href="/">Back to Dashboard</a>
        </center>
    '''

@route('/replenish', method='POST')
def do_replenish():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    conn.execute("UPDATE users SET credits = credits + 100 WHERE username=?", (user,))
    conn.commit()
    conn.close()
    return "<h3>Payment Successful!</h3> 100 credits added. <a href='/'>Go Pitch!</a>"

@route('/profile')
def profile_page():
    user = request.get_cookie("account", secret=MY_SECRET)
    if not user: return redirect('/login')

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    
    # Get user credits
    cursor.execute("SELECT credits FROM users WHERE username=?", (user,))
    credits = cursor.fetchone()[0]
    
    # Get total pitches sent (Aggregating the logs)
    cursor.execute("SELECT COUNT(*) FROM email_logs WHERE username=?", (user,))
    total_pitched = cursor.fetchone()[0]
    
    conn.close()

    return f'''
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com">
        <style>
            body {{ background-color: #008080; padding: 50px; }}
            .window {{ width: 350px; margin: auto; }}
        </style>
    </head>
    <body>
        <div class="window">
            <div class="title-bar">
                <div class="title-bar-text">System Properties - {user}</div>
            </div>
            <div class="window-body">
                <p><b>User Information:</b></p>
                <ul class="tree-view">
                    <li>Username: {user}</li>
                    <li>Status: Registered Entrepreneur</li>
                    <li>Current Balance: <font color="green">{credits} Credits</font></li>
                    <li>Successful Pitches: {total_pitched}</li>
                </ul>
                
                <section class="field-row" style="justify-content: center; margin-top: 15px;">
                    <button onclick="location.href='/credits'">Add Credits</button>
                    <button onclick="location.href='/'">Close</button>
                </section>
            </div>
            <div class="status-bar">
                <p class="status-bar-field">Memory: 640KB OK</p>
                <p class="status-bar-field">ID: #00{total_pitched + 101}</p>
            </div>
        </div>
    </body>
    </html>
    '''

@route('/search_users')
def search_users():
    query = request.query.get('q', '').strip()
    if not query: return "Enter a name to search."

    conn = sqlite3.connect('todo.db')
    cursor = conn.cursor()
    # Use '%' for wildcard searching (e.g., 'ali' matches 'alice')
    cursor.execute("SELECT username FROM users WHERE username LIKE ? LIMIT 10", (f'%{query}%',))
    results = cursor.fetchall()
    conn.close()

    if not results:
        return "<p>No users found.</p>"

    output = "<ul>"
    for row in results:
        name = row[0]
        # Reuse your 'Reply On Page' logic to fill the form instantly!
        output += f'''
            <li>{name} 
                <button onclick="document.getElementById('usernameto').value='{name}';">
                    Select
                </button>
            </li>'''
    output += "</ul>"
    return output


if __name__ == '__main__':
    run(host='localhost', port=8080, debug=True, reloader=True)
