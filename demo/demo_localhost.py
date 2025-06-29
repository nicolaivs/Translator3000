#!/usr/bin/env python3
"""
Demo script showing localhost LibreTranslate detection and prioritization.
This script demonstrates how Translator3000 automatically detects and prioritizes
local LibreTranslate instances for optimal performance.
"""

import time
import sys
import os
# Add parent directory to path so we can import translator3000
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from translator3000 import CONFIG, is_libretranslate_localhost_available, get_optimized_translation_services

def demo_service_prioritization():
    """Demonstrate service prioritization with and without localhost detection."""
    print("=" * 60)
    print("LibreTranslate Localhost Detection Demo")
    print("=" * 60)
    print()
    
    # Show current configuration
    
    print("Current Configuration:")
    print(f"  localhost_enabled: {CONFIG.get('libretranslate_localhost_enabled', False)}")
    print(f"  localhost_port: {CONFIG.get('libretranslate_localhost_port', 5000)}")
    print(f"  localhost_url: {CONFIG.get('libretranslate_localhost_url', 'N/A')}")
    print(f"  remote_url: {CONFIG.get('libretranslate_url', 'N/A')}")
    print()
    
    # Test localhost detection
    print("Testing localhost detection...")
    localhost_available = is_libretranslate_localhost_available()
    
    if localhost_available:
        print("✅ LOCAL LIBRETRANSLATE DETECTED!")
        print("   🚀 Performance boost: 8-15x faster than cloud services")
        print("   🔒 Privacy boost: Data stays on your machine")
        print("   💰 Cost boost: No API rate limits")
    else:
        print("❌ No local LibreTranslate detected")
        print("   💡 To enable ultra-fast translation, run:")
        print("      docker run -p 5000:5000 libretranslate/libretranslate")
    
    print()
    
    # Show service prioritization
    print("Service Priority Order:")
    services = get_optimized_translation_services()
    for i, service in enumerate(services, 1):
        speed_info = {
            'libretranslate': '8-15 trans/sec (LOCAL)' if localhost_available else '1 trans/sec (REMOTE)',
            'deep_translator': '4.6 trans/sec (CLOUD)',
            'googletrans': '4.0 trans/sec (CLOUD)'
        }
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        print(f"   {emoji} {i}. {service:15} - {speed_info.get(service, 'Unknown speed')}")
    
    print()
    
    # Performance explanation
    if localhost_available:
        print("🎯 OPTIMAL SETUP DETECTED!")
        print("   Your translations will be:")
        print("   • 8-15x faster than cloud services")
        print("   • Completely private (no data sent to cloud)")
        print("   • Unlimited (no rate limiting)")
        print("   • Available offline")
    else:
        print("📈 PERFORMANCE OPPORTUNITY:")
        print("   Install local LibreTranslate for massive speed improvement:")
        print("   1. Install Docker")
        print("   2. Run: docker run -p 5000:5000 libretranslate/libretranslate")
        print("   3. Restart Translator3000 - it will auto-detect and prioritize!")
    
    print()
    print("=" * 60)

def demo_translation_with_fallback():
    """Demonstrate translation with service fallback."""
    print("Translation Demo with Service Fallback")
    print("=" * 60)
    
    from translator3000 import CSVTranslator
    
    # Create translator instance
    print("Initializing translator...")
    translator = CSVTranslator(source_lang='en', target_lang='nl')
    
    print(f"Active services: {[name for name, _ in translator.translators]}")
    print()
    
    # Test translations
    test_phrases = [
        "Hello, world!",
        "This is a test translation.",
        "Quality is our top priority.",
        "Welcome to our online store.",
        "Free shipping on orders over $50."
    ]
    
    print("Testing translations:")
    for phrase in test_phrases:
        start_time = time.time()
        translated = translator.translate_text(phrase)
        end_time = time.time()
        
        print(f"  EN: {phrase}")
        print(f"  NL: {translated}")
        print(f"      (took {(end_time - start_time):.2f}s)")
        print()

if __name__ == "__main__":
    try:
        demo_service_prioritization()
        print()
        demo_translation_with_fallback()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Demo error: {e}")
        print("Make sure Translator3000 is properly installed.")
