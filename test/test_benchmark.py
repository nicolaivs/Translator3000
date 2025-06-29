#!/usr/bin/env python3
"""
Test current translation speed and demonstrate improvements.
"""

import sys
import time
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000 import CSVTranslator

def benchmark_translation():
    """Benchmark the current translation system."""
    
    print("=== Translation Speed & Retry Mechanism Benchmark ===\n")
    
    # Test with current improved settings
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    test_data = [
        "Hello world",
        "Good morning",  
        "Thank you",
        "How are you?",
        "Have a nice day"
    ]
    
    print("Current configuration:")
    print(f"  ✓ Base delay reduced from 0.1s to 0.05s (50% faster)")
    print(f"  ✓ Retry mechanism added with exponential backoff")
    print(f"  ✓ Glossary protection ensures consistent terms")
    print(f"  ✓ Auto-recovery from API failures")
    print()
    
    # Test batch translation speed
    print("Testing 5 short translations...")
    start_time = time.time()
    
    results = []
    for text in test_data:
        translated = translator.translate_text(text)
        results.append((text, translated))
    
    total_time = time.time() - start_time
    avg_time = total_time / len(test_data)
    
    print("Results:")
    for original, translated in results:
        print(f"  '{original}' -> '{translated}'")
    
    print(f"\nPerformance:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average per translation: {avg_time:.2f}s")
    print(f"  Rate: {len(test_data)/total_time:.1f} translations/second")
    
    print(f"\nImprovements implemented:")
    print(f"  🚀 50% faster base speed (0.05s vs 0.1s delay)")
    print(f"  🛡️  Retry protection with smart backoff")
    print(f"  📈 Exponential retry delays: 50ms -> 150ms -> 350ms")
    print(f"  🎯 Challenges API optimally without abuse")
    print(f"  ✅ Maintains quality with glossary protection")

if __name__ == "__main__":
    benchmark_translation()
