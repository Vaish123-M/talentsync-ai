"""Main Flask application module with app factory."""
from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


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
    
    # Set upload folder path (relative to backend directory)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app.config['UPLOAD_FOLDER'] = os.path.join(backend_dir, 'uploads')
    app.config['VECTOR_DB_PATH'] = os.path.join(backend_dir, 'vector_store')
    app.config['VECTOR_COLLECTION_NAME'] = os.getenv('VECTOR_COLLECTION_NAME', 'candidates')
    app.config['VECTOR_SEARCH_ENABLED'] = os.getenv('VECTOR_SEARCH_ENABLED', 'true').lower() in {
        '1', 'true', 'yes', 'on'
    }
    app.config['AI_ASSISTANT_ENABLED'] = os.getenv('AI_ASSISTANT_ENABLED', 'true').lower() in {
        '1', 'true', 'yes', 'on'
    }
    app.config['AI_ASSISTANT_USE_OPENAI'] = os.getenv('AI_ASSISTANT_USE_OPENAI', 'false').lower() in {
        '1', 'true', 'yes', 'on'
    }
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['VECTOR_DB_PATH'], exist_ok=True)
    
    # Setup logging
    setup_logging(app)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register routes
    register_routes(app)
    
    return app


def setup_logging(app):
    """Setup application logging."""
    if not app.debug and not app.testing:
        # Production logging setup
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/talentsync.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('TalentSync AI startup')
    else:
        # Development logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.routes import assistant_bp, resume_bp
    from app.routes.ranking_feedback import ranking_bp
    
    app.register_blueprint(resume_bp)
    app.register_blueprint(ranking_bp)
    if app.config.get('AI_ASSISTANT_ENABLED', True):
        app.register_blueprint(assistant_bp)


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
