"""Main Flask application module with app factory."""
from flask import Flask, jsonify
from flask_cors import CORS
import os


def create_app(config_name='development'):
    """Application factory for creating Flask app instances.
    
    Args:
        config_name: Configuration environment (development/production/testing)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'development':
        app.config['DEBUG'] = True
        app.config['ENV'] = 'development'
    elif config_name == 'production':
        app.config['DEBUG'] = False
        app.config['ENV'] = 'production'
    else:
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
    
    # Common configuration
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_EXTENSIONS'] = ['.pdf']
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register routes
    register_routes(app)
    
    return app


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.routes import resume_bp
    
    app.register_blueprint(resume_bp)


def register_routes(app):
    """Register application routes."""
    
    @app.route('/', methods=['GET'])
    def health_check():
        """Root route that returns application status."""
        return jsonify({
            'status': 'success',
            'message': 'TalentSync AI Hiring Assistant API is running',
            'version': '1.0.0',
            'environment': app.config.get('ENV', 'unknown')
        }), 200
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """API health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'api_version': 'v1'
        }), 200
