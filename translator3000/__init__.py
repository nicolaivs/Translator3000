"""
Translator3000 - Multi-Language CSV & XML Translation Package
============================================================

A modular translation package supporting CSV and XML files with multiple 
translation services and automatic fallback.

Main Classes:
    CSVTranslator: Main translation class for CSV and XML files

Usage:
    from translator3000 import CSVTranslator
    
    translator = CSVTranslator('en', 'da')  # English to Danish
    translator.translate_csv('input.csv', 'output.csv')
    translator.translate_xml('input.xml', 'output.xml')
"""

# Import from the new modular implementation
from .translator import CSVTranslator
from .config import load_config, CONFIG

# Import compatibility constants and functions
from .compat import (
    get_optimized_translation_services, get_translation_services,
    TRANSLATION_SERVICES, AVAILABLE_TRANSLATORS
)

# Package info
__version__ = "3.0.0"
__author__ = "Translator3000 Team"

__all__ = [
    'CSVTranslator', 'CONFIG', 'load_config',
    'get_optimized_translation_services', 'get_translation_services',
    'TRANSLATION_SERVICES', 'AVAILABLE_TRANSLATORS'
]
