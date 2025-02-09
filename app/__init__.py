from flask import Flask, g
from flask_cors import CORS
import os
import logging
from typing import Optional

from .config import Config, get_config
from .core.models import AIModelManager
from .core.session import SessionManager
from .core.clients import CohereClient
from .utils.logging import setup_logger

def create_app(config_name: str = 'development') -> Flask:
    """
    Application factory function.
    
    Args:
        config_name: Name of the configuration to use
    
    Returns:
        Configured Flask application instance
    """
    # Get the root directory (where run.py is located)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create Flask app with custom template and static folders
    app = Flask(__name__,
                template_folder=os.path.join(root_dir, 'templates'),
                static_folder=os.path.join(root_dir, 'static'))
    
    try:
        # Load configuration
        config = get_config(config_name)
        app.config.from_object(config)
        
        # Set up logging based on environment
        if config_name == 'production' and not app.config.get('LOGGING_ENABLED', True):
            # Disable all logging in production when disabled
            logging.disable(logging.CRITICAL)
            app.logger.disabled = True
        else:
            app.logger.setLevel(logging.INFO)
        
        # Store config instance
        app.config_instance = config
        
        # Initialize CORS
        CORS(app,
             supports_credentials=True,
             resources={r"/*": {
                 "origins": config.CORS_ORIGINS,
                 "methods": config.CORS_METHODS,
                 "allow_headers": config.CORS_HEADERS,
                 "expose_headers": config.CORS_HEADERS,
                 "supports_credentials": config.CORS_SUPPORTS_CREDENTIALS
             }})
        
        # Ensure upload directory exists
        upload_folder = os.path.join(root_dir, app.config['UPLOAD_FOLDER'])
        app.config['UPLOAD_FOLDER'] = upload_folder
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Initialize components with proper error handling
        with app.app_context():
            initialize_components(app)
        
        # Register blueprints
        register_blueprints(app)
        
        @app.before_request
        def before_request():
            """Set up request context with Cohere client."""
            g.cohere_client = CohereClient.get_client()
        
        app.logger.info(f"Application started successfully in {config_name} mode")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    return app

def initialize_components(app: Flask) -> None:
    """
    Initialize application components and extensions.
    
    Args:
        app: Flask application instance
    """
    try:
        # Initialize Cohere client first
        app.cohere_client = CohereClient.initialize(app.config)
        app.logger.info("Cohere client initialized successfully")
        
        # Initialize session manager
        app.session_manager = SessionManager()
        app.logger.info("Session manager initialized successfully")
        
        # Initialize AI model manager
        app.model_manager = AIModelManager(app.config_instance)
        app.logger.info("AI model manager initialized successfully")
        
        # Validate configuration
        if hasattr(app.config_instance, 'validate'):
            app.config_instance.validate()
            app.logger.info("Configuration validated successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize components: {str(e)}")
        raise

def register_blueprints(app: Flask) -> None:
    """
    Register Flask blueprints.
    
    Args:
        app: Flask application instance
    """
    try:
        # Import blueprints here to avoid circular imports
        from .routes.main import main_bp
        app.register_blueprint(main_bp)
        app.logger.info("Registered main blueprint")
        
        from .routes.chat import chat_bp
        app.register_blueprint(chat_bp)
        app.logger.info("Registered chat blueprint")
        
        from .routes.speech import speech_bp
        app.register_blueprint(speech_bp)
        app.logger.info("Registered speech blueprint")
        
    except Exception as e:
        app.logger.error(f"Error registering blueprints: {str(e)}")
        raise

def init():
    """Initialize the application with default configuration."""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    return app

# Create global application instance
_app: Optional[Flask] = None

def get_app() -> Flask:
    """
    Get or create the Flask application instance.
    
    Returns:
        Flask application instance
    """
    global _app
    if _app is None:
        _app = init()
    return _app
