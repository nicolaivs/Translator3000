#!/usr/bin/env python3
"""
Test script to compare translation speeds and services.
"""

import time
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000 import CSVTranslator, TRANSLATION_SERVICES, AVAILABLE_TRANSLATORS

def test_translation_services():
    """Test different translation services and their performance."""
    
    print("=== Translation Services Comparison ===")
    print(f"Available services: {TRANSLATION_SERVICES}")
    print(f"Service status: {AVAILABLE_TRANSLATORS}")
    
    # Test phrases
    test_phrases = [
        "Hello world",
        "This is a test",
        "The quick brown fox"
    ]
    
    # Test each available service individually by modifying config temporarily
    import translator3000
    original_config = translator3000.CONFIG['translation_services']
    
    for service in ['libretranslate', 'deep_translator', 'googletrans']:
        if not AVAILABLE_TRANSLATORS.get(service, False):
            print(f"\n--- {service} (unavailable) ---")
            continue
            
        print(f"\n--- Testing {service} ---")
        
        try:
            # Temporarily set config to use only this service
            translator3000.CONFIG['translation_services'] = service
            translator3000.TRANSLATION_SERVICES = [service]
            
            translator = CSVTranslator(
                source_lang='en', 
                target_lang='da'
            )
            
            start_time = time.time()
            
            for i, phrase in enumerate(test_phrases, 1):
                translated = translator.translate_text(phrase)
                print(f"  {i}. '{phrase}' -> '{translated}'")
            
            total_time = time.time() - start_time
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Rate: {len(test_phrases)/total_time:.1f} translations/sec")
            
        except Exception as e:
            print(f"  ✗ {service} failed: {e}")
        
        finally:
            # Restore original config
            translator3000.CONFIG['translation_services'] = original_config
            translator3000.TRANSLATION_SERVICES = translator3000.get_translation_services()

def test_service_fallback():
    """Test automatic fallback between services."""
    
    print("\n=== Service Fallback Test ===")
    
    try:
        translator = CSVTranslator(source_lang='en', target_lang='da')
        
        print(f"Translator has {len(translator.translators)} services configured:")
        for i, (service_name, _) in enumerate(translator.translators, 1):
            print(f"  {i}. {service_name}")
        
        # Test a simple phrase
        test_text = "Automatic fallback test"
        print(f"\nTesting: '{test_text}'")
        translated = translator.translate_text(test_text)
        print(f"Result: '{translated}'")
        
        print("✓ Fallback test completed successfully!")
        
    except Exception as e:
        print(f"✗ Fallback test failed: {e}")

if __name__ == "__main__":
    test_translation_services()
    test_service_fallback()
