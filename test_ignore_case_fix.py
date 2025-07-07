#!/usr/bin/env python3
"""
Test script to verify that Ignore="True" (capital I) and CDATA preservation work correctly.
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_ignore_case_and_cdata():
    """Test that Ignore='True' (capital I) is respected and CDATA is preserved."""
    
    # Create processors
    csv_processor = CSVProcessor('en', 'da')  # English to Danish
    xml_processor = XMLProcessor(csv_processor)
    
    input_file = "test_ignore_case_fix.xml"
    output_file = "test_ignore_case_fix_translated.xml"
    
    print("Testing XML with Ignore='True' (capital I) and CDATA preservation...")
    
    # Translate the XML
    success, chars_translated = xml_processor.translate_xml(input_file, output_file)
    
    if success:
        print(f"✅ Translation completed successfully!")
        print(f"Characters translated: {chars_translated}")
        
        # Read and display the result
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        print("\n📄 Translated XML content:")
        print(result)
        
        # Check specific requirements
        checks = [
            ('Ignore="True" respected', 'https://micare.dk/media/2141960.jpg?w=240&format=jpg' in result),
            ('No HTML escaping in CDATA', '&amp;' not in result or '<![CDATA[' in result),
            ('CDATA preserved for URLs', '<![CDATA[https://micare.dk/media/2141960.jpg?w=240&format=jpg]]>' in result),
            ('ignore="true" respected', 'https://example.com/path?param=value&other=data' in result),
        ]
        
        print("\n🔍 Verification results:")
        all_passed = True
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"  {status}: {check_name}")
            if not check_result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All tests passed! Ignore attribute and CDATA preservation work correctly.")
        else:
            print("\n⚠️  Some tests failed. Please check the implementation.")
            
    else:
        print("❌ Translation failed!")
        return False
    
    return success

if __name__ == "__main__":
    test_ignore_case_and_cdata()
