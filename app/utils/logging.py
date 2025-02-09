import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(name: str,
                log_file: str,
                level: int = logging.INFO,
                max_bytes: int = 10485760,  # 10MB
                backup_count: int = 5) -> logging.Logger:
    """
    Set up a logger with rotation capability.
    
    Args:
        name: Name of the logger
        log_file: Path to the log file
        level: Logging level
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handlers
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    
    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(handler)
    
    return logger

# Create chat logger
chat_logger = setup_logger('chatlogger', 'chat.log')

def log_chat(user_input: str,
             model: str,
             web_search_used: bool,
             error: Optional[str] = None) -> None:
    """
    Log chat interactions.
    
    Args:
        user_input: The user's input message
        model: The AI model used
        web_search_used: Whether web search was used
        error: Optional error message if something went wrong
    """
    from flask import current_app
    
    try:
        # Check if we're in production and logging is disabled
        if current_app.config.get('ENV') == 'production' and \
           not current_app.config.get('CHAT_LOGGING_ENABLED', True):
            return
            
        if error:
            chat_logger.error(
                f"Error in chat - Model: {model}, Input: {user_input}, "
                f"Web Search: {web_search_used}, Error: {error}"
            )
        else:
            chat_logger.info(
                f"Model: {model}, Web Search: {web_search_used}, "
                f"User Input: {user_input}"
            )
    except RuntimeError:
        # If we're outside application context, don't log
        return
