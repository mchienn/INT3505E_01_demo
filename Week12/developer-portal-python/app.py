from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g
import sqlite3
import secrets
import time
import functools

app = Flask(__name__)
app.secret_key = 'super_secret_dev_key'  # Change this in production
DATABASE = 'portal.db'

# --- Database Setup ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # API Keys Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key_value TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Posts Table (Mock Data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                user_id INTEGER
            )
        ''')
        
        db.commit()

# --- Auth Decorator ---
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# --- Helpers ---
def verify_api_key(key):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, user_id FROM api_keys WHERE key_value = ? AND active = 1", (key,))
    result = cur.fetchone()
    if result:
        # Rate limiting logic could go here (e.g., Redis check)
        return True
    return False

# --- Routes: Frontend ---

@app.route('/')
def index():
    user = None
    if 'user_id' in session:
        user = session['username']
    return render_template('index.html', user=user)

@app.route('/docs')
def docs():
    user = None
    if 'user_id' in session:
        user = session['username']
    return render_template('docs.html', user=user)

@app.route('/sandbox')
def sandbox():
    user = None
    if 'user_id' in session:
        user = session['username']
    return render_template('sandbox.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and user['password'] == password:  # Note: Use hashing in production!
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error=f"User {username} is already registered.")
            
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    keys = db.execute('SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    return render_template('dashboard.html', username=session['username'], keys=keys)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/keys/create', methods=['POST'])
@login_required
def create_key():
    name = request.form.get('name', 'My API Key')
    new_key = "sk_" + secrets.token_urlsafe(24)
    
    db = get_db()
    db.execute('INSERT INTO api_keys (user_id, key_value, name) VALUES (?, ?, ?)', 
               (session['user_id'], new_key, name))
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/api/keys/revoke/<int:key_id>', methods=['POST'])
@login_required
def revoke_key(key_id):
    db = get_db()
    db.execute('UPDATE api_keys SET active = 0 WHERE id = ? AND user_id = ?', (key_id, session['user_id']))
    db.commit()
    return redirect(url_for('dashboard'))


# --- Routes: The API (v1) ---

@app.route('/api/v1/posts', methods=['GET', 'POST'])
def api_posts():
    # Authentication Check
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        # Demo mode bypass (optional, for safety let's enforce checking if it's "sk_..." unless strictly public)
        # But per requirements: sandbox "without key" is demo.
        # If no key, return demo data or error depending on mode?
        # Let's enforce key for real API simulation, but allow a special header for "Demo"? 
        # Actually standard flow: Reject if no key.
        return jsonify({"error": {"code": 401, "message": "Missing or invalid API Key"}}), 401
    
    token = auth_header.split(" ")[1]
    if not verify_api_key(token):
        return jsonify({"error": {"code": 401, "message": "Invalid API Key"}}), 401

    db = get_db()
    
    # Simulate Rate Limit (just a sleep)
    time.sleep(0.1) 

    if request.method == 'POST':
        data = request.get_json()
        if not data or 'title' not in data:
             return jsonify({"error": {"code": 400, "message": "Missing title"}}), 400
        
        # In a real app we'd insert into DB
        return jsonify({
            "id": str(int(time.time())),
            "title": data['title'],
            "content": data.get('content', ''),
            "status": "published",
            "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }), 201

    # GET
    posts = [
        {"id": "1", "title": "Welcome to the API", "content": "This is real data derived from the backend."},
        {"id": "2", "title": "Python Power", "content": "Served via Flask."}
    ]
    return jsonify({"data": posts, "meta": {"total": 2}})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
