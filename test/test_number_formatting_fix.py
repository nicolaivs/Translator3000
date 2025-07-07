#!/usr/bin/env python3
"""
Test the CSV processor with actual data to verify the .0 number fix
"""
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from translator3000.translator import CSVTranslator

def test_actual_csv_with_numbers():
    """Test CSV translation with actual data to verify number formatting."""
    print("=== Testing CSV Translation with Number Fix ===")
    
    # Create a test CSV that mimics your semicolon-delimited data with potential empty cells
    test_csv_content = """ItemID;ProductID;Stock;Description
7131526;7131525;30000;Product with KIT component
1234567;;50000;Another product
9876543;8765432;;Empty stock product
5555555;4444444;12345;Normal product"""
    
    print("Test CSV content:")
    print(test_csv_content)
    
    # Write test file
    with open("test_number_formatting.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    # Initialize translator with semicolon delimiter
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    # Translate only the Description column
    success, chars = translator.translate_csv(
        input_file="test_number_formatting.csv",
        output_file="test_number_formatting_translated.csv", 
        columns_to_translate=["Description"],
        delimiter=";"
    )
    
    if success:
        print(f"✓ Translation completed successfully! {chars} characters translated.")
        
        # Read and show the result
        with open("test_number_formatting_translated.csv", "r", encoding="utf-8") as f:
            result = f.read()
        print("\nTranslated CSV content:")
        print(result)
        
        # Check for .0 in numeric columns
        lines = result.strip().split('\n')
        for i, line in enumerate(lines[1:], 1):  # Skip header
            if '.0;' in line:
                print(f"⚠️  Warning: Found .0 in line {i}: {line}")
            else:
                print(f"✓ Line {i} looks good: {line}")
    else:
        print("✗ Translation failed!")
    
    # Clean up
    try:
        os.remove("test_number_formatting.csv")
        os.remove("test_number_formatting_translated.csv") 
    except:
        pass

if __name__ == "__main__":
    test_actual_csv_with_numbers()
