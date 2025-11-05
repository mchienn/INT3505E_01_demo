"""
Product CRUD Routes
Handles all product operations: Create, Read, Update, Delete
"""
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.utils.auth import token_required

products_bp = Blueprint('products', __name__, url_prefix='/api/products')

# Global variables (will be set by app factory)
products_collection = None
jwt_manager = None


def init_product_routes(products_col, jwt_mgr):
    """Initialize routes with dependencies"""
    global products_collection, jwt_manager
    products_collection = products_col
    jwt_manager = jwt_mgr


@products_bp.route('', methods=['GET'])
def get_products():
    """
    Get all products with optional filters
    
    Query parameters:
    - category: Filter by category (case-insensitive substring match)
    - min_price: Minimum price
    - max_price: Maximum price
    - limit: Number of products to return (default: 100)
    - skip: Number of products to skip for pagination (default: 0)
    """
    try:
        # Build query from filters
        query = {}
        
        category = request.args.get('category')
        if category:
            query['category'] = {'$regex': category, '$options': 'i'}
        
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        if min_price is not None or max_price is not None:
            query['price'] = {}
            if min_price is not None:
                query['price']['$gte'] = min_price
            if max_price is not None:
                query['price']['$lte'] = max_price
        
        # Pagination
        limit = request.args.get('limit', default=100, type=int)
        skip = request.args.get('skip', default=0, type=int)
        
        # Query database
        products = list(products_collection.find(query).limit(limit).skip(skip))
        
        # Convert to response format
        product_list = []
        for product in products:
            product_response = ProductResponse(
                id=str(product['_id']),
                name=product['name'],
                description=product.get('description', ''),
                price=product['price'],
                category=product['category'],
                stock=product.get('stock', 0),
                created_by=product.get('created_by', ''),
                created_at=product.get('created_at', datetime.utcnow()).isoformat(),
                updated_at=product.get('updated_at', datetime.utcnow()).isoformat()
            )
            product_list.append(product_response.dict())
        
        return jsonify({
            'products': product_list,
            'total': len(product_list),
            'limit': limit,
            'skip': skip
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    """
    Get a single product by ID
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(product_id):
            return jsonify({'error': 'Invalid product ID'}), 400
        
        # Find product
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Convert to response format
        product_response = ProductResponse(
            id=str(product['_id']),
            name=product['name'],
            description=product.get('description', ''),
            price=product['price'],
            category=product['category'],
            stock=product.get('stock', 0),
            created_by=product.get('created_by', ''),
            created_at=product.get('created_at', datetime.utcnow()).isoformat(),
            updated_at=product.get('updated_at', datetime.utcnow()).isoformat()
        )
        
        return jsonify(product_response.dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('', methods=['POST'])
@token_required(lambda: jwt_manager)
def create_product(current_user):
    """
    Create a new product (requires authentication)
    
    Request body:
    {
        "name": "string",
        "description": "string",
        "price": number,
        "category": "string",
        "stock": number
    }
    """
    try:
        # Validate request data with Pydantic
        product_data = ProductCreate(**request.json)
        
        # Create new product
        new_product = {
            'name': product_data.name,
            'description': product_data.description,
            'price': product_data.price,
            'category': product_data.category,
            'stock': product_data.stock,
            'created_by': current_user['user_id'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = products_collection.insert_one(new_product)
        new_product['_id'] = result.inserted_id
        
        # Return product response
        product_response = ProductResponse(
            id=str(new_product['_id']),
            name=new_product['name'],
            description=new_product['description'],
            price=new_product['price'],
            category=new_product['category'],
            stock=new_product['stock'],
            created_by=new_product['created_by'],
            created_at=new_product['created_at'].isoformat(),
            updated_at=new_product['updated_at'].isoformat()
        )
        
        return jsonify(product_response.dict()), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>', methods=['PUT'])
@token_required(lambda: jwt_manager)
def update_product(current_user, product_id):
    """
    Update a product (requires authentication, owner or admin only)
    
    Request body (all fields optional):
    {
        "name": "string",
        "description": "string",
        "price": number,
        "category": "string",
        "stock": number
    }
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(product_id):
            return jsonify({'error': 'Invalid product ID'}), 400
        
        # Find product
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check authorization (owner or admin)
        if product['created_by'] != current_user['user_id'] and current_user['role'] != 'admin':
            return jsonify({'error': 'Unauthorized to update this product'}), 403
        
        # Validate update data with Pydantic
        update_data = ProductUpdate(**request.json)
        
        # Build update document (only include provided fields)
        update_doc = {'updated_at': datetime.utcnow()}
        
        if update_data.name is not None:
            update_doc['name'] = update_data.name
        if update_data.description is not None:
            update_doc['description'] = update_data.description
        if update_data.price is not None:
            update_doc['price'] = update_data.price
        if update_data.category is not None:
            update_doc['category'] = update_data.category
        if update_data.stock is not None:
            update_doc['stock'] = update_data.stock
        
        # Update product
        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': update_doc}
        )
        
        # Get updated product
        updated_product = products_collection.find_one({'_id': ObjectId(product_id)})
        
        # Return product response
        product_response = ProductResponse(
            id=str(updated_product['_id']),
            name=updated_product['name'],
            description=updated_product['description'],
            price=updated_product['price'],
            category=updated_product['category'],
            stock=updated_product['stock'],
            created_by=updated_product['created_by'],
            created_at=updated_product['created_at'].isoformat(),
            updated_at=updated_product['updated_at'].isoformat()
        )
        
        return jsonify(product_response.dict()), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<product_id>', methods=['DELETE'])
@token_required(lambda: jwt_manager)
def delete_product(current_user, product_id):
    """
    Delete a product (requires authentication, owner or admin only)
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(product_id):
            return jsonify({'error': 'Invalid product ID'}), 400
        
        # Find product
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Check authorization (owner or admin)
        if product['created_by'] != current_user['user_id'] and current_user['role'] != 'admin':
            return jsonify({'error': 'Unauthorized to delete this product'}), 403
        
        # Delete product
        products_collection.delete_one({'_id': ObjectId(product_id)})
        
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
