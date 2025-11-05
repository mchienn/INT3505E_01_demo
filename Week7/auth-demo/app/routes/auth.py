"""
Authentication Routes
Handles user registration, login, token refresh, logout
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import UserCreate, UserResponse, LoginRequest
from app.utils.auth import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Global variables (will be set by app factory)
users_collection = None
jwt_manager = None


def init_auth_routes(users_col, jwt_mgr):
    """Initialize routes with dependencies"""
    global users_collection, jwt_manager
    users_collection = users_col
    jwt_manager = jwt_mgr


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request body:
    {
        "username": "string",
        "password": "string",
        "email": "string",
        "full_name": "string"
    }
    """
    try:
        # Validate request data with Pydantic
        user_data = UserCreate(**request.json)
        
        # Check if username already exists
        if users_collection.find_one({'username': user_data.username}):
            return jsonify({'error': 'Username already exists'}), 400
        
        # Check if email already exists
        if users_collection.find_one({'email': user_data.email}):
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        new_user = {
            'username': user_data.username,
            'password': generate_password_hash(user_data.password),
            'email': user_data.email,
            'full_name': user_data.full_name,
            'role': 'user',
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(new_user)
        new_user['_id'] = result.inserted_id
        
        # Return user response (without password)
        user_response = UserResponse(
            id=str(new_user['_id']),
            username=new_user['username'],
            email=new_user['email'],
            full_name=new_user['full_name'],
            role=new_user['role']
        )
        
        return jsonify(user_response.dict()), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and return tokens
    
    Request body:
    {
        "username": "string",
        "password": "string"
    }
    """
    try:
        # Validate request data
        login_data = LoginRequest(**request.json)
        
        # Find user
        user = users_collection.find_one({'username': login_data.username})
        
        if not user or not check_password_hash(user['password'], login_data.password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.get('is_active', True):
            return jsonify({'error': 'Account is disabled'}), 403
        
        # Generate tokens
        access_token = jwt_manager.create_access_token(user)
        refresh_token = jwt_manager.create_refresh_token(user)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token
    
    Request body:
    {
        "refresh_token": "string"
    }
    """
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Verify refresh token
        payload = jwt_manager.verify_refresh_token(refresh_token)
        if not payload:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        # Get user from database
        user = users_collection.find_one({'_id': ObjectId(payload['user_id'])})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Revoke old refresh token and create new ones (token rotation)
        jwt_manager.revoke_refresh_token(payload['jti'])
        
        # Generate new tokens
        new_access_token = jwt_manager.create_access_token(user)
        new_refresh_token = jwt_manager.create_refresh_token(user)
        
        return jsonify({
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'token_type': 'Bearer'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@token_required(lambda: jwt_manager)
def logout(current_user):
    """
    Logout user and revoke refresh token
    
    Request body:
    {
        "refresh_token": "string"
    }
    """
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if refresh_token:
            payload = jwt_manager.verify_refresh_token(refresh_token)
            if payload:
                jwt_manager.revoke_refresh_token(payload['jti'])
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@token_required(lambda: jwt_manager)
def get_current_user(current_user):
    """
    Get current user information
    """
    try:
        user = users_collection.find_one({'_id': ObjectId(current_user['user_id'])})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_response = UserResponse(
            id=str(user['_id']),
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            role=user['role']
        )
        
        return jsonify(user_response.dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@token_required(lambda: jwt_manager)
def change_password(current_user):
    """
    Change user password
    
    Request body:
    {
        "old_password": "string",
        "new_password": "string"
    }
    """
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords are required'}), 400
        
        # Get user
        user = users_collection.find_one({'_id': ObjectId(current_user['user_id'])})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify old password
        if not check_password_hash(user['password'], old_password):
            return jsonify({'error': 'Invalid old password'}), 401
        
        # Validate new password (reuse Pydantic validator)
        try:
            UserCreate(
                username=user['username'],
                password=new_password,
                email=user['email'],
                full_name=user['full_name']
            )
        except ValidationError as e:
            return jsonify({'error': 'Invalid new password', 'details': e.errors()}), 400
        
        # Update password
        users_collection.update_one(
            {'_id': ObjectId(current_user['user_id'])},
            {'$set': {'password': generate_password_hash(new_password)}}
        )
        
        # Revoke all refresh tokens for security
        jwt_manager.revoke_all_user_tokens(current_user['user_id'])
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
