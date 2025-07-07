#!/usr/bin/env python3
"""
Test script to verify that empty elements and self-closing tags don't get malformed CDATA.
"""

import sys
import os
import logging
import xml.etree.ElementTree as ET

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_empty_elements():
    """Test that empty elements and self-closing tags are handled correctly."""
    
    # Create processors
    csv_processor = CSVProcessor('en', 'da')  # English to Danish
    xml_processor = XMLProcessor(csv_processor)
    
    input_file = "test_empty_elements.xml"
    output_file = "test_empty_elements_translated.xml"
    
    print("Testing empty elements and self-closing tags...")
    
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
        
        # Validate XML is well-formed
        try:
            ET.parse(output_file)
            print("\n✅ XML is well-formed!")
        except ET.ParseError as e:
            print(f"\n❌ XML is malformed: {e}")
            return False
        
        # Check for specific issues
        checks = [
            ('No malformed CDATA after self-closing tags', '<Title /><![CDATA[' not in result),
            ('No malformed CDATA after empty elements', '<EmptyTitle></EmptyTitle><![CDATA[' not in result),
            ('CDATA preserved in valid elements', '<![CDATA[<p>' in result),
            ('Self-closing tags preserved', '<SelfClosingTitle />' in result or '<SelfClosingTitle/>' in result),
        ]
        
        print("\n🔍 Verification results:")
        all_passed = True
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"  {status}: {check_name}")
            if not check_result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All tests passed! Empty elements handled correctly.")
        else:
            print("\n⚠️  Some tests failed. Please check the implementation.")
            
        return all_passed
            
    else:
        print("❌ Translation failed!")
        return False

if __name__ == "__main__":
    success = test_empty_elements()
    if not success:
        sys.exit(1)
