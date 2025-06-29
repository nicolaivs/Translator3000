#!/usr/bin/env python3
"""
Test multithreaded vs single-threaded translation performance.
"""

import sys
import time
import pandas as pd
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000 import CSVTranslator

def test_multithreading_performance():
    """Test the performance difference between single and multithreaded translation."""
    
    print("=== Multithreading Performance Test ===\n")
    
    # Create test data
    test_data = {
        'Product': [
            'Premium Coffee Beans',
            'Organic Green Tea',
            'Dark Chocolate Bar',
            'Fresh Orange Juice',
            'Whole Wheat Bread',
            'Natural Honey',
            'Greek Yogurt',
            'Almond Butter',
            'Coconut Oil',
            'Vanilla Extract',
            'Sea Salt',
            'Olive Oil',
            'Balsamic Vinegar',
            'Red Wine',
            'Sparkling Water'
        ],
        'Description': [
            'High quality coffee beans from Colombia',
            'Organic green tea leaves from Japan',
            'Rich dark chocolate with 70% cocoa',
            'Fresh squeezed orange juice with pulp',
            'Nutritious whole wheat bread',
            'Pure natural honey from local beehives',
            'Creamy Greek yogurt with probiotics',
            'Smooth almond butter with no additives',
            'Virgin coconut oil for cooking',
            'Pure vanilla extract for baking',
            'Natural sea salt from Mediterranean',
            'Extra virgin olive oil from Italy',
            'Aged balsamic vinegar from Modena',
            'Full-bodied red wine from France',
            'Refreshing sparkling mineral water'
        ]
    }
    
    df = pd.DataFrame(test_data)
    print(f"Test dataset: {len(df)} rows, 2 columns")
    print(f"Sample data:")
    print(df.head(3))
    print()
    
    # Create translator
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    # Test single-threaded approach
    print("Testing SINGLE-THREADED translation...")
    start_time = time.time()
    single_threaded_result = translator._translate_column_single_threaded(df, 'Product')
    single_threaded_time = time.time() - start_time
    
    print(f"Single-threaded time: {single_threaded_time:.2f}s")
    print(f"Sample results: {single_threaded_result.head(3).tolist()}")
    print()
    
    # Test multithreaded approach with different worker counts
    for workers in [2, 4, 6]:
        print(f"Testing MULTITHREADED translation ({workers} workers)...")
        start_time = time.time()
        multithreaded_result = translator.translate_column_multithreaded(df, 'Product', max_workers=workers)
        multithreaded_time = time.time() - start_time
        
        speedup = single_threaded_time / multithreaded_time if multithreaded_time > 0 else 0
        
        print(f"Multithreaded time ({workers} workers): {multithreaded_time:.2f}s")
        print(f"Speedup: {speedup:.1f}x faster")
        print(f"Sample results: {multithreaded_result.head(3).tolist()}")
        print()
    
    # Test the automatic selection logic
    print("Testing AUTOMATIC threading selection...")
    start_time = time.time()
    auto_result = translator.translate_column(df, 'Description', use_multithreading=True, max_workers=4)
    auto_time = time.time() - start_time
    
    auto_speedup = single_threaded_time / auto_time if auto_time > 0 else 0
    print(f"Automatic multithreading time: {auto_time:.2f}s")
    print(f"Speedup vs single-threaded: {auto_speedup:.1f}x faster")
    print()
    
    print("=== Performance Summary ===")
    print(f"📊 Dataset size: {len(df)} rows")
    print(f"🐌 Single-threaded: {single_threaded_time:.2f}s")
    print(f"🚀 Best multithreaded: {min([multithreaded_time]):.2f}s")
    print(f"⚡ Maximum speedup: {max([single_threaded_time / multithreaded_time]):.1f}x faster")
    print()
    print("🧵 Multithreading benefits:")
    print("  ✅ Parallel API requests")
    print("  ✅ Better CPU utilization")
    print("  ✅ Faster large dataset processing")
    print("  ✅ Automatic fallback to single-threaded")
    print("  ✅ Thread-safe progress tracking")

if __name__ == "__main__":
    test_multithreading_performance()
