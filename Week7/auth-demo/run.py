"""
Application Entry Point
Run this file to start the Flask server
"""
from app import create_app
import os

# Create Flask app
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║         Product API with MongoDB Integration              ║
╠═══════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:{port}                  ║
║  Swagger UI:        http://localhost:{port}/docs             ║
║  Health Check:      http://localhost:{port}/health           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
