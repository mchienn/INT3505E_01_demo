from flask import Flask, request, jsonify, send_file
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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
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

# Products Database
PRODUCTS_DB = {
    1: {
        "product_id": 1,
        "name": "Laptop Dell XPS 15",
        "description": "High-performance laptop with Intel i7, 16GB RAM, 512GB SSD",
        "price": 1299.99,
        "category": "Electronics",
        "stock": 25,
        "created_by": 1,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    2: {
        "product_id": 2,
        "name": "iPhone 15 Pro",
        "description": "Apple iPhone 15 Pro with 256GB storage",
        "price": 999.99,
        "category": "Electronics",
        "stock": 50,
        "created_by": 1,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    3: {
        "product_id": 3,
        "name": "Office Chair Ergonomic",
        "description": "Comfortable ergonomic office chair with lumbar support",
        "price": 249.99,
        "category": "Furniture",
        "stock": 15,
        "created_by": 2,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
}


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



@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'JWT Authentication API with Product CRUD',
        'version': '2.0.0',
        'endpoints': {
            'docs': '/docs',
            'auth': {
                'login': 'POST /auth/login',
                'register': 'POST /auth/register',
                'refresh': 'POST /auth/refresh',
                'logout': 'POST /auth/logout',
                'me': 'GET /auth/me',
                'change_password': 'POST /auth/change-password'
            },
            'products': {
                'list': 'GET /api/products',
                'get': 'GET /api/products/{id}',
                'create': 'POST /api/products',
                'update': 'PUT /api/products/{id}',
                'delete': 'DELETE /api/products/{id}'
            }
        },
        'test_accounts': {
            'admin': {'username': 'admin', 'password': 'admin123'},
            'user': {'username': 'user1', 'password': 'user123'}
        }
    }), 200


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
    # Chỉ xóa refresh token khỏi database
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


# ============================================================================
# Product CRUD Endpoints
# ============================================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products with optional filters"""
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    products = list(PRODUCTS_DB.values())
    
    # Apply filters
    if category:
        products = [p for p in products if p['category'].lower() == category.lower()]
    if min_price is not None:
        products = [p for p in products if p['price'] >= min_price]
    if max_price is not None:
        products = [p for p in products if p['price'] <= max_price]
    
    return jsonify({
        'total': len(products),
        'products': products
    }), 200


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    product = PRODUCTS_DB.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({'product': product}), 200


@app.route('/api/products', methods=['POST'])
@token_required
def create_product():
    """Create a new product (authenticated users)"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'price', 'category']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate price
    try:
        price = float(data['price'])
        if price < 0:
            return jsonify({'error': 'Price must be non-negative'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid price format'}), 400
    
    # Validate stock if provided
    stock = data.get('stock', 0)
    try:
        stock = int(stock)
        if stock < 0:
            return jsonify({'error': 'Stock must be non-negative'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid stock format'}), 400
    
    # Generate product ID
    product_id = max(PRODUCTS_DB.keys()) + 1 if PRODUCTS_DB else 1
    
    # Create product
    new_product = {
        'product_id': product_id,
        'name': data['name'],
        'description': data.get('description', ''),
        'price': price,
        'category': data['category'],
        'stock': stock,
        'created_by': request.current_user['user_id'],
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    PRODUCTS_DB[product_id] = new_product
    
    return jsonify({
        'message': 'Product created successfully',
        'product': new_product
    }), 201


@app.route('/api/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(product_id):
    """Update a product (owner or admin only)"""
    product = PRODUCTS_DB.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Check permission: owner or admin
    if product['created_by'] != request.current_user['user_id'] and request.current_user['role'] != 'admin':
        return jsonify({'error': 'You do not have permission to update this product'}), 403
    
    data = request.get_json()
    
    # Update fields if provided
    if 'name' in data:
        product['name'] = data['name']
    
    if 'description' in data:
        product['description'] = data['description']
    
    if 'price' in data:
        try:
            price = float(data['price'])
            if price < 0:
                return jsonify({'error': 'Price must be non-negative'}), 400
            product['price'] = price
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid price format'}), 400
    
    if 'category' in data:
        product['category'] = data['category']
    
    if 'stock' in data:
        try:
            stock = int(data['stock'])
            if stock < 0:
                return jsonify({'error': 'Stock must be non-negative'}), 400
            product['stock'] = stock
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid stock format'}), 400
    
    product['updated_at'] = datetime.utcnow().isoformat()
    
    return jsonify({
        'message': 'Product updated successfully',
        'product': product
    }), 200


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(product_id):
    """Delete a product (owner or admin only)"""
    product = PRODUCTS_DB.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Check permission: owner or admin
    if product['created_by'] != request.current_user['user_id'] and request.current_user['role'] != 'admin':
        return jsonify({'error': 'You do not have permission to delete this product'}), 403
    
    del PRODUCTS_DB[product_id]
    
    return jsonify({
        'message': 'Product deleted successfully',
        'deleted_product': {
            'product_id': product['product_id'],
            'name': product['name']
        }
    }), 200


# ============================================================================
# Documentation
# ============================================================================

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
    return send_file('openapi.yaml', mimetype='text/yaml')


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 JWT Authentication API v2.0 - Product CRUD")
    print("="*70)
    print(f"\n📍 Server: http://localhost:5000")
    print(f"📖 API Docs: http://localhost:5000/docs")
    print(f"\n👤 Test Accounts:")
    print(f"   Admin:  username=admin  password=admin123")
    print(f"   User:   username=user1  password=user123")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, port=5000)

