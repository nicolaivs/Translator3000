#!/usr/bin/env python3
"""
Test the CSV processor with the .0 fix
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from translator3000.translator import CSVTranslator

def test_csv_processor_fix():
    """Test the CSV processor with the .0 fix."""
    print("=== Testing CSV Processor Fix ===")
    
    # Create test CSV like user's issue
    test_csv_content = """id;name;price
7131526;Product A;30000
7131525;Product B;
9999999;Product C;50000"""
    
    with open("test_processor_fix.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    print("Original CSV:")
    print(test_csv_content)
    
    # Use the CSV processor to translate only the 'name' column
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    success, chars = translator.translate_csv(
        input_file="test_processor_fix.csv",
        output_file="test_processor_output.csv",
        columns_to_translate=["name"],  # Only translate name, not id or price
        delimiter=";"
    )
    
    if success:
        print(f"\n✓ Translation completed! {chars} characters translated.")
        
        # Read the output
        with open("test_processor_output.csv", "r", encoding="utf-8") as f:
            output = f.read()
        print("\nOutput CSV:")
        print(output)
        
        # Check if numbers still have .0
        if ".0" in output:
            print("\n❌ PROBLEM: Numbers still have .0 added!")
        else:
            print("\n✅ SUCCESS: Numbers preserved correctly!")
    else:
        print("\n❌ Translation failed!")
    
    # Clean up
    for file in ["test_processor_fix.csv", "test_processor_output.csv"]:
        try:
            os.remove(file)
        except:
            pass

if __name__ == "__main__":
    test_csv_processor_fix()
