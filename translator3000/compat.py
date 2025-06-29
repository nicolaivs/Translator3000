"""
Compatibility utilities for Translator3000.

This module provides backward compatibility functions and constants
that are used by test scripts and other legacy code.
"""

from typing import List
from .config import load_config


def get_optimized_translation_services() -> List[str]:
    """
    Get optimized translation services based on availability.
    
    Returns:
        List of available translation service names
    """
    config = load_config()
    base_services = config.get('translation_services', 'deep_translator,googletrans,libretranslate').split(',')
    
    # Clean service names
    services = [s.strip() for s in base_services if s.strip()]
    
    # Check LibreTranslate availability
    try:
        from .services.libre_translate import LibreTranslateService
        # Try to detect if self-hosted LibreTranslate is available
        test_service = LibreTranslateService('en', 'da')
        if hasattr(test_service, '_test_connection'):
            # If we can test connection, do so
            pass
    except Exception:
        # If LibreTranslate is not available, remove it from services
        services = [s for s in services if s != 'libretranslate']
    
    return services


def get_translation_services() -> List[str]:
    """
    Get available translation services.
    
    Returns:
        List of translation service names
    """
    return get_optimized_translation_services()


# For backward compatibility
TRANSLATION_SERVICES = get_translation_services()
AVAILABLE_TRANSLATORS = TRANSLATION_SERVICES
