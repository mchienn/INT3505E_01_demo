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
    app.config['next_id'] = 1

    @app.route('/api/sessions', methods=['POST'])
    def login():
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        # demo-only credentials
        if username == 'admin' and password == 'secret':
            return jsonify({'token': 'fake-token'}), 200
        return jsonify({'error': 'invalid credentials'}), 401

    @app.route('/api/products', methods=['GET'])
    def list_products():
        return jsonify(app.config['products']), 200

    @app.route('/api/products', methods=['POST'])
    def create_product():
        data = request.get_json() or {}
        name = data.get('name')
        price = data.get('price')
        if not name:
            return jsonify({'error': 'name required'}), 400
        product = {'id': app.config['next_id'], 'name': name, 'price': price}
        app.config['next_id'] += 1
        app.config['products'].append(product)
        return jsonify(product), 201

    @app.route('/api/products/<int:product_id>', methods=['PUT'])
    def update_product(product_id):
        data = request.get_json() or {}
        for p in app.config['products']:
            if p['id'] == product_id:
                p['name'] = data.get('name', p['name'])
                p['price'] = data.get('price', p.get('price'))
                return jsonify(p), 200
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/products/<int:product_id>', methods=['DELETE'])
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
