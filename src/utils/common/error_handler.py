"""
Error handling and logging utilities.
"""
import logging
import streamlit as st
from typing import Callable, Any
import traceback
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for the app."""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        "destination_empty": "⚠️ Please enter a destination",
        "destination_too_long": "⚠️ Destination name is too long",
        "invalid_inputs": "⚠️ Please check all your inputs and try again",
        "api_error": "❌ Service temporarily unavailable. Please try again later.",
        "malformed_response": "⚠️ Received invalid response from AI service",
        "rate_limit": "⚠️ Too many requests. Please wait a moment and try again.",
        "no_api_key": "❌ API key not configured. Check your .env file.",
        "generic": "❌ An unexpected error occurred. Please try again.",
    }
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """Log error with full traceback."""
        logger.error(f"Error in {context}: {str(error)}")
        logger.debug(traceback.format_exc())
    
    @staticmethod
    def show_error(error: Exception, user_message: str = None):
        """Display user-friendly error message."""
        ErrorHandler.log_error(error, "user_action")
        
        if user_message:
            st.error(user_message)
        else:
            st.error(ErrorHandler.ERROR_MESSAGES["generic"])
    
    @staticmethod
    def handle_validation_error(error: Exception):
        """Handle validation errors."""
        ErrorHandler.log_error(error, "validation")
        st.error(f"⚠️ {str(error)}")
    
    @staticmethod
    def handle_api_error(error: Exception):
        """Handle API/LLM errors."""
        ErrorHandler.log_error(error, "api")
        
        error_msg = str(error).lower()
        
        if "api_key" in error_msg or "authentication" in error_msg:
            st.error(ErrorHandler.ERROR_MESSAGES["no_api_key"])
        elif "rate" in error_msg or "quota" in error_msg:
            st.error(ErrorHandler.ERROR_MESSAGES["rate_limit"])
        elif "connection" in error_msg or "timeout" in error_msg:
            st.error(ErrorHandler.ERROR_MESSAGES["api_error"])
        else:
            st.error(ErrorHandler.ERROR_MESSAGES["malformed_response"])


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Execute a function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ErrorHandler.log_error(e, func.__name__)
        raise
