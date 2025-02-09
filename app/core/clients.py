import cohere
from typing import Optional

class CohereClient:
    """Manager for Cohere client instance."""
    
    _instance: Optional[cohere.Client] = None
    
    @classmethod
    def initialize(cls, config) -> cohere.Client:
        """
        Initialize or get existing Cohere client.
        
        Args:
            config: Application configuration
            
        Returns:
            Initialized Cohere client
        """
        if cls._instance is None:
            cohere_api_key = config.get('COHERE_API_KEY')
            if not cohere_api_key:
                raise ValueError("COHERE_API_KEY not found in configuration")
            cls._instance = cohere.Client(cohere_api_key)
        return cls._instance
    
    @classmethod
    def get_client(cls) -> Optional[cohere.Client]:
        """Get the current Cohere client instance."""
        return cls._instance
