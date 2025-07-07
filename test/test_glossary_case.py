#!/usr/bin/env python3
"""
Test script to verify glossary case preservation functionality.
"""

import sys
import os
import tempfile
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator3000.processors.csv_processor import CSVProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_glossary_case_preservation():
    """Test that glossary case preservation works correctly."""
    
    # Create a temporary glossary file
    glossary_content = """source;target;keep_case
nonwood;Nonwood;True
ajax;AJAX;False
javascript;JavaScript;True
api;API;False"""

    # Write to the actual glossary.csv file
    with open("glossary.csv", "w", encoding="utf-8") as f:
        f.write(glossary_content)
    
    try:
        # Create CSV processor
        csv_processor = CSVProcessor('en', 'da')  # English to Danish
        
        # Test cases
        test_cases = [
            # Case preservation tests (keep_case=True)
            ("nonwood", "Nonwood"),  # Should preserve target case: "Nonwood"
            ("Nonwood", "Nonwood"),  # Should keep exact match
            ("NONWOOD", "NONWOOD"),  # Should transform target to uppercase: "NONWOOD"
            ("NonWood", "NonWood"),  # Should transform target to title case: "NonWood"
            
            ("javascript", "JavaScript"),  # Should preserve target case
            ("JavaScript", "JavaScript"),  # Should keep exact match
            ("JAVASCRIPT", "JAVASCRIPT"),  # Should transform to uppercase
            
            # Case insensitive tests (keep_case=False)
            ("ajax", "AJAX"),  # Should always use target case
            ("Ajax", "AJAX"),  # Should always use target case
            ("AJAX", "AJAX"),  # Should always use target case
            
            ("api", "API"),  # Should always use target case
            ("Api", "API"),  # Should always use target case
            ("API", "API"),  # Should always use target case
        ]
        
        print("Testing glossary case preservation...")
        print("=" * 50)
        
        all_passed = True
        for input_text, expected_output in test_cases:
            result = csv_processor._apply_glossary_replacements(input_text)
            
            if result == expected_output:
                print(f"✅ PASS: '{input_text}' -> '{result}' (expected: '{expected_output}')")
            else:
                print(f"❌ FAIL: '{input_text}' -> '{result}' (expected: '{expected_output}')")
                all_passed = False
        
        print("=" * 50)
        if all_passed:
            print("🎉 All glossary case preservation tests passed!")
        else:
            print("⚠️ Some tests failed. Please check the implementation.")
        
        # Test in context
        print("\nTesting in sentence context...")
        context_tests = [
            ("This is a nonwood material.", "This is a Nonwood material."),
            ("Using NONWOOD for construction.", "Using NONWOOD for construction."),
            ("We need ajax support.", "We need AJAX support."),
            ("The javascript library is good.", "The JavaScript library is good."),
        ]
        
        for input_text, expected in context_tests:
            result = csv_processor._apply_glossary_replacements(input_text)
            if result == expected:
                print(f"✅ CONTEXT: '{input_text}' -> '{result}'")
            else:
                print(f"❌ CONTEXT: '{input_text}' -> '{result}' (expected: '{expected}')")
                all_passed = False
        
        return all_passed
        
    finally:
        # Restore original glossary file content
        original_content = """# Add your custom translation glossary here
# Format: source;target;keep_case
# Example: ajax;AJAX;False (will replace "Ajax" with "AJAX")
# Example: javascript;JavaScript;True (will replace "javascript" with "JavaScript" but keep original case)
source;target;keep_case
micare;micare;False
ajax;ajax;False
aps;ApS;False
Firhuse;Firhuse;False
Bording;Bording;False
nonwood;nonwood;True"""
        
        with open("glossary.csv", "w", encoding="utf-8") as f:
            f.write(original_content)

if __name__ == "__main__":
    success = test_glossary_case_preservation()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
