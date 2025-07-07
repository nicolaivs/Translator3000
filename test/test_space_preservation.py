#!/usr/bin/env python3
"""
Test script to verify that spaces around translated text are preserved.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from translator3000.processors.xml_processor import XMLProcessor
from translator3000.processors.csv_processor import CSVProcessor
import tempfile

def test_space_preservation():
    """Test that spaces around translated text are preserved."""
    
    print("🧪 Testing space preservation in HTML translation...")
    
    # Initialize processors
    csv_processor = CSVProcessor('en', 'da')  # English to Danish for testing
    xml_processor = XMLProcessor(csv_processor)
    
    # XML with HTML content that has critical spaces
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <Content><![CDATA[
        Use micare<strong data-end="1719" data-start="1699">Surface maintenance</strong>For best results.
        Also try <em>product testing</em> before use.
        Text with <span>multiple words</span> and more text.
    ]]></Content>
</root>'''
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as input_file:
        input_file.write(xml_content)
        input_path = input_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        print("📄 Original XML content:")
        print("=" * 60)
        print(xml_content)
        print("=" * 60)
        
        # Process the XML
        success, char_count = xml_processor.translate_xml_sequential(input_path, output_path)
        
        if not success:
            print("❌ Translation failed")
            return False
        
        # Read the result
        with open(output_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        print("\n📄 Translated XML content:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # Check for proper space preservation
        print("\n🔍 Analyzing space preservation:")
        
        # Check that spaces around <strong> tag are preserved
        if 'micare<strong' in result and '</strong>For' in result:
            print("✅ Spaces around <strong> tag preserved")
        else:
            print("❌ Spaces around <strong> tag lost!")
            if 'micare <strong' in result:
                print("  - Extra space before <strong> detected")
            if '</strong> For' in result:
                print("  - Extra space after </strong> detected")
            return False
        
        # Check that spaces around <em> tag are preserved
        if ' <em>' in result and '</em> ' in result:
            print("✅ Spaces around <em> tag preserved")
        else:
            print("❌ Spaces around <em> tag lost!")
            return False
        
        # Check that spaces around <span> tag are preserved
        if ' <span>' in result and '</span> ' in result:
            print("✅ Spaces around <span> tag preserved")
        else:
            print("❌ Spaces around <span> tag lost!")
            return False
        
        print("\n🎉 SUCCESS: All spaces properly preserved!")
        return True
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except:
            pass

if __name__ == "__main__":
    success = test_space_preservation()
    if success:
        print("\n✅ Space preservation test passed!")
    else:
        print("\n❌ Space preservation test failed!")
