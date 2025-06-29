"""
Translation services package.

This package contains all the translation service implementations with a clean,
modular architecture for easy maintenance and extension.
"""

from .base import BaseTranslationService
from .libre_translate import LibreTranslateService, is_libretranslate_selfhost_available
from .google_translate import DeepTranslatorService, GoogleTransService

__all__ = [
    'BaseTranslationService',
    'LibreTranslateService', 
    'DeepTranslatorService',
    'GoogleTransService', 
    'is_libretranslate_selfhost_available'
]
