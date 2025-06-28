#!/usr/bin/env python3
"""
Test script to compare translation speeds with different delay settings.
"""

import time
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from translator3000 import CSVTranslator

def test_delay_performance():
    """Test translation performance with different delay settings."""
    
    print("=== Translation Delay Performance Comparison ===")
    
    # Test phrases
    test_phrases = [
        "Hello world",
        "This is a test",
        "The quick brown fox",
        "micare provides excellent service",
        "We offer high quality products"
    ]
    
    # Test different delays (in seconds)
    delay_settings = [
        (0.001, "1ms"),    # Very fast
        (0.005, "5ms"),    # Current optimized setting  
        (0.010, "10ms"),   # User's suggested setting
        (0.050, "50ms"),   # Original conservative setting
    ]
    
    for delay_seconds, delay_name in delay_settings:
        print(f"\n--- Testing with {delay_name} delay ---")
        
        # Create translator with specific delay
        translator = CSVTranslator(
            source_lang='en', 
            target_lang='da', 
            delay_between_requests=delay_seconds
        )
        
        start_time = time.time()
        
        for i, phrase in enumerate(test_phrases, 1):
            translated = translator.translate_text(phrase)
            print(f"  {i}. '{phrase}' -> '{translated}'")
        
        total_time = time.time() - start_time
        avg_time = total_time / len(test_phrases)
        
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Average per translation: {avg_time:.3f}s")
        print(f"  Rate: {len(test_phrases)/total_time:.1f} translations/sec")

if __name__ == "__main__":
    test_delay_performance()
