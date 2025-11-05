"""
Flask Application Factory
Creates and configures the Flask application
"""
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os

from app.config import config
from app.database.connection import get_database, init_collections, seed_initial_data
from app.utils.auth import JWTManager
from app.routes import auth_bp, products_bp, init_auth_routes, init_product_routes


def create_app(config_name=None):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration name ('development', 'production', or 'default')
    
    Returns:
        Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize database
    db = get_database()
    users_collection = db['users']
    products_collection = db['products']
    refresh_tokens_collection = db['refresh_tokens']
    
    # Create indexes and seed data
    init_collections()
    seed_initial_data()
    
    # Initialize JWT Manager
    jwt_manager = JWTManager(
        secret_key=app.config['SECRET_KEY'],
        refresh_secret_key=app.config['REFRESH_SECRET_KEY'],
        algorithm=app.config['ALGORITHM']
    )
    jwt_manager.set_expiry(
        app.config['ACCESS_TOKEN_EXPIRE_MINUTES'],
        app.config['REFRESH_TOKEN_EXPIRE_DAYS']
    )
    jwt_manager.set_collections(refresh_tokens_collection)
    
    # Initialize routes with dependencies
    init_auth_routes(users_collection, jwt_manager)
    init_product_routes(products_collection, jwt_manager)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    
    # Root endpoint
    @app.route('/')
    def index():
        """API information"""
        return jsonify({
            'message': 'Product API with JWT Authentication',
            'version': '1.0.0',
            'endpoints': {
                'auth': {
                    'register': 'POST /auth/register',
                    'login': 'POST /auth/login',
                    'refresh': 'POST /auth/refresh',
                    'logout': 'POST /auth/logout',
                    'me': 'GET /auth/me',
                    'change_password': 'POST /auth/change-password'
                },
                'products': {
                    'list': 'GET /api/products',
                    'get': 'GET /api/products/{id}',
                    'create': 'POST /api/products',
                    'update': 'PUT /api/products/{id}',
                    'delete': 'DELETE /api/products/{id}'
                },
                'documentation': {
                    'swagger_ui': 'GET /docs',
                    'openapi_spec': 'GET /openapi.yaml'
                }
            }
        })
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint"""
        try:
            # Test database connection
            db.command('ping')
            return jsonify({
                'status': 'healthy',
                'database': 'connected'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }), 500
    
    # Swagger UI endpoint
    @app.route('/docs')
    def swagger_ui():
        """Swagger UI documentation"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>API Documentation</title>
            <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
            <script>
                window.onload = function() {
                    SwaggerUIBundle({
                        url: '/openapi.yaml',
                        dom_id: '#swagger-ui',
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIBundle.SwaggerUIStandalonePreset
                        ]
                    });
                };
            </script>
        </body>
        </html>
        '''
    
    # OpenAPI spec endpoint
    @app.route('/openapi.yaml')
    def openapi_spec():
        """Serve OpenAPI specification"""
        return send_file('../openapi.yaml', mimetype='text/yaml')
    
    return app
