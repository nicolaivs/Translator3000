"""
Translation service manager.

This module handles service selection, optimization, and fallback logic.
"""

import logging
from typing import List
from ..config import get_config
from .libre_translate import is_libretranslate_selfhost_available

logger = logging.getLogger(__name__)


def get_optimized_translation_services() -> List[str]:
    """Get translation services in optimal order, prioritizing selfhost if available."""
    config = get_config()
    base_services = config.get('translation_services', 'deep_translator,googletrans,libretranslate').split(',')
    base_services = [s.strip() for s in base_services]
    
    # Check if selfhost LibreTranslate is available
    if is_libretranslate_selfhost_available():
        # If selfhost is available, prioritize it by putting it first
        # and ensure we only have one libretranslate entry
        optimized_services = ['libretranslate']  # selfhost version goes first
        for service in base_services:
            if service != 'libretranslate':  # avoid duplicates
                optimized_services.append(service)
        
        logger.info("🚀 Self-hosted LibreTranslate prioritized for optimal performance")
        return optimized_services
    else:
        # No selfhost, use configured order
        logger.info("Using configured service order (no self-hosted LibreTranslate detected)")
        return base_services
