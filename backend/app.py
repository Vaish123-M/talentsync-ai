"""Entry point for running Flask application in development mode."""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import create_app


if __name__ == '__main__':
    # Create Flask app instance in development mode
    app = create_app(config_name='development')
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
