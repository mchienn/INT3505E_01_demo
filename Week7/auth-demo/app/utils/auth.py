"""
JWT Authentication Utilities
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import secrets


class JWTManager:
    """JWT token management"""
    
    def __init__(self, secret_key, refresh_secret_key, algorithm='HS256'):
        self.secret_key = secret_key
        self.refresh_secret_key = refresh_secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 7
        self.refresh_tokens_collection = None
    
    def set_collections(self, refresh_tokens_collection):
        """Set MongoDB collections"""
        self.refresh_tokens_collection = refresh_tokens_collection
    
    def set_expiry(self, access_minutes, refresh_days):
        """Set token expiry times"""
        self.access_token_expire_minutes = access_minutes
        self.refresh_token_expire_days = refresh_days
    
    def create_access_token(self, user_data: dict) -> str:
        """Create JWT access token"""
        payload = {
            'user_id': str(user_data['_id']),
            'username': user_data['username'],
            'role': user_data['role'],
            'email': user_data['email'],
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_data: dict) -> str:
        """Create JWT refresh token and store in database"""
        jti = secrets.token_hex(16)
        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            'user_id': str(user_data['_id']),
            'username': user_data['username'],
            'type': 'refresh',
            'jti': jti,
            'exp': expires_at,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.refresh_secret_key, algorithm=self.algorithm)
        
        # Store in database
        if self.refresh_tokens_collection is not None:
            self.refresh_tokens_collection.insert_one({
                'jti': jti,
                'user_id': str(user_data['_id']),
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'last_used': datetime.utcnow()
            })
        
        return token
    
    def verify_access_token(self, token: str):
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get('type') != 'access':
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_refresh_token(self, token: str):
        """Verify JWT refresh token and check database"""
        try:
            payload = jwt.decode(token, self.refresh_secret_key, algorithms=[self.algorithm])
            if payload.get('type') != 'refresh':
                return None
            
            # Check if token exists in database and hasn't been revoked
            if self.refresh_tokens_collection is not None:
                jti = payload.get('jti')
                token_data = self.refresh_tokens_collection.find_one({'jti': jti})
                
                if not token_data:
                    return None
                
                # Update last_used timestamp
                self.refresh_tokens_collection.update_one(
                    {'jti': jti},
                    {'$set': {'last_used': datetime.utcnow()}}
                )
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_refresh_token(self, jti: str):
        """Revoke a refresh token"""
        if self.refresh_tokens_collection is not None:
            self.refresh_tokens_collection.delete_one({'jti': jti})
    
    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all refresh tokens for a user"""
        if self.refresh_tokens_collection is not None:
            self.refresh_tokens_collection.delete_many({'user_id': user_id})


def token_required(jwt_manager):
    """Decorator to require valid JWT token"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    token = auth_header.split(' ')[1]
                except IndexError:
                    return jsonify({'error': 'Invalid token format'}), 401
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            current_user = jwt_manager.verify_access_token(token)
            if not current_user:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            
            return f(current_user, *args, **kwargs)
        
        return decorated_function
    return decorator
