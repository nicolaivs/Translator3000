#!/usr/bin/env python3
"""
Benchmark script to compare localhost vs remote LibreTranslate performance.
"""

import time
import sys
sys.path.append('.')

def benchmark_localhost_vs_remote():
    """Benchmark localhost LibreTranslate vs other services."""
    from translator3000 import CSVTranslator
    
    print("=" * 60)
    print("LibreTranslate Performance Benchmark")
    print("=" * 60)
    
    # Test phrases
    test_phrases = [
        "Hello world",
        "This is a test",
        "Quality first",
        "Fast translation",
        "Excellent service"
    ]
    
    print(f"Testing {len(test_phrases)} translations...")
    print()
    
    # Create translator with current prioritization
    translator = CSVTranslator(source_lang='en', target_lang='nl')
    print(f"Active services: {[name for name, _ in translator.translators]}")
    print()
    
    # Benchmark current setup
    print("🚀 Benchmarking current setup (localhost prioritized):")
    start_time = time.time()
    
    for i, phrase in enumerate(test_phrases, 1):
        trans_start = time.time()
        result = translator.translate_text(phrase)
        trans_end = time.time()
        print(f"  {i}. {phrase} → {result} ({trans_end - trans_start:.2f}s)")
    
    total_time = time.time() - start_time
    avg_time = total_time / len(test_phrases)
    translations_per_sec = len(test_phrases) / total_time
    
    print()
    print(f"📊 Performance Results:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average per translation: {avg_time:.2f}s")
    print(f"   Translations per second: {translations_per_sec:.1f}")
    print()
    
    # Compare with expected performance
    expected_performance = {
        'localhost_libretranslate': '8-15 trans/sec',
        'deep_translator': '4.6 trans/sec',
        'remote_libretranslate': '1.0 trans/sec'
    }
    
    primary_service = translator.translators[0][0] if translator.translators else 'unknown'
    
    if translations_per_sec >= 8:
        print("🎯 EXCELLENT! Performance matches localhost LibreTranslate expectations")
        print("   Your setup is optimized for maximum speed!")
    elif translations_per_sec >= 4:
        print("✅ GOOD! Performance matches cloud service expectations")
        print("   Consider localhost LibreTranslate for even better performance")
    else:
        print("⚠️  SLOWER PERFORMANCE")
        print("   This may be normal for remote LibreTranslate or network issues")
    
    print()
    print("💡 Performance Tips:")
    print("   • First translation is slower (model loading)")
    print("   • Subsequent translations are much faster")
    print("   • localhost LibreTranslate is fastest after warm-up")
    print("   • Network latency affects cloud services")

if __name__ == "__main__":
    try:
        benchmark_localhost_vs_remote()
    except Exception as e:
        print(f"Benchmark error: {e}")
        import traceback
        traceback.print_exc()
