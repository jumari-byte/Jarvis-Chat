import os
import sys
import logging
from app import create_app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "CEREBRAS_API_KEY",
        "GROQ_API_KEY",
        "GROQ_API_KEY2",
        "MISTRAL_API_KEY",
        "SAMBANOVA_API_KEY",
        "GLHF_API_KEY",
        "GITHUB_API_KEY",
        "GEMINI_API_KEY",
        "COHERE_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in start.bat or your environment")
        return False
    return True

if __name__ == '__main__':
    try:
        # Check environment variables
        if not check_environment():
            sys.exit(1)
            
        # Get environment setting
        env = os.getenv('FLASK_ENV', 'development')
        logger.info(f"Starting application in {env} mode")
        
        # Create app instance with appropriate config
        app = create_app(env)
        
        # Set host and port
        host = '0.0.0.0'
        port = int(os.getenv('PORT', 4001))
        
        # Log startup information
        logger.info(f"Starting server on {host}:{port}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=(env == 'development')
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)