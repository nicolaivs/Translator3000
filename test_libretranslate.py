#!/usr/bin/env python3
"""
Test script to verify LibreTranslate integration and fallback functionality.
"""

import time
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from translator3000 import CSVTranslator, TRANSLATION_SERVICES

def test_libretranslate_integration():
    """Test LibreTranslate integration with fallback support."""
    
    print("=== LibreTranslate Integration Test ===")
    print(f"Available translation services: {TRANSLATION_SERVICES}")
    
    # Test phrases
    test_phrases = [
        "Hello world",
        "This is a test",
        "micare provides excellent service"
    ]
    
    try:
        # Create translator (will use services in order of preference)
        translator = CSVTranslator(
            source_lang='en', 
            target_lang='da'
        )
        
        print(f"\nTranslator initialized with {len(translator.translators)} services:")
        for i, (service_name, _) in enumerate(translator.translators, 1):
            print(f"  {i}. {service_name}")
        
        print(f"\nTesting translations:")
        start_time = time.time()
        
        for i, phrase in enumerate(test_phrases, 1):
            translated = translator.translate_text(phrase)
            print(f"  {i}. '{phrase}' -> '{translated}'")
        
        total_time = time.time() - start_time
        print(f"\nTotal time: {total_time:.3f}s")
        print(f"Rate: {len(test_phrases)/total_time:.1f} translations/sec")
        
        print("\n✓ LibreTranslate integration test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_service_fallback():
    """Test fallback between translation services."""
    
    print("\n=== Service Fallback Test ===")
    
    # Test with a phrase that might fail on some services
    test_text = "Special characters: åæø"
    
    try:
        translator = CSVTranslator(source_lang='da', target_lang='en')
        
        print(f"Testing service fallback with: '{test_text}'")
        translated = translator.translate_text(test_text)
        print(f"Result: '{translated}'")
        
        print("✓ Service fallback test completed!")
        
    except Exception as e:
        print(f"✗ Fallback test failed: {e}")

if __name__ == "__main__":
    test_libretranslate_integration()
    test_service_fallback()
