#!/usr/bin/env python3
"""
Test the exact scenario from the original issue: "7131526;7131525;30000;" becoming "7131526;7131525.0;30000;"
"""
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from translator3000.translator import CSVTranslator

def test_original_issue():
    """Test the exact scenario that was causing .0 to be added."""
    print("=== Testing Original Issue Scenario ===")
    
    # Create a CSV with the exact data pattern from your issue
    test_csv_content = """ItemID;ProductID;Stock
7131526;7131525;30000
1234567;8765432;50000"""
    
    print("Original CSV:")
    print(test_csv_content)
    
    # Write test file
    with open("test_original_issue.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    # Test WITHOUT translating any columns (to see if numbers still get .0 added)
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    print("\n=== Test 1: No columns translated (just read/write) ===")
    success, chars = translator.translate_csv(
        input_file="test_original_issue.csv",
        output_file="test_original_issue_output.csv", 
        columns_to_translate=[],  # No columns to translate
        delimiter=";"
    )
    
    if success:
        with open("test_original_issue_output.csv", "r", encoding="utf-8") as f:
            result = f.read()
        print("Result after read/write cycle:")
        print(result)
        
        # Check specifically for the pattern from your issue
        if "7131525.0" in result:
            print("❌ ISSUE REPRODUCED: Found .0 in numbers!")
        else:
            print("✅ ISSUE FIXED: No .0 found in numbers!")
    
    # Clean up
    try:
        os.remove("test_original_issue.csv")
        os.remove("test_original_issue_output.csv") 
    except:
        pass

if __name__ == "__main__":
    test_original_issue()
