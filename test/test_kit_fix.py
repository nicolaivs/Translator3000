#!/usr/bin/env python3
"""
Test case to ensure KIT glossary behavior is correct
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from translator3000.utils.text_utils import load_glossary, apply_glossary_replacements
from translator3000.processors.csv_processor import CSVProcessor
from pathlib import Path

def test_kit_glossary_behavior():
    """Test that KIT with keep_case=True works correctly."""
    print("=== Testing KIT Glossary Behavior ===")
    
    # Load glossary
    glossary_path = Path("glossary.csv")
    glossary = load_glossary(glossary_path)
    
    # Test cases that should all result in "KIT"
    test_cases = [
        ("KIT", "KIT"),
        ("Kit", "KIT"), 
        ("kit", "KIT"),
        ("KIT 4", "KIT 4"),
        ("Kit 4", "KIT 4"),
        ("kit 4", "KIT 4"),
        ("This is a KIT for you", "This is a KIT for you"),
        ("This is a Kit for you", "This is a KIT for you"),
        ("This is a kit for you", "This is a KIT for you"),
    ]
    
    print("Testing text_utils.apply_glossary_replacements:")
    all_passed = True
    for input_text, expected in test_cases:
        result = apply_glossary_replacements(input_text, glossary)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected: '{expected}')")
        if not passed:
            all_passed = False
    
    # Also test CSV processor
    print("\nTesting CSVProcessor._apply_glossary_replacements:")
    processor = CSVProcessor(source_lang='en', target_lang='nl')
    
    for input_text, expected in test_cases:
        result = processor._apply_glossary_replacements(input_text)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected: '{expected}')")
        if not passed:
            all_passed = False
    
    print(f"\nOverall result: {'All tests passed!' if all_passed else 'Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    test_kit_glossary_behavior()
