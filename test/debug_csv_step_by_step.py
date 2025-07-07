#!/usr/bin/env python3
"""
Debug why the CSV translation doesn't show KIT preservation
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from translator3000.processors.csv_processor import CSVProcessor

def debug_csv_translation():
    """Debug CSV translation step by step."""
    print("=== Debugging CSV Translation ===")
    
    processor = CSVProcessor(source_lang='en', target_lang='da')
    
    test_text = "This is a KIT for testing"
    print(f"Original: '{test_text}'")
    
    # Step 1: Apply glossary before translation
    after_glossary_1 = processor._apply_glossary_replacements(test_text)
    print(f"After glossary 1: '{after_glossary_1}'")
    
    # Step 2: Plain text translation
    translated = processor._translate_plain_text(after_glossary_1)
    print(f"After translation: '{translated}'")
    
    # Step 3: Apply glossary after translation
    after_glossary_2 = processor._apply_glossary_replacements(translated)
    print(f"After glossary 2: '{after_glossary_2}'")
    
    # Compare with the actual translate_text method
    print("\n=== Using translate_text method ===")
    final_result = processor.translate_text(test_text)
    print(f"Final result: '{final_result}'")

if __name__ == "__main__":
    debug_csv_translation()
