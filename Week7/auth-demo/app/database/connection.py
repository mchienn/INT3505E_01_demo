"""
Database connection and configuration for MongoDB
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    """MongoDB Database connection singleton"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        """Connect to MongoDB"""
        if self._client is None:
            try:
                mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
                self._client = MongoClient(mongodb_uri)
                
                # Test connection
                self._client.admin.command('ping')
                
                db_name = os.getenv('MONGODB_DATABASE', 'product_api')
                self._db = self._client[db_name]
                
                print(f"✅ Connected to MongoDB: {db_name}")
                return self._db
            except ConnectionFailure as e:
                print(f"❌ Failed to connect to MongoDB: {e}")
                raise
        return self._db
    
    def get_db(self):
        """Get database instance"""
        if self._db is None:
            return self.connect()
        return self._db
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            print("🔌 MongoDB connection closed")


# Create global database instance
db_instance = Database()


def get_database():
    """Get database connection"""
    return db_instance.get_db()


def init_collections():
    """Initialize collections with indexes"""
    db = get_database()
    
    # Users collection
    users_collection = db['users']
    users_collection.create_index('username', unique=True)
    users_collection.create_index('email', unique=True)
    
    # Products collection
    products_collection = db['products']
    products_collection.create_index('category')
    products_collection.create_index('created_by')
    products_collection.create_index('price')
    
    # Refresh tokens collection
    refresh_tokens_collection = db['refresh_tokens']
    refresh_tokens_collection.create_index('jti', unique=True)
    refresh_tokens_collection.create_index('user_id')
    refresh_tokens_collection.create_index('expires_at')
    
    print("✅ Collections initialized with indexes")


def seed_initial_data():
    """Seed initial users if database is empty"""
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    db = get_database()
    users_collection = db['users']
    
    # Check if users exist
    if users_collection.count_documents({}) == 0:
        initial_users = [
            {
                'username': 'admin',
                'password': generate_password_hash('admin123'),
                'email': 'admin@example.com',
                'full_name': 'Administrator',
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.utcnow()
            },
            {
                'username': 'user1',
                'password': generate_password_hash('user123'),
                'email': 'user1@example.com',
                'full_name': 'John Doe',
                'role': 'user',
                'is_active': True,
                'created_at': datetime.utcnow()
            }
        ]
        
        users_collection.insert_many(initial_users)
        print("✅ Initial users seeded")
    
    # Seed sample products
    products_collection = db['products']
    if products_collection.count_documents({}) == 0:
        # Get admin user ID
        admin = users_collection.find_one({'username': 'admin'})
        
        sample_products = [
            {
                'name': 'Laptop Dell XPS 15',
                'description': 'High-performance laptop with Intel i7, 16GB RAM, 512GB SSD',
                'price': 1299.99,
                'category': 'Electronics',
                'stock': 25,
                'created_by': str(admin['_id']),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'name': 'iPhone 15 Pro',
                'description': 'Apple iPhone 15 Pro with 256GB storage',
                'price': 999.99,
                'category': 'Electronics',
                'stock': 50,
                'created_by': str(admin['_id']),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'name': 'Office Chair Ergonomic',
                'description': 'Comfortable ergonomic office chair with lumbar support',
                'price': 249.99,
                'category': 'Furniture',
                'stock': 15,
                'created_by': str(admin['_id']),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        products_collection.insert_many(sample_products)
        print("✅ Sample products seeded")
