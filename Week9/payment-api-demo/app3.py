from flask import Flask, request, jsonify
import uuid
from datetime import datetime

app = Flask(__name__)

# In-memory storage
payments = {}

@app.route('/api/payments', methods=['POST'])
def create_payment():
    version = request.headers.get('X-API-Version', 'v1')
    
    data = request.get_json() or {}
    if 'amount' not in data or 'source' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    payment_id = str(uuid.uuid4())
    payment = {
        'id': payment_id,
        'amount': data['amount'],
        'currency': data.get('currency', 'USD'),
        'source': data['source'],
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'description': data.get('description'),
        'metadata': data.get('metadata', {})
    }
    payments[payment_id] = payment

    if version == 'v2':
        return jsonify({
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at'],
            'description': payment['description'],
            'metadata': payment['metadata'],
            'version_used': 'v2 (Header)'
        }), 201
    else:
        return jsonify({
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at']
        }), 201

@app.route('/api/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    # Lấy version từ Header
    version = request.headers.get('X-API-Version', 'v1')
    
    payment = payments.get(payment_id)
    
    if not payment:
        return jsonify({'error': 'Not found'}), 404

    if version == 'v2':
        # V2 Response
        return jsonify({
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at'],
            'description': payment.get('description'),
            'metadata': payment.get('metadata'),
            'version_used': 'v2 (Header)'
        })
    else:
        # V1 Response
        return jsonify({
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at']
        })

if __name__ == '__main__':
    print("Running Header Versioning Demo on port 5002")
    print("Usage: Curl -H 'X-API-Version: v2' ...")
    app.run(debug=True, port=5002)
