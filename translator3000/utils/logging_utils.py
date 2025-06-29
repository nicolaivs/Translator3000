"""
Logging utilities for Translator3000.

This module sets up consistent logging across the application with UTF-8 support
and cross-platform compatibility.
"""

import logging
import sys
import io


def setup_logging():
    """Set up logging with UTF-8 encoding and Unicode-safe console output."""
    
    # Create a UTF-8 compatible stdout wrapper for Windows
    if sys.platform.startswith('win'):
        # On Windows, wrap stdout to handle Unicode characters
        utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    else:
        utf8_stdout = sys.stdout

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('translation.log', encoding='utf-8'),
            logging.StreamHandler(utf8_stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name or __name__)


# Set up logging when module is imported
setup_logging()
