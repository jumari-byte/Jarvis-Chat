# Jumari Advanced Virtual Intelligence System

## Overview
This is  Flask application that provides chat functionality with multiple AI models, file processing, text-to-speech capabilities, and web search integration.  It features basic memory for follow-up questions, customizable system prompts, and allows you to select from a variety of AI models. Designed for ease of use, it requires minimal setup to get started. Powering a local ChatGPT-like environment. The system is designed to be user-friendly, accurate, and informative, with a focus on providing relevant and contextual responses.

## Directory Structure
```
app/
├── __init__.py          # Application factory
├── config.py            # Configuration settings
├── core/               # Core components
│   ├── clients.py       # API clients and integrations
│   ├── models.py        # Data models and schemas
│   └── session.py       # Session management
├── routes/              # API route handlers
│   ├── chat.py          # Chat-related routes
│   ├── main.py          # Main application routes
│   └── speech.py        # Speech-to-text and text-to-speech routes
├── services/          # Business logic and services
│   ├── file_processor.py # File processing services
│   └── search.py        # Search services
├── utils/             # Utility modules
│   └── logging.py       # Logging utilities
static/               # Static files (CSS, JS, images)
templates/            # HTML templates
tools/               # External tools and scripts
uploads/              # Directory for file uploads
```

## Setup

1. Create a Python virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Dependencies

Install all dependencies using pip:
cd to jarvis-chat
```bash
pip install -r requirements.txt
```

3. Set up environment variables:

   a. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   b. Edit the `.env` file and fill in your API keys:
   ```bash
   # Required: AI Model API Keys
   CEREBRAS_API_KEY=your-cerebras-key
   GROQ_API_KEY=your-groq-key
   MISTRAL_API_KEY=your-mistral-key
   SAMBANOVA_API_KEY=your-sambanova-key
   GLHF_API_KEY=your-glhf-key
   GEMINI_API_KEY=your-gemini-key
   COHERE_API_KEY=your-cohere-key

   # Optional Configuration
   FLASK_ENV=development  # or "production"
   PORT=4001
   ```

   You can obtain API keys from the following providers:
   - Cerebras: https://www.cerebras.ai/
   - Groq: https://www.groq.com/
   - Mistral AI: https://www.mistral.ai/
   - SambaNova: https://www.sambanova.ai/
   - GLHF: https://glhf.chat/
   - Google Gemini: https://ai.google.dev/
   - Cohere: https://cohere.com/

   Note: The application requires at least one valid API key to function. For optimal performance, it is recommended to provide keys for multiple models.

## Running the Application

1. Start the application:
```bash
python run.py
```

2. Access the application at `http://localhost:4001`

## Features

- Multi-model chat interface
- File upload and processing (PDF, images)
- Text-to-speech and speech-to-text
- Web search integration
- Semantic search in uploaded documents
- Session management
- Streaming responses
- Markdown Rendering: Supports rendering of Markdown syntax for formatted text.
- Code Highlighting: Highlights code snippets with syntax highlighting for better readability.
- Code Copying: Allows users to easily copy generated code with a single click.
- You can also get information from a URL. Jarvis will add the content from the URL as context before providing a response.

## Development

- The application uses a factory pattern for initialization
- Configuration is environment-based (development, production, testing)
- Blueprints separate different functional areas
- Services handle business logic
- Core modules manage fundamental functionality

## Error Handling

The application includes comprehensive error handling:
- API client initialization errors
- File processing errors
- Network request failures
- Invalid configuration errors

## Logging

Logging is configured for:
- Chat interactions
- Model usage
- Web searches
- Error tracking

## Security

- CORS is configured for specific origins
- File upload restrictions
- Session security
- Environment variable validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
