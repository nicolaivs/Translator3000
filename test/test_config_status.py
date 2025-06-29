#!/usr/bin/env python3
"""
Simple script to verify configuration loading.
"""

import sys
import os
# Add parent directory to path so we can import translator3000
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from translator3000 import CONFIG, load_config

print("=== Translator3000 Configuration Status ===")
print(f"Current delay setting: {CONFIG['delay']}ms")
print(f"CSV max workers: {CONFIG['csv_max_workers']}")
print(f"XML max workers: {CONFIG['xml_max_workers']}")
print(f"Multithreading threshold: {CONFIG['multithreading_threshold']}")
print(f"Max retries: {CONFIG['max_retries']}")
print(f"Progress interval: {CONFIG['progress_interval']}")

print("\n=== Performance Notes ===")
print("- 5ms delay provides optimal performance (4.6 translations/sec)")
print("- Benchmarked as 25% faster than old 50ms default")
print("- Multithreading enabled for 3+ items for maximum speed")
print("- See CONFIG.md for detailed performance analysis")
