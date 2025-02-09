from typing import Dict, Optional
import openai
from ..config import Config

class AIModelManager:
    """Manager class for AI model clients and configurations."""
    
    def __init__(self, config: Config):
        """Initialize AI model clients with configuration."""
        self.config = config
        self._clients: Dict[str, openai.OpenAI] = {}
        self._initialize_clients()
        
    def _initialize_clients(self) -> None:
        """Initialize all AI model clients with error handling."""
        # Initialize individual clients with proper error handling
        try:
            if self.config.get('CEREBRAS_API_KEY'):
                self._clients['cerebras'] = openai.OpenAI(
                    base_url=self.config.get('CEREBRAS_BASE_URL'),
                    api_key=self.config.get('CEREBRAS_API_KEY')
                )
            
            if self.config.get('GROQ_API_KEY'):
                self._clients['groq'] = openai.OpenAI(
                    base_url=self.config.get('GROQ_BASE_URL'),
                    api_key=self.config.get('GROQ_API_KEY')
                )
            
            if self.config.get('MISTRAL_API_KEY'):
                self._clients['mistral'] = openai.OpenAI(
                    base_url=self.config.get('MISTRAL_BASE_URL'),
                    api_key=self.config.get('MISTRAL_API_KEY')
                )
            
            if self.config.get('SAMBANOVA_API_KEY'):
                self._clients['sambanova'] = openai.OpenAI(
                    base_url=self.config.get('SAMBANOVA_BASE_URL'),
                    api_key=self.config.get('SAMBANOVA_API_KEY')
                )
            
            if self.config.get('GLHF_API_KEY'):
                self._clients['glhf'] = openai.OpenAI(
                    base_url=self.config.get('GLHF_BASE_URL'),
                    api_key=self.config.get('GLHF_API_KEY')
                )
            
            if self.config.get('GEMINI_API_KEY'):
                self._clients['gemini'] = openai.OpenAI(
                    base_url=self.config.get('GEMINI_BASE_URL'),
                    api_key=self.config.get('GEMINI_API_KEY')
                )
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI clients: {str(e)}")
        
        # Ensure at least one client is initialized
        if not self._clients:
            raise RuntimeError("No AI clients could be initialized. Check API keys.")
    
    @property
    def model_client_mapping(self) -> Dict[str, openai.OpenAI]:
        """Get mapping of model names to their respective clients."""
        return {
            'llama-3.3-70b': self._clients.get('cerebras'),
            'pixtral-large-latest': self._clients.get('mistral'),
            'mistral-large-latest': self._clients.get('mistral'),
            'mistral-small-latest': self._clients.get('mistral'),
            'Meta-Llama-3.1-405B-Instruct': self._clients.get('sambanova'),
            'Meta-Llama-3.1-70B-Instruct': self._clients.get('sambanova'),
            'hf:Qwen/Qwen2.5-72B-Instruct': self._clients.get('glhf'),
            'hf:Qwen/Qwen2.5-Coder-32B-Instruct': self._clients.get('glhf'),
            'hf:meta-llama/Llama-3.3-70B-Instruct': self._clients.get('glhf'),
            'hf:nvidia/Llama-3.1-Nemotron-70B-Instruct-HF': self._clients.get('glhf'),
            'gemini-2.0-flash': self._clients.get('gemini'),
            'gemini-2.0-flash-lite-preview-02-05': self._clients.get('gemini'),
            'gemini-2.0-flash-thinking-exp-01-21': self._clients.get('gemini'),
            'whisper-large-v3': self._clients.get('groq'),
        }
    
    def get_client_for_model(self, model_name: str) -> openai.OpenAI:
        """Get the appropriate client for a given model name."""
        client = self.model_client_mapping.get(model_name)
        # Default to any available client if model not found in mapping
        if not client:
            for fallback_client in ['groq', 'mistral', 'cerebras']:
                if fallback_client in self._clients:
                    return self._clients[fallback_client]
        return client
    
    def get_search_client(self) -> openai.OpenAI:
        """Get the client designated for search operations."""
        return self._clients.get('groq') or self.get_client_for_model('llama-3.3-70b')
    
    def validate_clients(self) -> None:
        """Validate that at least one client is properly initialized."""
        if not self._clients:
            raise ValueError("No AI clients have been initialized successfully")