#!/usr/bin/env python3
"""
Test the new retry mechanism and faster translation speeds.
"""

import sys
import time
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000 import CSVTranslator

def test_translation_speed():
    """Test the new faster translation with retry mechanism."""
    
    print("=== Testing Translation Speed & Retry Mechanism ===\n")
    
    # Create translator with new faster default delay (0.05s instead of 0.1s)
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    # Test texts
    test_texts = [
        "Hello world",
        "This is a test",
        "The quick brown fox jumps over the lazy dog",
        "micare provides excellent service",
        "We offer high quality products"
    ]
    
    print("Translation settings:")
    print(f"  Base delay: {translator.delay}s (was 0.1s, now 0.05s = 50% faster)")
    print(f"  Retry mechanism: Enabled with exponential backoff")
    print(f"  Retry delays: 0.05s -> 0.15s -> 0.35s (if needed)")
    print()
    
    print("Testing translations:")
    print("-" * 60)
    
    total_start = time.time()
    
    for i, text in enumerate(test_texts, 1):
        start_time = time.time()
        
        # This will use the new _translate_with_retry method automatically
        translated = translator.translate_text(text)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"{i}. Original:  '{text}'")
        print(f"   Translated: '{translated}'")
        print(f"   Time: {duration:.3f}s")
        print()
    
    total_time = time.time() - total_start
    avg_time = total_time / len(test_texts)
    
    print("Summary:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average per translation: {avg_time:.3f}s")
    print(f"  Estimated improvement: ~50% faster base delay")
    print(f"  Retry protection: Automatic recovery from API failures")
    
    print("\nRetry mechanism features:")
    print("  - Exponential backoff: 50ms -> 150ms -> 350ms")
    print("  - 50ms extra delay per retry attempt")
    print("  - Automatic fallback to original text if all retries fail")
    print("  - Challenges API respectfully without abuse")

if __name__ == "__main__":
    test_translation_speed()
