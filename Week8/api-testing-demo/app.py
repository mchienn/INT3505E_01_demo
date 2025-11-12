from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)

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
    # auth tokens (in-memory for demo)
    app.config['tokens'] = set()

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

    @app.route('/api/sessions', methods=['POST'])
    def login():
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        # demo-only credentials
        if username == 'admin' and password == 'secret':
            # generate a short-lived demo token
            from uuid import uuid4
            token = f"token-{uuid4().hex}"
            app.config['tokens'].add(token)
            return jsonify({'token': token}), 200
        return jsonify({'error': 'invalid credentials'}), 401


    def _require_auth():
        # Accept standard `Authorization: Bearer <token>` header or
        # a fallback `X-Auth-Token` header for convenience in simple clients.
        auth = request.headers.get('Authorization', '')
        if auth and auth.startswith('Bearer '):
            return auth.split(' ', 1)[1]
        # fallback header
        return request.headers.get('X-Auth-Token')


    def require_token(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            token = _require_auth()
            if not token or token not in app.config['tokens']:
                return jsonify({'error': 'unauthorized'}), 401
            return func(*args, **kwargs)

        return wrapper

    @app.route('/api/products', methods=['GET'])
    def list_products():
        return jsonify(app.config['products']), 200

    @app.route('/api/products', methods=['POST'])
    @require_token
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