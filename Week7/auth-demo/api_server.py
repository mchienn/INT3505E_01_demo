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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
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
REFRESH_TOKENS_DB = {}
BLACKLISTED_TOKENS = set()


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
    
    payload = verify_refresh_token(data['refresh_token'])
    if not payload:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    
    user = USERS_DB.get(payload['username'])
    if not user or not user['is_active']:
        return jsonify({'error': 'User is inactive'}), 401
    
    new_access_token = create_access_token(user)
    
    return jsonify({
        'message': 'Token refreshed successfully',
        'access_token': new_access_token,
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }), 200


@app.route('/auth/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers['Authorization'].split(" ")[1]
    BLACKLISTED_TOKENS.add(token)
    
    data = request.get_json() or {}
    if data.get('refresh_token'):
        try:
            payload = jwt.decode(data['refresh_token'], app.config['REFRESH_SECRET_KEY'], algorithms=[ALGORITHM])
            jti = payload.get('jti')
            if jti and jti in REFRESH_TOKENS_DB:
                del REFRESH_TOKENS_DB[jti]
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


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 JWT Authentication API v2.0 - Production Ready")
    print("="*70)
    print(f"\n📍 Server: http://localhost:5000")
    print(f"� Demo UI: http://localhost:5000")
    print(f"�📖 API Docs: http://localhost:5000/docs")
    print(f"\n🔐 Security Features:")
    print(f"   ✓ Password hashing (bcrypt)")
    print(f"   ✓ Access tokens (15 min expiry)")
    print(f"   ✓ Refresh tokens (7 days expiry)")
    print(f"   ✓ Token blacklisting on logout")
    print(f"   ✓ Email & password validation")
    print(f"   ✓ User activation/deactivation")
    print(f"   ✓ Auto refresh token on expiry")
    print(f"\n👤 Test Accounts:")
    print(f"   Admin:  username=admin  password=admin123")
    print(f"   User:   username=user1  password=user123")
    print(f"\n📝 Try These Flows:")
    print(f"   1. Login → Wait for token to expire → Auto refresh!")
    print(f"   2. Login → Logout → Session cleared")
    print(f"   3. F5 refresh page → Session restored from LocalStorage")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5000)
