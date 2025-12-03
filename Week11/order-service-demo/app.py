"""
Order Service API
Demo implementation với REST CRUD, Query endpoint và Webhook notifications
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
import uuid
import hmac
import hashlib
import requests
import threading
from functools import wraps

app = Flask(__name__)
CORS(app)

# ============= In-memory Data Store =============
orders_db = {}
webhooks_db = {}

# ============= Helper Functions =============

def generate_id(prefix):
    """Generate unique ID với prefix"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def get_current_time():
    """Get current UTC time"""
    return datetime.now(timezone.utc).isoformat()

def calculate_total(items):
    """Tính tổng tiền đơn hàng"""
    return sum(item['quantity'] * item['unitPrice'] for item in items)

def generate_webhook_secret():
    """Generate webhook secret"""
    return f"whsec_{uuid.uuid4().hex}"

def create_webhook_signature(payload, secret):
    """Tạo HMAC signature cho webhook payload"""
    message = str(payload).encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return f"sha256={signature}"

def send_webhook_notification(event_type, order_data, previous_status=None):
    """Gửi webhook notification đến tất cả registered webhooks"""
    def send_async():
        for webhook_id, webhook in webhooks_db.items():
            if not webhook.get('isActive', True):
                continue
            if event_type not in webhook.get('events', []):
                continue
            
            payload = {
                'id': generate_id('evt'),
                'event': event_type,
                'timestamp': get_current_time(),
                'data': {
                    'order': order_data
                }
            }
            
            if previous_status:
                payload['data']['previousStatus'] = previous_status
            
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Event': event_type,
                'X-Webhook-Id': webhook_id
            }
            
            if webhook.get('secret'):
                headers['X-Webhook-Signature'] = create_webhook_signature(payload, webhook['secret'])
            
            try:
                response = requests.post(
                    webhook['url'],
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                print(f"Webhook sent to {webhook['url']}: {response.status_code}")
            except Exception as e:
                print(f"Webhook failed for {webhook['url']}: {str(e)}")
    
    # Gửi webhook async để không block response
    thread = threading.Thread(target=send_async)
    thread.daemon = True
    thread.start()

def error_response(code, message, details=None, status_code=400):
    """Tạo error response chuẩn"""
    response = {
        'code': code,
        'message': message
    }
    if details:
        response['details'] = details
    return jsonify(response), status_code

def validate_order_data(data, is_update=False):
    """Validate order data"""
    errors = []
    
    if not is_update or 'customerId' in data:
        if not data.get('customerId'):
            errors.append({'field': 'customerId', 'message': 'customerId is required'})
    
    if not is_update or 'items' in data:
        items = data.get('items', [])
        if not items:
            errors.append({'field': 'items', 'message': 'At least one item is required'})
        else:
            for i, item in enumerate(items):
                if not item.get('productId'):
                    errors.append({'field': f'items[{i}].productId', 'message': 'productId is required'})
                if not item.get('productName'):
                    errors.append({'field': f'items[{i}].productName', 'message': 'productName is required'})
                if not item.get('quantity') or item.get('quantity', 0) < 1:
                    errors.append({'field': f'items[{i}].quantity', 'message': 'quantity must be at least 1'})
                if item.get('unitPrice') is None or item.get('unitPrice', 0) < 0:
                    errors.append({'field': f'items[{i}].unitPrice', 'message': 'unitPrice must be non-negative'})
    
    return errors

# ============= CRUD Endpoints for Orders =============

@app.route('/api/v1/orders', methods=['GET'])
def get_orders():
    """GET /orders - Lấy danh sách tất cả orders"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # Validate pagination
    page = max(1, page)
    limit = max(1, min(100, limit))
    
    # Get all orders sorted by createdAt desc
    all_orders = sorted(
        orders_db.values(),
        key=lambda x: x['createdAt'],
        reverse=True
    )
    
    # Paginate
    total = len(all_orders)
    start = (page - 1) * limit
    end = start + limit
    paginated_orders = all_orders[start:end]
    
    return jsonify({
        'data': paginated_orders,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'totalPages': (total + limit - 1) // limit if total > 0 else 0
        }
    })

@app.route('/api/v1/orders', methods=['POST'])
def create_order():
    """POST /orders - Tạo order mới"""
    data = request.get_json()
    
    if not data:
        return error_response('BAD_REQUEST', 'Request body is required')
    
    # Validate
    errors = validate_order_data(data)
    if errors:
        return error_response('VALIDATION_ERROR', 'Invalid request body', errors)
    
    # Create order
    order_id = generate_id('ord')
    now = get_current_time()
    
    order = {
        'id': order_id,
        'customerId': data['customerId'],
        'items': data['items'],
        'totalAmount': calculate_total(data['items']),
        'status': 'pending',
        'shippingAddress': data.get('shippingAddress'),
        'notes': data.get('notes'),
        'createdAt': now,
        'updatedAt': now
    }
    
    orders_db[order_id] = order
    
    # Send webhook notification
    send_webhook_notification('order.created', order)
    
    return jsonify(order), 201

@app.route('/api/v1/orders/<order_id>', methods=['GET'])
def get_order_by_id(order_id):
    """GET /orders/{orderId} - Lấy thông tin một order"""
    order = orders_db.get(order_id)
    
    if not order:
        return error_response('NOT_FOUND', 'Order not found', status_code=404)
    
    return jsonify(order)

@app.route('/api/v1/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    """PUT /orders/{orderId} - Cập nhật toàn bộ order"""
    order = orders_db.get(order_id)
    
    if not order:
        return error_response('NOT_FOUND', 'Order not found', status_code=404)
    
    data = request.get_json()
    
    if not data:
        return error_response('BAD_REQUEST', 'Request body is required')
    
    # Validate
    errors = validate_order_data(data)
    if errors:
        return error_response('VALIDATION_ERROR', 'Invalid request body', errors)
    
    # Validate status
    valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    if data.get('status') and data['status'] not in valid_statuses:
        return error_response('VALIDATION_ERROR', 'Invalid status', [
            {'field': 'status', 'message': f'Status must be one of: {", ".join(valid_statuses)}'}
        ])
    
    previous_status = order['status']
    
    # Update order
    order['customerId'] = data['customerId']
    order['items'] = data['items']
    order['totalAmount'] = calculate_total(data['items'])
    order['status'] = data.get('status', order['status'])
    order['shippingAddress'] = data.get('shippingAddress')
    order['notes'] = data.get('notes')
    order['updatedAt'] = get_current_time()
    
    orders_db[order_id] = order
    
    # Send webhook notifications
    send_webhook_notification('order.updated', order)
    if previous_status != order['status']:
        send_webhook_notification('order.status_changed', order, previous_status)
    
    return jsonify(order)

@app.route('/api/v1/orders/<order_id>', methods=['PATCH'])
def patch_order(order_id):
    """PATCH /orders/{orderId} - Cập nhật một phần order"""
    order = orders_db.get(order_id)
    
    if not order:
        return error_response('NOT_FOUND', 'Order not found', status_code=404)
    
    data = request.get_json()
    
    if not data:
        return error_response('BAD_REQUEST', 'Request body is required')
    
    # Validate status if provided
    valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    if data.get('status') and data['status'] not in valid_statuses:
        return error_response('VALIDATION_ERROR', 'Invalid status', [
            {'field': 'status', 'message': f'Status must be one of: {", ".join(valid_statuses)}'}
        ])
    
    previous_status = order['status']
    
    # Partial update
    if 'status' in data:
        order['status'] = data['status']
    if 'shippingAddress' in data:
        order['shippingAddress'] = data['shippingAddress']
    if 'notes' in data:
        order['notes'] = data['notes']
    
    order['updatedAt'] = get_current_time()
    orders_db[order_id] = order
    
    # Send webhook notifications
    send_webhook_notification('order.updated', order)
    if previous_status != order['status']:
        send_webhook_notification('order.status_changed', order, previous_status)
    
    return jsonify(order)

@app.route('/api/v1/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """DELETE /orders/{orderId} - Xóa order"""
    order = orders_db.get(order_id)
    
    if not order:
        return error_response('NOT_FOUND', 'Order not found', status_code=404)
    
    # Send webhook notification before deleting
    send_webhook_notification('order.deleted', order)
    
    del orders_db[order_id]
    
    return '', 204

# ============= Query Endpoint =============

@app.route('/api/v1/orders/search', methods=['GET'])
def search_orders():
    """GET /orders/search - Tìm kiếm orders"""
    # Get query parameters
    customer_id = request.args.get('customerId')
    status = request.args.get('status')
    from_date = request.args.get('fromDate')
    to_date = request.args.get('toDate')
    min_total = request.args.get('minTotal', type=float)
    max_total = request.args.get('maxTotal', type=float)
    sort_by = request.args.get('sortBy', 'createdAt')
    sort_order = request.args.get('sortOrder', 'desc')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # Validate pagination
    page = max(1, page)
    limit = max(1, min(100, limit))
    
    # Validate sort parameters
    valid_sort_fields = ['createdAt', 'totalAmount', 'status']
    if sort_by not in valid_sort_fields:
        sort_by = 'createdAt'
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Filter orders
    filtered_orders = list(orders_db.values())
    
    if customer_id:
        filtered_orders = [o for o in filtered_orders if o['customerId'] == customer_id]
    
    if status:
        filtered_orders = [o for o in filtered_orders if o['status'] == status]
    
    if from_date:
        filtered_orders = [o for o in filtered_orders if o['createdAt'] >= from_date]
    
    if to_date:
        filtered_orders = [o for o in filtered_orders if o['createdAt'] <= to_date]
    
    if min_total is not None:
        filtered_orders = [o for o in filtered_orders if o['totalAmount'] >= min_total]
    
    if max_total is not None:
        filtered_orders = [o for o in filtered_orders if o['totalAmount'] <= max_total]
    
    # Sort
    reverse = sort_order == 'desc'
    filtered_orders.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
    
    # Paginate
    total = len(filtered_orders)
    start = (page - 1) * limit
    end = start + limit
    paginated_orders = filtered_orders[start:end]
    
    # Build applied filters
    filters = {}
    if customer_id:
        filters['customerId'] = customer_id
    if status:
        filters['status'] = status
    if from_date:
        filters['fromDate'] = from_date
    if to_date:
        filters['toDate'] = to_date
    if min_total is not None:
        filters['minTotal'] = min_total
    if max_total is not None:
        filters['maxTotal'] = max_total
    
    return jsonify({
        'data': paginated_orders,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'totalPages': (total + limit - 1) // limit if total > 0 else 0
        },
        'filters': filters
    })

# ============= Webhook Endpoints =============

@app.route('/api/v1/webhooks', methods=['GET'])
def get_webhooks():
    """GET /webhooks - Lấy danh sách webhooks"""
    return jsonify(list(webhooks_db.values()))

@app.route('/api/v1/webhooks', methods=['POST'])
def register_webhook():
    """POST /webhooks - Đăng ký webhook mới"""
    data = request.get_json()
    
    if not data:
        return error_response('BAD_REQUEST', 'Request body is required')
    
    # Validate
    errors = []
    if not data.get('url'):
        errors.append({'field': 'url', 'message': 'url is required'})
    if not data.get('events') or len(data.get('events', [])) == 0:
        errors.append({'field': 'events', 'message': 'At least one event is required'})
    
    valid_events = ['order.created', 'order.updated', 'order.status_changed', 'order.deleted']
    for event in data.get('events', []):
        if event not in valid_events:
            errors.append({'field': 'events', 'message': f'Invalid event: {event}'})
    
    if errors:
        return error_response('VALIDATION_ERROR', 'Invalid request body', errors)
    
    # Create webhook
    webhook_id = generate_id('wh')
    now = get_current_time()
    
    webhook = {
        'id': webhook_id,
        'url': data['url'],
        'events': data['events'],
        'secret': data.get('secret') or generate_webhook_secret(),
        'isActive': True,
        'description': data.get('description'),
        'createdAt': now,
        'updatedAt': now
    }
    
    webhooks_db[webhook_id] = webhook
    
    return jsonify(webhook), 201

@app.route('/api/v1/webhooks/<webhook_id>', methods=['GET'])
def get_webhook_by_id(webhook_id):
    """GET /webhooks/{webhookId} - Lấy thông tin webhook"""
    webhook = webhooks_db.get(webhook_id)
    
    if not webhook:
        return error_response('NOT_FOUND', 'Webhook not found', status_code=404)
    
    return jsonify(webhook)

@app.route('/api/v1/webhooks/<webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    """PUT /webhooks/{webhookId} - Cập nhật webhook"""
    webhook = webhooks_db.get(webhook_id)
    
    if not webhook:
        return error_response('NOT_FOUND', 'Webhook not found', status_code=404)
    
    data = request.get_json()
    
    if not data:
        return error_response('BAD_REQUEST', 'Request body is required')
    
    # Validate events if provided
    valid_events = ['order.created', 'order.updated', 'order.status_changed', 'order.deleted']
    if data.get('events'):
        for event in data['events']:
            if event not in valid_events:
                return error_response('VALIDATION_ERROR', 'Invalid event', [
                    {'field': 'events', 'message': f'Invalid event: {event}'}
                ])
    
    # Update
    if 'url' in data:
        webhook['url'] = data['url']
    if 'events' in data:
        webhook['events'] = data['events']
    if 'isActive' in data:
        webhook['isActive'] = data['isActive']
    if 'description' in data:
        webhook['description'] = data['description']
    
    webhook['updatedAt'] = get_current_time()
    webhooks_db[webhook_id] = webhook
    
    return jsonify(webhook)

@app.route('/api/v1/webhooks/<webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    """DELETE /webhooks/{webhookId} - Xóa webhook"""
    webhook = webhooks_db.get(webhook_id)
    
    if not webhook:
        return error_response('NOT_FOUND', 'Webhook not found', status_code=404)
    
    del webhooks_db[webhook_id]
    
    return '', 204

@app.route('/api/v1/webhooks/<webhook_id>/test', methods=['POST'])
def test_webhook(webhook_id):
    """POST /webhooks/{webhookId}/test - Test webhook"""
    webhook = webhooks_db.get(webhook_id)
    
    if not webhook:
        return error_response('NOT_FOUND', 'Webhook not found', status_code=404)
    
    # Create test payload
    test_payload = {
        'id': generate_id('evt'),
        'event': 'test',
        'timestamp': get_current_time(),
        'data': {
            'message': 'This is a test webhook notification',
            'webhookId': webhook_id
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Event': 'test',
        'X-Webhook-Id': webhook_id
    }
    
    if webhook.get('secret'):
        headers['X-Webhook-Signature'] = create_webhook_signature(test_payload, webhook['secret'])
    
    try:
        start_time = datetime.now()
        response = requests.post(
            webhook['url'],
            json=test_payload,
            headers=headers,
            timeout=10
        )
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return jsonify({
            'success': 200 <= response.status_code < 300,
            'statusCode': response.status_code,
            'responseTime': response_time,
            'message': 'Webhook test completed'
        })
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'statusCode': None,
            'responseTime': 10000,
            'message': 'Webhook request timed out'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'statusCode': None,
            'responseTime': None,
            'message': f'Webhook request failed: {str(e)}'
        })

# ============= Demo Webhook Receiver =============

@app.route('/demo/webhook-receiver', methods=['POST'])
def demo_webhook_receiver():
    """Demo endpoint để nhận webhook notifications"""
    data = request.get_json()
    event = request.headers.get('X-Webhook-Event', 'unknown')
    signature = request.headers.get('X-Webhook-Signature', 'none')
    
    print(f"\n{'='*50}")
    print(f"WEBHOOK RECEIVED")
    print(f"Event: {event}")
    print(f"Signature: {signature}")
    print(f"Payload: {data}")
    print(f"{'='*50}\n")
    
    return jsonify({'received': True, 'event': event})

# ============= Health Check =============

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': get_current_time(),
        'ordersCount': len(orders_db),
        'webhooksCount': len(webhooks_db)
    })

# ============= Create Sample Data =============

def create_sample_data():
    """Tạo dữ liệu mẫu"""
    # Sample orders
    sample_orders = [
        {
            'customerId': 'cust_001',
            'items': [
                {'productId': 'prod_001', 'productName': 'Laptop Dell XPS 15', 'quantity': 1, 'unitPrice': 25000000},
                {'productId': 'prod_002', 'productName': 'Mouse Logitech MX Master', 'quantity': 1, 'unitPrice': 2500000}
            ],
            'status': 'delivered',
            'shippingAddress': {
                'street': '123 Nguyen Hue',
                'city': 'Ho Chi Minh',
                'district': 'District 1',
                'postalCode': '700000',
                'country': 'Vietnam'
            }
        },
        {
            'customerId': 'cust_002',
            'items': [
                {'productId': 'prod_003', 'productName': 'iPhone 15 Pro', 'quantity': 2, 'unitPrice': 28000000}
            ],
            'status': 'processing',
            'shippingAddress': {
                'street': '456 Le Loi',
                'city': 'Ha Noi',
                'district': 'Hoan Kiem',
                'postalCode': '100000',
                'country': 'Vietnam'
            }
        },
        {
            'customerId': 'cust_001',
            'items': [
                {'productId': 'prod_004', 'productName': 'AirPods Pro', 'quantity': 1, 'unitPrice': 5500000}
            ],
            'status': 'pending'
        }
    ]
    
    for order_data in sample_orders:
        order_id = generate_id('ord')
        now = get_current_time()
        orders_db[order_id] = {
            'id': order_id,
            'customerId': order_data['customerId'],
            'items': order_data['items'],
            'totalAmount': calculate_total(order_data['items']),
            'status': order_data['status'],
            'shippingAddress': order_data.get('shippingAddress'),
            'notes': order_data.get('notes'),
            'createdAt': now,
            'updatedAt': now
        }
    
    # Sample webhook (pointing to demo receiver)
    webhook_id = generate_id('wh')
    now = get_current_time()
    webhooks_db[webhook_id] = {
        'id': webhook_id,
        'url': 'http://localhost:5000/demo/webhook-receiver',
        'events': ['order.created', 'order.updated', 'order.status_changed', 'order.deleted'],
        'secret': generate_webhook_secret(),
        'isActive': True,
        'description': 'Demo webhook receiver',
        'createdAt': now,
        'updatedAt': now
    }

if __name__ == '__main__':
    create_sample_data()
    print("\n" + "="*60)
    print("Order Service API started!")
    print("="*60)
    print("\nEndpoints:")
    print("  - Orders CRUD:    /api/v1/orders")
    print("  - Search Orders:  /api/v1/orders/search")
    print("  - Webhooks:       /api/v1/webhooks")
    print("  - Health Check:   /health")
    print("\nSample data created:")
    print(f"  - {len(orders_db)} orders")
    print(f"  - {len(webhooks_db)} webhooks")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)
