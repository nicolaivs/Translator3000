#!/usr/bin/env python3
"""
Test script to verify that spaces around translated text are preserved in CSV processing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from translator3000.processors.csv_processor import CSVProcessor
import pandas as pd
import tempfile

def test_csv_space_preservation():
    """Test that spaces around translated text are preserved in CSV processing."""
    
    print("🧪 Testing space preservation in CSV HTML translation...")
    
    # Initialize processor
    csv_processor = CSVProcessor('en', 'da')  # English to Danish for testing
    
    # Test HTML content with critical spaces
    test_cases = [
        "Use micare<strong data-end='1719' data-start='1699'>Surface maintenance</strong>For best results.",
        "Also try <em>product testing</em> before use.",
        "Text with <span>multiple words</span> and more text.",
        "Simple text without HTML tags.",
        "Mixed content with <b>bold text</b> and normal text."
    ]
    
    print("📄 Testing HTML content translation:")
    print("=" * 80)
    
    for i, original in enumerate(test_cases):
        print(f"\nTest case {i+1}:")
        print(f"Original: {original}")
        
        # Translate the HTML content
        translated = csv_processor.translate_html_content(original)
        print(f"Translated: {translated}")
        
        # Check for space preservation patterns
        if i == 0:  # micare<strong>...</strong>For case
            if 'micare<strong' in translated and '</strong>For' in translated:
                print("✅ Spaces around <strong> tag preserved")
            else:
                print("❌ Spaces around <strong> tag lost!")
                
        elif i == 1:  # <em>...</em> case
            if ' <em>' in translated and '</em> ' in translated:
                print("✅ Spaces around <em> tag preserved")
            else:
                print("❌ Spaces around <em> tag lost!")
                
        elif i == 2:  # <span>...</span> case
            if ' <span>' in translated and '</span> ' in translated:
                print("✅ Spaces around <span> tag preserved")
            else:
                print("❌ Spaces around <span> tag lost!")
    
    print("\n" + "=" * 80)
    
    # Test with CSV file
    print("\n🧪 Testing CSV file translation with HTML content...")
    
    # Create test CSV data
    test_data = {
        'id': [1, 2, 3],
        'title': ['Product Title 1', 'Product Title 2', 'Product Title 3'],
        'description': [
            "Use micare<strong>Surface maintenance</strong>For best results.",
            "Also try <em>product testing</em> before use.",
            "Text with <span>multiple words</span> and more text."
        ]
    }
    
    df = pd.DataFrame(test_data)
    
    # Create temporary CSV files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as input_file:
        df.to_csv(input_file.name, index=False, encoding='utf-8')
        input_path = input_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Translate the CSV
        success, char_count = csv_processor.translate_csv(
            input_path, 
            output_path, 
            columns_to_translate=['description']
        )
        
        if success:
            # Read the result
            result_df = pd.read_csv(output_path, encoding='utf-8')
            
            print("📄 Original CSV descriptions:")
            for i, desc in enumerate(df['description']):
                print(f"  Row {i+1}: {desc}")
            
            print("\n📄 Translated CSV descriptions:")
            for i, desc in enumerate(result_df['description_translated']):
                print(f"  Row {i+1}: {desc}")
            
            # Check space preservation in CSV results
            print("\n🔍 Analyzing space preservation in CSV results:")
            
            success_count = 0
            total_checks = 0
            
            for i, translated_desc in enumerate(result_df['description_translated']):
                if i == 0:  # micare<strong>...</strong>For case
                    total_checks += 1
                    if 'micare<strong' in translated_desc and '</strong>For' in translated_desc:
                        print(f"✅ Row {i+1}: Spaces around <strong> tag preserved")
                        success_count += 1
                    else:
                        print(f"❌ Row {i+1}: Spaces around <strong> tag lost!")
                        
                elif i == 1:  # <em>...</em> case
                    total_checks += 1
                    if ' <em>' in translated_desc and '</em> ' in translated_desc:
                        print(f"✅ Row {i+1}: Spaces around <em> tag preserved")
                        success_count += 1
                    else:
                        print(f"❌ Row {i+1}: Spaces around <em> tag lost!")
                        
                elif i == 2:  # <span>...</span> case
                    total_checks += 1
                    if ' <span>' in translated_desc and '</span> ' in translated_desc:
                        print(f"✅ Row {i+1}: Spaces around <span> tag preserved")
                        success_count += 1
                    else:
                        print(f"❌ Row {i+1}: Spaces around <span> tag lost!")
            
            print(f"\n📊 Summary: {success_count}/{total_checks} space preservation checks passed")
            
            if success_count == total_checks:
                print("🎉 SUCCESS: All spaces properly preserved in CSV processing!")
                return True
            else:
                print("❌ Some space preservation issues found in CSV processing")
                return False
        else:
            print("❌ CSV translation failed!")
            return False
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except:
            pass

if __name__ == "__main__":
    success = test_csv_space_preservation()
    if success:
        print("\n✅ CSV space preservation test passed!")
    else:
        print("\n❌ CSV space preservation test failed!")
