from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from functools import wraps
import jwt


def create_app():
    app = Flask(__name__)
    
    # JWT Secret key (in production, use environment variable)
    app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_ALGORITHM'] = 'HS256'

    # simple in-memory store
    app.config['products'] = [
        {'id': 1, 'name': 'Widget', 'price': 9.99},
        {'id': 2, 'name': 'Gadget', 'price': 12.49},
        {'id': 3, 'name': 'Doodad', 'price': 7.75},
        {'id': 4, 'name': 'Thingamajig', 'price': 15.00},
        {'id': 5, 'name': 'Contraption', 'price': 22.50},
        {'id': 6, 'name': 'Device', 'price': 18.00},
        {'id': 7, 'name': 'Apparatus', 'price': 11.25},
        {'id': 8, 'name': 'Gizmo', 'price': 14.30},
        {'id': 9, 'name': 'Instrument', 'price': 19.99},
    ]
    
    # Revoked tokens blacklist (in production, use Redis or database)
    app.config['revoked_tokens'] = set()
    
    # Demo users with roles
    app.config['users'] = {
        'admin': {'password': 'secret', 'role': 'admin'},
        'user': {'password': 'pass123', 'role': 'user'},
    }
    
    # Token expiry times (configurable)
    ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)
    REFRESH_TOKEN_EXPIRY = timedelta(days=7)

    # helper to compute the next id on-demand from current products
    def _get_next_id():
        """Return next id equal to max(existing ids) + 1.

        This computes the id each time so the in-memory store never gets
        out-of-sync (e.g. when products are modified/deleted elsewhere).
        """
        products = app.config.get('products', [])
        if not products:
            return 1
        max_id = max((p.get('id', 0) for p in products), default=0)
        return max_id + 1
    
    def _generate_jwt_token(username, role, token_type='access'):
        """Generate a JWT token with claims."""
        expiry = datetime.utcnow() + (ACCESS_TOKEN_EXPIRY if token_type == 'access' else REFRESH_TOKEN_EXPIRY)
        payload = {
            'sub': username,  # subject (user identifier)
            'role': role,
            'type': token_type,
            'iat': datetime.utcnow(),  # issued at
            'exp': expiry  # expiration
        }
        token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['JWT_ALGORITHM'])
        return token, expiry
    
    def _decode_jwt_token(token):
        """Decode and validate JWT token. Returns payload or None."""
        try:
            # check if token is revoked
            if token in app.config['revoked_tokens']:
                return None
            
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=[app.config['JWT_ALGORITHM']])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # token expired
        except jwt.InvalidTokenError:
            return None  # invalid token
    
    def _validate_token(token, token_type='access'):
        """Validate JWT token and return payload if valid."""
        payload = _decode_jwt_token(token)
        if not payload:
            return None
        if payload.get('type') != token_type:
            return None
        return payload
    
    def _get_token_from_request():
        """Extract token from Authorization header or X-Auth-Token."""
        auth = request.headers.get('Authorization', '')
        if auth and auth.startswith('Bearer '):
            return auth.split(' ', 1)[1]
        return request.headers.get('X-Auth-Token')
    
    def require_token(func):
        """Decorator to require valid JWT access token."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = _get_token_from_request()
            if not token:
                return jsonify({'error': 'unauthorized', 'message': 'token missing'}), 401
            
            token_data = _validate_token(token, 'access')
            if not token_data:
                return jsonify({'error': 'unauthorized', 'message': 'invalid or expired access token'}), 401
            
            # attach user info from JWT claims to request context
            request.current_user = token_data['sub']
            request.current_role = token_data['role']
            return func(*args, **kwargs)
        return wrapper
    
    def require_role(*roles):
        """Decorator to require specific role(s). Use after @require_token."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not hasattr(request, 'current_role') or request.current_role not in roles:
                    return jsonify({'error': 'forbidden', 'message': f'requires role: {", ".join(roles)}'}), 403
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @app.route('/api/sessions', methods=['POST'])
    def login():
        """Login endpoint: returns access_token and refresh_token."""
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        
        user = app.config['users'].get(username)
        if not user or user['password'] != password:
            return jsonify({'error': 'invalid credentials'}), 401
        
        # generate both JWT tokens
        access_token, access_expiry = _generate_jwt_token(username, user['role'], 'access')
        refresh_token, refresh_expiry = _generate_jwt_token(username, user['role'], 'refresh')
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(ACCESS_TOKEN_EXPIRY.total_seconds()),
            'user': username,
            'role': user['role']
        }), 200
    
    @app.route('/api/sessions/refresh', methods=['POST'])
    def refresh():
        """Refresh endpoint: accepts refresh_token, returns new access_token."""
        data = request.get_json() or {}
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'refresh_token required'}), 400
        
        token_data = _validate_token(refresh_token, 'refresh')
        if not token_data:
            return jsonify({'error': 'invalid or expired refresh token'}), 401
        
        # generate new JWT access token
        access_token, access_expiry = _generate_jwt_token(token_data['sub'], token_data['role'], 'access')
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': int(ACCESS_TOKEN_EXPIRY.total_seconds())
        }), 200
    
    @app.route('/api/sessions/logout', methods=['POST'])
    @require_token
    def logout():
        """Logout endpoint: revokes the current access token."""
        token = _get_token_from_request()
        if token:
            app.config['revoked_tokens'].add(token)
        return jsonify({'message': 'logged out successfully'}), 200

    @app.route('/api/products', methods=['GET'])
    def list_products():
        return jsonify(app.config['products']), 200

    @app.route('/api/products', methods=['POST'])%
    @require_token
    @require_role('admin')  # only admin can create products
    def create_product():
        data = request.get_json() or {}
        name = data.get('name')
        price = data.get('price')
        if not name:
            return jsonify({'error': 'name required'}), 400

        # compute next id from current products to avoid any drift
        existing_ids = {p.get('id') for p in app.config.get('products', [])}
        nid = _get_next_id()
        # in the rare case of a collision (concurrent manual edits), bump until unique
        while nid in existing_ids:
            nid += 1

        product = {'id': nid, 'name': name, 'price': price}
        app.config['products'].append(product)
        return jsonify(product), 201

    @app.route('/api/products/<int:product_id>', methods=['PUT'])
    @require_token
    def update_product(product_id):
        data = request.get_json() or {}
        for p in app.config['products']:
            if p['id'] == product_id:
                p['name'] = data.get('name', p['name'])
                p['price'] = data.get('price', p.get('price'))
                return jsonify(p), 200
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/products/<int:product_id>', methods=['DELETE'])
    @require_token
    @require_role('admin')  # only admin can delete products
    def delete_product(product_id):
        prods = app.config['products']
        for i, p in enumerate(prods):
            if p['id'] == product_id:
                prods.pop(i)
                return '', 204
        return jsonify({'error': 'not found'}), 404

    return app


if __name__ == '__main__':
    create_app().run(debug=True)

# Load testing command:
# $env:TEST_SCENARIO='load'; $env:VUS='50'; $env:DURATION='30s'
# k6 run .\k6_test.js

# Stress testing command:
# $env:TEST_SCENARIO='stress'; $env:START_VUS='10'; $env:PEAK_VUS='200'
# k6 run .\k6_test.js

# Spike testing command:
# $env:TEST_SCENARIO='spike'; $env:BASELINE_VUS='5'; $env:SPIKE_VUS='300'; $env:SPIKE_DURATION='15s'
# k6 run .\k6_test.js

# Soak testing command:
# $env:TEST_SCENARIO='soak'; $env:VUS='10'; $env:DURATION='30m'
# k6 run .\k6_test.js

# Scale testing command:
# $env:TEST_SCENARIO='scalability'; $env:S1='10'; $env:S2='50'; $env:S3='150'
# k6 run .\k6_test.js