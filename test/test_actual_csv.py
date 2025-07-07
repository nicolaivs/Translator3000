#!/usr/bin/env python3
"""
Test the actual CSV translation with the KIT fix
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from translator3000.translator import CSVTranslator

def test_csv_translation():
    """Test CSV translation with KIT fix."""
    print("=== Testing CSV Translation with KIT fix ===")
    
    # Create a test CSV with KIT cases
    test_csv_content = """name,description
Product 1,This is a KIT for testing
Product 2,Contains kit components
Product 3,The Kit includes everything"""
    
    with open("test_kit.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    # Initialize translator
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    # Translate the CSV
    success, chars = translator.translate_csv(
        input_file="test_kit.csv",
        output_file="test_kit_translated.csv", 
        columns_to_translate=["description"]
    )
    
    if success:
        print(f"✓ Translation completed successfully! {chars} characters translated.")
        
        # Read and show the result
        with open("test_kit_translated.csv", "r", encoding="utf-8") as f:
            result = f.read()
        print("\nTranslated CSV content:")
        print(result)
    else:
        print("✗ Translation failed!")
    
    # Clean up
    import os
    try:
        os.remove("test_kit.csv")
        os.remove("test_kit_translated.csv") 
    except:
        pass

if __name__ == "__main__":
    test_csv_translation()
