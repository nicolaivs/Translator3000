#!/usr/bin/env python3
"""
Test script for LibreTranslate localhost detection and prioritization.
"""

import sys
sys.path.append('.')

import sys
import os
# Add parent directory to path so we can import translator3000
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from translator3000 import (
    load_config, 
    is_libretranslate_localhost_available,
    get_optimized_translation_services,
    CSVTranslator
)

def test_localhost_detection():
    """Test localhost LibreTranslate detection."""
    print("Testing LibreTranslate localhost detection...")
    print("=" * 50)
    
    # Load config
    config = load_config()
    print(f"Config loaded:")
    print(f"  - localhost_enabled: {config.get('libretranslate_localhost_enabled')}")
    print(f"  - localhost_port: {config.get('libretranslate_localhost_port')}")
    print(f"  - localhost_url: {config.get('libretranslate_localhost_url')}")
    print()
    
    # Test localhost detection
    localhost_available = is_libretranslate_localhost_available()
    print(f"Localhost LibreTranslate available: {localhost_available}")
    
    # Test service ordering
    print("\nTesting service ordering...")
    optimized_services = get_optimized_translation_services()
    print(f"Optimized service order: {optimized_services}")
    
    # Test translator initialization
    print("\nTesting translator initialization...")
    try:
        translator = CSVTranslator(source_lang='en', target_lang='nl')
        print(f"✓ Translator initialized successfully with {len(translator.translators)} services")
        
        # Test a simple translation
        print("\nTesting translation...")
        test_text = "Hello, how are you today?"
        translated = translator.translate_text(test_text)
        print(f"Original: {test_text}")
        print(f"Translated: {translated}")
        
    except Exception as e:
        print(f"✗ Error initializing translator: {e}")

if __name__ == "__main__":
    test_localhost_detection()
