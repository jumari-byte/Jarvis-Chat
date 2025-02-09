import os
from typing import Dict, Any, Set

class Config:
    """Base configuration class for the application."""
    
    def __init__(self):
        """Initialize configuration with environment variables."""
        # Flask configuration
        self.SECRET_KEY = os.urandom(24)
        self.SESSION_COOKIE_SECURE = True
        self.SESSION_COOKIE_SAMESITE = 'None'
        
        # File upload configuration
        self.UPLOAD_FOLDER = 'uploads'
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
        self.ALLOWED_EXTENSIONS: Set[str] = {'pdf', 'jpg', 'png', 'jpeg'}
        
        # AI Model API Base URLs
        self.CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
        self.GROQ_BASE_URL = "https://api.groq.com/openai/v1"
        self.MISTRAL_BASE_URL = "https://api.mistral.ai/v1"
        self.SAMBANOVA_BASE_URL = "https://api.sambanova.ai/v1"
        self.GLHF_BASE_URL = "https://glhf.chat/api/openai/v1"
        self.GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
        
        # AI Model API keys from environment
        self.CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        self.SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY")
        self.GLHF_API_KEY = os.getenv("GLHF_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.COHERE_API_KEY = os.getenv("COHERE_API_KEY")
        
        # CORS configuration
        self.CORS_ORIGINS = ["*"]
        self.CORS_METHODS = ["GET", "POST", "OPTIONS"]
        self.CORS_HEADERS = ["Content-Type"]
        self.CORS_SUPPORTS_CREDENTIALS = True
        
        # Voice configuration for TTS
        self.VOICE_MAPPING = {
            'en-US': 'en-US-ChristopherNeural',
            'id-ID': 'id-ID-ArdiNeural',
            'en-GB': 'en-GB-RyanNeural',
            'ja-JP': 'ja-JP-NanamiNeural',
            'zh-CN': 'zh-CN-YunxiNeural',
            'ko-KR': 'ko-KR-InJoonNeural'
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return getattr(self, key, default)
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if a filename has an allowed extension."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    def validate(self) -> None:
        """Validate the configuration settings."""
        required_env_vars = [
            "GROQ_API_KEY",
            "MISTRAL_API_KEY",
            "GEMINI_API_KEY",
            "COHERE_API_KEY"
        ]
        
        missing_vars = [var for var in required_env_vars 
                       if not self.get(var)]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

class DevelopmentConfig(Config):
    """Development configuration."""
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.TESTING = False
        self.SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
        self.LOGGING_ENABLED = False
        self.CHAT_LOGGING_ENABLED = False

class TestingConfig(Config):
    """Testing configuration."""
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.TESTING = True
        self.UPLOAD_FOLDER = 'test_uploads'

# Configuration dictionary
config_by_name: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config(config_name: str = 'development') -> Config:
    """Get configuration class by name."""
    config_class = config_by_name.get(config_name, DevelopmentConfig)
    return config_class()