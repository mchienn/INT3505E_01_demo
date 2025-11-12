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


def _normalize_id(product_id):
    """Convert simple numeric IDs (1, 2, 3) to a valid ObjectId hex string."""
    if isinstance(product_id, int) or (isinstance(product_id, str) and str(product_id).isdigit()):
        numeric_value = int(product_id)
        # Convert decimal integer to 24-character hex string for ObjectId compatibility
        padded_hex = format(numeric_value, 'x').zfill(24)
        return padded_hex
    return str(product_id)


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
    
    # Convert ObjectId and datetime to JSON-serializable format
    for product in products:
        product['id'] = str(product['_id'])
        del product['_id']
        if 'created_at' in product:
            product['created_at'] = product['created_at'].isoformat() if hasattr(product['created_at'], 'isoformat') else str(product['created_at'])
        if 'updated_at' in product:
            product['updated_at'] = product['updated_at'].isoformat() if hasattr(product['updated_at'], 'isoformat') else str(product['updated_at'])
    
    return products


def get_product_by_id(product_id):
    """Get single product by ID"""
    product_id = _normalize_id(product_id)
    
    if not ObjectId.is_valid(product_id):
        return None
    
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    
    if product:
        product['id'] = str(product['_id'])
        del product['_id']
        if 'created_at' in product:
            product['created_at'] = product['created_at'].isoformat() if hasattr(product['created_at'], 'isoformat') else str(product['created_at'])
        if 'updated_at' in product:
            product['updated_at'] = product['updated_at'].isoformat() if hasattr(product['updated_at'], 'isoformat') else str(product['updated_at'])
    
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
    
    # Convert to JSON-serializable format
    new_product['id'] = str(result.inserted_id)
    new_product['created_at'] = new_product['created_at'].isoformat()
    new_product['updated_at'] = new_product['updated_at'].isoformat()
    # Remove _id field to avoid ObjectId serialization error
    if '_id' in new_product:
        del new_product['_id']
    
    return new_product


def update_product(product_id, product_data):
    """Update existing product"""
    product_id = _normalize_id(product_id)
    
    if not ObjectId.is_valid(product_id):
        return None
    
    existing = products_collection.find_one({'_id': ObjectId(product_id)})
    if not existing:
        return None

    update_doc = {}

    for field in ['name', 'description', 'category']:
        if field in product_data and product_data[field] is not None:
            update_doc[field] = product_data[field]

    if 'price' in product_data and product_data['price'] is not None:
        update_doc['price'] = float(product_data['price'])

    if 'stock' in product_data and product_data['stock'] is not None:
        update_doc['stock'] = int(product_data['stock'])

    if not update_doc:
        # Nothing to update, return current document
        return get_product_by_id(product_id)

    update_doc['updated_at'] = datetime.utcnow()

    products_collection.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': update_doc}
    )

    return get_product_by_id(product_id)


def delete_product(product_id):
    """Delete product"""
    product_id = _normalize_id(product_id)
    
    if not ObjectId.is_valid(product_id):
        return False
    
    result = products_collection.delete_one({'_id': ObjectId(product_id)})
    return result.deleted_count > 0


def seed_data():
    """Seed initial data if database is empty"""
    try:
        # Sample products with deterministic ObjectIds derived from integers 1..5
        seeds = [
            {
                'name': 'Laptop Dell XPS 15',
                'description': 'High-performance laptop with 16GB RAM',
                'price': 1299.99,
                'category': 'Electronics',
                'stock': 15
            },
            {
                'name': 'iPhone 15 Pro',
                'description': 'Latest iPhone with A17 chip',
                'price': 999.99,
                'category': 'Electronics',
                'stock': 25
            },
            {
                'name': 'Samsung Galaxy S24',
                'description': 'Flagship Android phone',
                'price': 899.99,
                'category': 'Electronics',
                'stock': 20
            },
            {
                'name': 'Sony WH-1000XM5',
                'description': 'Noise cancelling headphones',
                'price': 399.99,
                'category': 'Audio',
                'stock': 30
            },
            {
                'name': 'iPad Air',
                'description': 'Lightweight tablet with M1 chip',
                'price': 599.99,
                'category': 'Electronics',
                'stock': 18
            }
        ]

        inserted_ids = []
        for index, seed in enumerate(seeds, start=1):
            padded_hex = _normalize_id(index)
            seed_id = ObjectId(padded_hex)
            seed_document = {
                '_id': seed_id,
                **seed,
                'created_by': 'system',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            result = products_collection.replace_one({'_id': seed_id}, seed_document, upsert=True)
            if result.upserted_id or result.matched_count:
                inserted_ids.append(str(seed_id))
        
        print(f"✅ Seeded/updated {len(inserted_ids)} products with fixed IDs: {', '.join(inserted_ids)}")
        
    except Exception as e:
        print(f"⚠️ Seed data warning: {e}")


# Initialize on import
create_indexes()
seed_data()