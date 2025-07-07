#!/usr/bin/env python3
"""
Test script to verify CDATA preservation for all HTML-containing elements.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from translator3000.processors.xml_processor import XMLProcessor
from translator3000.processors.csv_processor import CSVProcessor

def test_cdata_preservation():
    """Test that CDATA sections are preserved for all HTML elements."""
    
    print("🧪 Testing CDATA preservation...")
    
    # Initialize processors
    csv_processor = CSVProcessor('en', 'da')  # English to Danish for testing
    xml_processor = XMLProcessor(csv_processor)
    
    input_file = "test_cdata_preservation.xml"
    output_file = "test_cdata_preservation_translated.xml"
    
    print(f"📖 Input file: {input_file}")
    print(f"💾 Output file: {output_file}")
    
    # Read original content for comparison
    with open(input_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    print("\n📄 Original XML content:")
    print("=" * 50)
    print(original_content)
    print("=" * 50)
    
    # Translate the XML
    success, chars_translated = xml_processor.translate_xml(input_file, output_file)
    
    if success:
        print(f"✅ Translation completed successfully!")
        print(f"📏 Characters translated: {chars_translated}")
        
        # Read and display the result
        with open(output_file, 'r', encoding='utf-8') as f:
            result = f.read()
        
        print("\n📄 Translated XML content:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
        # Check CDATA preservation
        print("\n🔍 Analyzing CDATA preservation:")
        
        elements_to_check = [
            ('Teaser', '<p>'),
            ('Content', '<h1>'),
            ('Description', '<p>')
        ]
        
        preserved_count = 0
        for element_name, html_tag in elements_to_check:
            if f'<{element_name}><![CDATA[' in result and html_tag in result:
                print(f"✅ {element_name}: CDATA preserved with raw HTML")
                preserved_count += 1
            elif f'<{element_name}>' in result and '&lt;' in result:
                print(f"❌ {element_name}: CDATA missing - HTML was escaped")
            else:
                print(f"⚠️  {element_name}: Unable to determine CDATA status")
        
        print(f"\n📊 Summary: {preserved_count}/{len(elements_to_check)} elements have CDATA properly preserved")
        
        if preserved_count == len(elements_to_check):
            print("🎉 SUCCESS: All CDATA sections properly preserved!")
        else:
            print("⚠️  Some CDATA sections were not preserved correctly")
            
    else:
        print("❌ Translation failed!")

if __name__ == "__main__":
    test_cdata_preservation()
