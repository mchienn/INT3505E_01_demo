from flask import Flask, request, jsonify, render_template
from functools import wraps
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-secret-key')
app.config['REFRESH_SECRET_KEY'] = os.getenv('REFRESH_SECRET_KEY', 'default-dev-refresh-key')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))

USERS_DB = {
    "admin": {
        "user_id": 1,
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "email": "admin@example.com",
        "full_name": "Administrator",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00"
    },
    "user1": {
        "user_id": 2,
        "username": "user1",
        "password": generate_password_hash("user123"),
        "role": "user",
        "email": "user1@example.com",
        "full_name": "John Doe",
        "is_active": True,
        "created_at": "2024-01-15T00:00:00"
    },
    "user2": {
        "user_id": 3,
        "username": "user2",
        "password": generate_password_hash("user123"),
        "role": "user",
        "email": "user2@example.com",
        "full_name": "Jane Smith",
        "is_active": False,
        "created_at": "2024-02-01T00:00:00"
    }
}

REFRESH_TOKENS_DB = {}
BLACKLISTED_TOKENS = set()

# OAuth 2.0 Clients Database
OAUTH_CLIENTS = {
    "third_party_app": {
        "client_id": "third_party_app",
        "client_secret": "secret_xyz_third_party",
        "client_name": "Third Party Application",
        "redirect_uris": ["http://localhost:5001/callback"],
        "allowed_scopes": ["profile", "email"]
    },
}

# OAuth 2.0 Authorization Codes (temporary storage)
AUTHORIZATION_CODES = {}


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, ""


def create_access_token(user_data: dict) -> str:
    payload = {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'role': user_data['role'],
        'email': user_data['email'],
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm=ALGORITHM)


def create_refresh_token(user_data: dict) -> str:
    jti = secrets.token_hex(16)
    payload = {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'type': 'refresh',
        'jti': jti,
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, app.config['REFRESH_SECRET_KEY'], algorithm=ALGORITHM)
    REFRESH_TOKENS_DB[jti] = {
        'user_id': user_data['user_id'],
        'created_at': datetime.utcnow(),
        'last_used': datetime.utcnow()
    }
    return token


def verify_access_token(token: str):
    try:
        if token in BLACKLISTED_TOKENS:
            return None
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[ALGORITHM])
        if payload.get('type') != 'access':
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, app.config['REFRESH_SECRET_KEY'], algorithms=[ALGORITHM])
        if payload.get('type') != 'refresh':
            return None
        jti = payload.get('jti')
        if jti not in REFRESH_TOKENS_DB:
            return None
        REFRESH_TOKENS_DB[jti]['last_used'] = datetime.utcnow()
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Token format invalid'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_access_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        user = USERS_DB.get(payload['username'])
        if not user or not user['is_active']:
            return jsonify({'error': 'User is inactive'}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    user = USERS_DB.get(data['username'])
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user['is_active']:
        return jsonify({'error': 'Account is inactive'}), 403
    
    if not check_password_hash(user['password'], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'email': user['email'],
            'full_name': user['full_name']
        }
    }), 200


@app.route('/auth/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Refresh token required'}), 400
    token = data['refresh_token']

    # Verify the refresh token is valid and present in our store
    payload = verify_refresh_token(token)
    if not payload:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401

    user = USERS_DB.get(payload['username'])
    if not user or not user['is_active']:
        return jsonify({'error': 'User is inactive'}), 401

    # Rotation: issue a new refresh token and access token, remove the old jti
    old_jti = payload.get('jti')
    new_refresh = create_refresh_token(user)
    if old_jti and old_jti in REFRESH_TOKENS_DB:
        try:
            del REFRESH_TOKENS_DB[old_jti]
        except KeyError:
            pass

    new_access_token = create_access_token(user)

    return jsonify({
        'message': 'Token refreshed successfully',
        'access_token': new_access_token,
        'refresh_token': new_refresh,
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }), 200


@app.route('/auth/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers['Authorization'].split(" ")[1]
    BLACKLISTED_TOKENS.add(token)
    print(f"\n[Auth] Access token blacklisted: {token[:20]}...")
    
    data = request.get_json() or {}
    if data.get('refresh_token'):
        try:
            payload = jwt.decode(data['refresh_token'], app.config['REFRESH_SECRET_KEY'], algorithms=[ALGORITHM])
            jti = payload.get('jti')
            if jti and jti in REFRESH_TOKENS_DB:
                del REFRESH_TOKENS_DB[jti]
                print(f"[Auth] Refresh token jti removed: {jti}")
        except:
            pass
    
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['username', 'password', 'email', 'full_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if data['username'] in USERS_DB:
        return jsonify({'error': 'Username already exists'}), 409
    
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    is_valid, error_msg = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    user_id = max([u['user_id'] for u in USERS_DB.values()]) + 1
    
    new_user = {
        'user_id': user_id,
        'username': data['username'],
        'password': generate_password_hash(data['password']),
        'role': 'user',
        'email': data['email'],
        'full_name': data['full_name'],
        'is_active': True,
        'created_at': datetime.utcnow().isoformat()
    }
    
    USERS_DB[data['username']] = new_user
    
    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'user_id': new_user['user_id'],
            'username': new_user['username'],
            'email': new_user['email'],
            'full_name': new_user['full_name']
        }
    }), 201


@app.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    user = USERS_DB.get(request.current_user['username'])
    return jsonify({
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'email': user['email'],
            'full_name': user['full_name'],
            'is_active': user['is_active'],
            'created_at': user['created_at']
        }
    }), 200


@app.route('/auth/change-password', methods=['POST'])
@token_required
def change_password():
    data = request.get_json()
    
    if not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': 'Old password and new password required'}), 400
    
    user = USERS_DB.get(request.current_user['username'])
    
    if not check_password_hash(user['password'], data['old_password']):
        return jsonify({'error': 'Invalid old password'}), 401
    
    is_valid, error_msg = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    user['password'] = generate_password_hash(data['new_password'])
    
    return jsonify({'message': 'Password changed successfully'}), 200


@app.route('/api/public', methods=['GET'])
def public_endpoint():
    return jsonify({
        'message': 'This is a public endpoint',
        'data': 'Anyone can access this',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/protected', methods=['GET'])
@token_required
def protected_endpoint():
    return jsonify({
        'message': 'This is a protected endpoint',
        'data': 'Only authenticated users can see this',
        'user': request.current_user['username'],
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/admin', methods=['GET'])
@admin_required
def admin_endpoint():
    return jsonify({
        'message': 'This is an admin endpoint',
        'data': 'Only admin users can see this',
        'admin': request.current_user['username'],
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    users = []
    for username, user in USERS_DB.items():
        users.append({
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role'],
            'is_active': user['is_active'],
            'created_at': user['created_at']
        })
    
    return jsonify({
        'total': len(users),
        'users': users
    }), 200


@app.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = None
    for u in USERS_DB.values():
        if u['user_id'] == user_id:
            user = u
            break
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user['role'] == 'admin':
        return jsonify({'error': 'Cannot deactivate admin users'}), 403
    
    user['is_active'] = not user['is_active']
    
    return jsonify({
        'message': f'User {"activated" if user["is_active"] else "deactivated"} successfully',
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'is_active': user['is_active']
        }
    }), 200


@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_by_id(user_id):
    user = None
    for u in USERS_DB.values():
        if u['user_id'] == user_id:
            user = u
            break
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role'],
            'is_active': user['is_active'],
            'created_at': user['created_at']
        }
    }), 200


@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = None
    username_key = None
    for key, u in USERS_DB.items():
        if u['user_id'] == user_id:
            user = u
            username_key = key
            break
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'email' in data:
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        user['email'] = data['email']
    
    if 'full_name' in data:
        user['full_name'] = data['full_name']
    
    if 'role' in data:
        if data['role'] not in ['admin', 'user']:
            return jsonify({'error': 'Invalid role. Must be "admin" or "user"'}), 400
        user['role'] = data['role']
    
    if 'password' in data:
        is_valid, error_msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        user['password'] = generate_password_hash(data['password'])
    
    return jsonify({
        'message': 'User updated successfully',
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role'],
            'is_active': user['is_active']
        }
    }), 200


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = None
    username_key = None
    for key, u in USERS_DB.items():
        if u['user_id'] == user_id:
            user = u
            username_key = key
            break
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user['role'] == 'admin':
        return jsonify({'error': 'Cannot delete admin users'}), 403
    
    if user['user_id'] == request.current_user['user_id']:
        return jsonify({'error': 'Cannot delete yourself'}), 403
    
    del USERS_DB[username_key]
    
    for jti in list(REFRESH_TOKENS_DB.keys()):
        if REFRESH_TOKENS_DB[jti]['user_id'] == user_id:
            del REFRESH_TOKENS_DB[jti]
    
    return jsonify({
        'message': 'User deleted successfully',
        'deleted_user': {
            'user_id': user['user_id'],
            'username': user['username']
        }
    }), 200


@app.route('/api/admin/refresh-tokens', methods=['GET'])
@admin_required
def get_refresh_tokens():
    tokens = []
    for jti, info in REFRESH_TOKENS_DB.items():
        tokens.append({
            'jti': jti,
            'user_id': info['user_id'],
            'created_at': info['created_at'].isoformat(),
            'last_used': info['last_used'].isoformat()
        })
    
    return jsonify({
        'total': len(tokens),
        'active_refresh_tokens': tokens,
        'blacklisted_access_tokens': len(BLACKLISTED_TOKENS)
    }), 200


@app.route('/docs', methods=['GET'])
def docs():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({
                url: '/openapi.yaml',
                dom_id: '#swagger-ui',
            })
        </script>
    </body>
    </html>
    '''


@app.route('/openapi.yaml', methods=['GET'])
def openapi_spec():
    from flask import send_file
    return send_file('openapi.yaml', mimetype='text/yaml')


# ============================================================================
# OAuth 2.0 Endpoints (Authorization Server)
# ============================================================================

@app.route('/oauth/authorize', methods=['GET', 'POST'])
def oauth_authorize():
    """OAuth 2.0 Authorization Endpoint"""
    
    if request.method == 'GET':
        # Parse OAuth 2.0 request parameters
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        scope = request.args.get('scope', 'profile email')
        state = request.args.get('state', '')
        
        # Validate client
        client = OAUTH_CLIENTS.get(client_id)
        if not client:
            return jsonify({'error': 'invalid_client', 'message': 'Client not found'}), 400
        
        if redirect_uri not in client['redirect_uris']:
            return jsonify({'error': 'invalid_redirect_uri'}), 400
        
        # Show login & authorization page
        auth_page = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - OAuth 2.0</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 450px;
                    margin: 80px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .logo {{
                    text-align: center;
                    font-size: 36px;
                    color: #4285f4;
                    margin-bottom: 10px;
                    font-weight: bold;
                }}
                .tagline {{
                    text-align: center;
                    color: #666;
                    margin-bottom: 30px;
                }}
                .card {{
                    background: white;
                    border: 1px solid #ddd;
                    padding: 30px;
                }}
                h2 {{
                    margin-top: 0;
                }}
                .info {{
                    background: #e7f3ff;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 3px solid #4285f4;
                }}
                input {{
                    width: 100%;
                    padding: 10px;
                    margin: 8px 0;
                    border: 1px solid #ddd;
                }}
                button {{
                    width: 100%;
                    padding: 12px;
                    background: #4285f4;
                    color: white;
                    border: none;
                    cursor: pointer;
                    margin-top: 10px;
                }}
                button:hover {{
                    background: #357ae8;
                }}
                .hint {{
                    font-size: 12px;
                    color: #666;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="logo">MyAuth Server</div>
            <div class="tagline">Secure OAuth 2.0 Provider</div>
            
            <div class="card">
                <h2>Sign in</h2>
                
                <div class="info">
                    <strong>{client['client_name']}</strong> wants to access your account
                    <br><br>
                    This will allow {client['client_name']} to:
                    <ul style="margin: 10px 0;">
                        <li>View your email address</li>
                        <li>View your profile information</li>
                    </ul>
                </div>
                
                <form method="POST">
                    <input type="text" name="username" placeholder="Username" value="admin" required>
                    <input type="password" name="password" placeholder="Password" value="admin123" required>
                    <input type="hidden" name="client_id" value="{client_id}">
                    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                    <input type="hidden" name="scope" value="{scope}">
                    <input type="hidden" name="state" value="{state}">
                    <button type="submit">Sign in and Continue</button>
                </form>
                
                <div class="hint">
                    <strong>Test accounts:</strong><br>
                    • admin / admin123 (Admin)<br>
                    • user1 / user123 (User)
                </div>
            </div>
        </body>
        </html>
        '''
        return auth_page
    
    elif request.method == 'POST':
        # Handle login and authorization
        username = request.form.get('username')
        password = request.form.get('password')
        client_id = request.form.get('client_id')
        redirect_uri = request.form.get('redirect_uri')
        scope = request.form.get('scope')
        state = request.form.get('state')
        
        # Authenticate user
        user = USERS_DB.get(username)
        if not user or not check_password_hash(user['password'], password):
            return "Invalid credentials", 401
        
        if not user['is_active']:
            return "Account is inactive", 403
        
        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)
        AUTHORIZATION_CODES[auth_code] = {
            'client_id': client_id,
            'user_id': user['user_id'],
            'username': username,
            'scope': scope,
            'expires_at': datetime.utcnow() + timedelta(minutes=10)
        }
        
        print(f"\n[OAuth] Authorization code generated: {auth_code[:20]}... for {username}")
        
        # Redirect back to client with authorization code
        from flask import redirect
        separator = '&' if '?' in redirect_uri else '?'
        return redirect(f"{redirect_uri}{separator}code={auth_code}&state={state}")


@app.route('/oauth/token', methods=['POST'])
def oauth_token():
    """OAuth 2.0 Token Endpoint - Exchange code for JWT access token"""
    
    data = request.get_json() or request.form
    grant_type = data.get('grant_type')
    
    if grant_type == 'authorization_code':
        code = data.get('code')
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        # Validate client credentials
        client = OAUTH_CLIENTS.get(client_id)
        if not client or client['client_secret'] != client_secret:
            return jsonify({'error': 'invalid_client'}), 401
        
        # Validate authorization code
        auth_data = AUTHORIZATION_CODES.get(code)
        if not auth_data:
            return jsonify({'error': 'invalid_grant', 'message': 'Code not found'}), 400
        
        if auth_data['expires_at'] < datetime.utcnow():
            del AUTHORIZATION_CODES[code]
            return jsonify({'error': 'invalid_grant', 'message': 'Code expired'}), 400
        
        if auth_data['client_id'] != client_id:
            return jsonify({'error': 'invalid_grant', 'message': 'Client mismatch'}), 400
        
        # Get user
        user = USERS_DB.get(auth_data['username'])
        
        # Generate JWT access token
        access_token = create_access_token(user)
        
        # Delete authorization code (one-time use)
        del AUTHORIZATION_CODES[code]
        
        print(f"\n[OAuth] Access token issued for {user['username']} to client {client_id}")
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            'scope': auth_data['scope']
        }), 200
    
    else:
        return jsonify({'error': 'unsupported_grant_type'}), 400


@app.route('/oauth/userinfo', methods=['GET'])
def oauth_userinfo():
    """OAuth 2.0 UserInfo Endpoint - Get user info with access token"""
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'missing_token'}), 401
    
    token = auth_header.split(' ')[1]
    
    payload = verify_access_token(token)
    if not payload:
        return jsonify({'error': 'invalid_token'}), 401
    
    user = USERS_DB.get(payload['username'])
    
    return jsonify({
        'sub': str(user['user_id']),
        'username': user['username'],
        'email': user['email'],
        'name': user['full_name'],
        'role': user['role']
    }), 200


@app.route('/oauth/revoke', methods=['POST'])
def oauth_revoke():
    data = request.get_json() or request.form
    token = data.get('token')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')

    if not client_id or not client_secret:
        return jsonify({'error': 'invalid_client', 'message': 'client_id and client_secret required'}), 401

    client = OAUTH_CLIENTS.get(client_id)
    if not client or client.get('client_secret') != client_secret:
        return jsonify({'error': 'invalid_client'}), 401

    if not token:
        return jsonify({'error': 'invalid_request', 'message': 'token is required'}), 400

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[ALGORITHM])
        if payload.get('type') == 'access':
            BLACKLISTED_TOKENS.add(token)
            print(f"\n[OAuth] Access token revoked: {token[:20]}... by client {client_id}")
            return ('', 200)
    except Exception:
        pass

    return ('', 200)


@app.route('/oauth/revoke', methods=['GET'])
def oauth_revoke_form():
    """Simple HTML form so third-party can test revoke via browser POST"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Revoke Token</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 60px auto; padding: 20px; }
            .card { border: 1px solid #ddd; padding: 20px; border-radius: 6px; }
            input, button { width: 100%; padding: 10px; margin: 8px 0; }
            button { background: #2196F3; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Revoke Access Token (Third-Party)</h2>
            <p>Enter client credentials and the <strong>access token</strong> to revoke. Refresh token revocation is not available to third-party clients.</p>
            <form method="POST" action="/oauth/revoke">
                <label>Client ID</label>
                <input type="text" name="client_id" value="" required />
                <label>Client Secret</label>
                <input type="password" name="client_secret" value="" required />
                <label>Access Token</label>
                <input type="text" name="token" value="" required />
                <button type="submit">Revoke Token</button>
            </form>
        </div>
    </body>
    </html>
    '''


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 JWT Authentication API v2.0 - Production Ready")
    print("="*70)
    print(f"\n📍 Server: http://localhost:5000")
    print(f"�📖 API Docs: http://localhost:5000/docs")
    print(f"\n👤 Test Accounts:")
    print(f"   Admin:  username=admin  password=admin123")
    print(f"   User:   username=user1  password=user123")
    
    app.run(debug=True, port=5000)
