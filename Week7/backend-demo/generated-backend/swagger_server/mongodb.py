"""
MongoDB Integration for Generated Backend
"""
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

# MongoDB Connection
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client[os.getenv('MONGODB_DATABASE', 'product_api')]

# Collections
products_collection = db['products']
users_collection = db['users']


def create_indexes():
    """Create indexes for better performance"""
    try:
        # Products indexes
        products_collection.create_index('category')
        products_collection.create_index('price')
        products_collection.create_index('created_by')
        
        # Users indexes
        users_collection.create_index('username', unique=True)
        users_collection.create_index('email', unique=True)
        
        print("✅ MongoDB indexes created")
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")


# Product CRUD Operations
def get_all_products(category=None, min_price=None, max_price=None):
    """Get all products with optional filters"""
    query = {}
    
    if category:
        query['category'] = {'$regex': category, '$options': 'i'}
    
    if min_price is not None or max_price is not None:
        query['price'] = {}
        if min_price is not None:
            query['price']['$gte'] = float(min_price)
        if max_price is not None:
            query['price']['$lte'] = float(max_price)
    
    products = list(products_collection.find(query))
    
    # Convert ObjectId to string
    for product in products:
        product['id'] = str(product['_id'])
        del product['_id']
    
    return products


def get_product_by_id(product_id):
    """Get single product by ID"""
    if not ObjectId.is_valid(product_id):
        return None
    
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    
    if product:
        product['id'] = str(product['_id'])
        del product['_id']
    
    return product


def create_product(product_data, user_id):
    """Create new product"""
    new_product = {
        'name': product_data.get('name'),
        'description': product_data.get('description'),
        'price': float(product_data.get('price', 0)),
        'category': product_data.get('category'),
        'stock': int(product_data.get('stock', 0)),
        'created_by': user_id,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    result = products_collection.insert_one(new_product)
    new_product['id'] = str(result.inserted_id)
    
    return new_product


def update_product(product_id, product_data):
    """Update existing product"""
    if not ObjectId.is_valid(product_id):
        return None
    
    update_doc = {'updated_at': datetime.utcnow()}
    
    for field in ['name', 'description', 'category']:
        if field in product_data:
            update_doc[field] = product_data[field]
    
    if 'price' in product_data:
        update_doc['price'] = float(product_data['price'])
    
    if 'stock' in product_data:
        update_doc['stock'] = int(product_data['stock'])
    
    result = products_collection.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': update_doc}
    )
    
    if result.matched_count > 0:
        return get_product_by_id(product_id)
    
    return None


def delete_product(product_id):
    """Delete product"""
    if not ObjectId.is_valid(product_id):
        return False
    
    result = products_collection.delete_one({'_id': ObjectId(product_id)})
    return result.deleted_count > 0


# Initialize on import
create_indexes()