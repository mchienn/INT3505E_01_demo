"""
API Routes
"""
from .auth import auth_bp, init_auth_routes
from .products import products_bp, init_product_routes

__all__ = [
    'auth_bp',
    'products_bp',
    'init_auth_routes',
    'init_product_routes'
]
