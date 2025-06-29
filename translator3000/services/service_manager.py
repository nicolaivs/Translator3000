"""
Service manager for handling translation service initialization and optimization.

This module manages the creation and optimization of translation services,
including self-hosted service detection and automatic prioritization.
"""

import logging
from typing import List, Tuple, Any

from .libre_translate import LibreTranslateService, is_libretranslate_selfhost_available
from .google_translate import DeepTranslatorService, GoogleTransService
from ..config import get_config

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


def create_translation_services(source_lang: str, target_lang: str) -> List[Tuple[str, Any]]:
    """Create and initialize all available translation services."""
    config = get_config()
    services = []
    service_names = get_optimized_translation_services()
    
    for service_name in service_names:
        try:
            if service_name == 'libretranslate':
                service = LibreTranslateService(
                    source_lang=source_lang,
                    target_lang=target_lang,
                    api_key=config.get('libretranslate_api_key', '')
                )
                services.append(('libretranslate', service))
                logger.info(f"✓ LibreTranslate service initialized")
            
            elif service_name == 'deep_translator':
                service = DeepTranslatorService(source_lang=source_lang, target_lang=target_lang)
                services.append(('deep_translator', service))
                logger.info(f"✓ deep-translator service initialized")
            
            elif service_name == 'googletrans':
                service = GoogleTransService(source_lang=source_lang, target_lang=target_lang)
                services.append(('googletrans', service))
                logger.info(f"✓ googletrans service initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize {service_name}: {e}")
    
    if not services:
        raise ImportError("No translation services could be initialized")
    
    logger.info(f"Active translation services: {[name for name, _ in services]}")
    return services
