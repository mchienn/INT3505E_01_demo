from flask import Flask, jsonify, request, send_from_directory, render_template_string
from datetime import datetime
import uuid
import os


def create_app():
    app = Flask(__name__)
    
    # In-memory storage for payments (in production, use database)
    app.config['payments'] = {}
    
    # ============================================
    # Docs Endpoints - Swagger UI
    # ============================================
    
    @app.route('/docs/v1')
    def docs_v1():
        """Swagger UI cho API V1"""
        return render_template_string(SWAGGER_UI_TEMPLATE, 
                                     spec_url='/openapi/v1.yaml',
                                     title='Payment API - Version 1')
    
    @app.route('/docs/v2')
    def docs_v2():
        """Swagger UI cho API V2"""
        return render_template_string(SWAGGER_UI_TEMPLATE,
                                     spec_url='/openapi/v2.yaml',
                                     title='Payment API - Version 2')
    
    @app.route('/docs')
    def docs_index():
        """Trang chủ docs - chọn version"""
        return render_template_string(DOCS_INDEX_TEMPLATE)
    
    @app.route('/openapi/v1.yaml')
    def openapi_v1():
        """Serve OpenAPI spec cho V1"""
        file_path = os.path.join(os.path.dirname(__file__), 'openapi-v1.yaml')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = app.response_class(
            response=content,
            mimetype='text/yaml; charset=utf-8'
        )
        return response
    
    @app.route('/openapi/v2.yaml')
    def openapi_v2():
        """Serve OpenAPI spec cho V2"""
        file_path = os.path.join(os.path.dirname(__file__), 'openapi-v2.yaml')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = app.response_class(
            response=content,
            mimetype='text/yaml; charset=utf-8'
        )
        return response
    
    # ============================================
    # V1 API - Payment API
    # ============================================
    
    @app.route('/api/v1/payments', methods=['POST'])
    def create_payment():
        """
        Tạo payment
        Body: { amount, currency, source }
        """
        data = request.get_json() or {}
        
        # Validation
        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        source = data.get('source')
        
        if not amount or amount <= 0:
            return jsonify({'error': 'amount must be positive'}), 400
        if not source:
            return jsonify({'error': 'source is required'}), 400
        
        # Create payment với V1 shape
        payment_id = str(uuid.uuid4())
        payment = {
            'id': payment_id,
            'amount': amount,
            'currency': currency,
            'source': source,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'version': 'v1'  # Mark as V1
        }
        
        app.config['payments'][payment_id] = payment
        
        # Trả về V1 shape - chỉ các fields cơ bản (không có description, metadata, updated_at)
        v1_response = {
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at']
        }
        return jsonify(v1_response), 201
    
    @app.route('/api/v1/payments/<payment_id>', methods=['GET'])
    def get_payment_v1(payment_id):
        """
        Lấy trạng thái payment - V1 shape (backward compatible)
        """
        payment = app.config['payments'].get(payment_id)
        if not payment:
            return jsonify({'error': 'payment not found'}), 404
        
        # Trả về V1 shape - chỉ các fields cơ bản
        v1_response = {
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at']
        }
        return jsonify(v1_response), 200
    
    # ============================================
    # V2 API - Payment API (Enhanced)
    # ============================================
    
    @app.route('/api/v2/payments', methods=['POST'])
    def create_payment_v2():
        """
        Tạo payment - V2 với description và metadata
        Body: { amount, currency, source, description?, metadata? }
        """
        data = request.get_json() or {}
        
        # Validation
        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        source = data.get('source')
        description = data.get('description')
        metadata = data.get('metadata')
        
        if not amount or amount <= 0:
            return jsonify({'error': 'amount must be positive'}), 400
        if not source:
            return jsonify({'error': 'source is required'}), 400
        
        # Create payment với V2 fields
        payment_id = str(uuid.uuid4())
        payment = {
            'id': payment_id,
            'amount': amount,
            'currency': currency,
            'source': source,
            'description': description,
            'metadata': metadata if metadata else {},
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'version': 'v2'
        }
        
        app.config['payments'][payment_id] = payment
        
        # Trả về V2 shape - enriched response
        return jsonify(payment), 201
    
    @app.route('/api/v2/payments/<payment_id>', methods=['GET'])
    def get_payment_v2(payment_id):
        """
        Lấy payment - V2 shape (enriched)
        """
        payment = app.config['payments'].get(payment_id)
        if not payment:
            return jsonify({'error': 'payment not found'}), 404
        
        # Nếu payment được tạo bởi V1, vẫn trả về V2 shape nhưng với null cho optional fields
        v2_response = {
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at'],
            'description': payment.get('description'),
            'metadata': payment.get('metadata'),
            'updated_at': payment.get('updated_at'),
            'version': payment.get('version', 'v1')
        }
        return jsonify(v2_response), 200
    
    @app.route('/api/v2/payments/<payment_id>', methods=['PATCH'])
    def update_payment_v2(payment_id):
        """
        Cập nhật payment - V2 only
        Body: { status?, metadata? }
        """
        payment = app.config['payments'].get(payment_id)
        if not payment:
            return jsonify({'error': 'payment not found'}), 404
        
        data = request.get_json() or {}
        
        # Update status
        if 'status' in data:
            valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
            if data['status'] not in valid_statuses:
                return jsonify({'error': 'invalid status'}), 400
            payment['status'] = data['status']
        
        # Update metadata (merge)
        if 'metadata' in data:
            if payment.get('metadata'):
                payment['metadata'].update(data['metadata'])
            else:
                payment['metadata'] = data['metadata']
        
        # Update timestamp và version
        payment['updated_at'] = datetime.utcnow().isoformat()
        payment['version'] = 'v2'
        
        # Trả về V2 shape
        v2_response = {
            'id': payment['id'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'source': payment['source'],
            'status': payment['status'],
            'created_at': payment['created_at'],
            'description': payment.get('description'),
            'metadata': payment.get('metadata'),
            'updated_at': payment.get('updated_at'),
            'version': payment.get('version', 'v1')
        }
        return jsonify(v2_response), 200
    
    @app.route('/api/v2/payments', methods=['GET'])
    def list_payments_v2():
        """
        Liệt kê payments - V2 only với filtering
        Query params: status?, currency?, limit?, offset?
        """
        status_filter = request.args.get('status')
        currency_filter = request.args.get('currency')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        payments = list(app.config['payments'].values())
        
        # Apply filters
        if status_filter:
            payments = [p for p in payments if p.get('status') == status_filter]
        if currency_filter:
            payments = [p for p in payments if p.get('currency') == currency_filter]
        
        # Convert to V2 shape
        v2_payments = []
        for p in payments:
            v2_payments.append({
                'id': p['id'],
                'amount': p['amount'],
                'currency': p['currency'],
                'source': p['source'],
                'status': p['status'],
                'created_at': p['created_at'],
                'description': p.get('description'),
                'metadata': p.get('metadata'),
                'updated_at': p.get('updated_at'),
                'version': p.get('version', 'v1')
            })
        
        # Pagination
        total = len(v2_payments)
        v2_payments = v2_payments[offset:offset + limit]
        
        return jsonify({
            'payments': v2_payments,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
    
    return app


# Swagger UI HTML Template
SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.3/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "{{ spec_url }}",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                tryItOutEnabled: true
            });
        };
    </script>
</body>
</html>
"""

# Docs Index Template
DOCS_INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment API Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }
        .versions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .version-card {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 30px;
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        .version-card:hover {
            border-color: #667eea;
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
        }
        .version-card h2 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.8em;
        }
        .version-card p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        .version-card .badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-top: 10px;
        }
        .features {
            list-style: none;
            margin-top: 15px;
        }
        .features li {
            padding: 5px 0;
            color: #555;
        }
        .features li:before {
            content: "✓ ";
            color: #667eea;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 Payment API</h1>
        <p class="subtitle">API Documentation - Chiến lược nâng cấp v1 → v2</p>
        
        <div class="versions">
            <a href="/docs/v1" class="version-card">
                <h2>Version 1</h2>
                <p>API đơn giản với các tính năng cơ bản</p>
                <ul class="features">
                    <li>POST /api/v1/payments</li>
                    <li>GET /api/v1/payments/{id}</li>
                </ul>
                <span class="badge">Legacy</span>
            </a>
            
            <a href="/docs/v2" class="version-card">
                <h2>Version 2</h2>
                <p>API nâng cao với các tính năng mới</p>
                <ul class="features">
                    <li>POST /api/v2/payments (với description, metadata)</li>
                    <li>GET /api/v2/payments/{id}</li>
                    <li>PATCH /api/v2/payments/{id} (NEW)</li>
                    <li>GET /api/v2/payments (NEW - List với filter)</li>
                </ul>
                <span class="badge">Enhanced</span>
            </a>
        </div>
    </div>
</body>
</html>
"""


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)

