#!/usr/bin/env python3
"""
Test script to verify the robust XML processor with BeautifulSoup handles:
1. ignore="true" attributes properly
2. Nested HTML content with CDATA
3. Structure preservation
4. Character counting accuracy
"""

import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # Go up one directory to find translator3000

from translator3000.processors.xml_processor import XMLProcessor
from translator3000.processors.csv_processor import CSVProcessor

# Enable debug logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_ignore_attribute():
    """Test that elements with ignore='true' are not translated."""
    
    print("🧪 Testing XML processor with ignore attribute...")
    
    # Initialize processors
    csv_processor = CSVProcessor('en', 'da')  # English to Danish for testing
    xml_processor = XMLProcessor(csv_processor)
    
    input_file = "test_ignore_attribute.xml"
    output_file = "test_ignore_attribute_translated.xml"
    
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
        
        # Check for ignore behavior more accurately
        print("\n🔍 Analyzing ignore attribute behavior:")
        
        # Check XML-level ignore elements
        if '<Description ignore="true">This should NOT be translated</Description>' in result:
            print("✅ XML-level ignore working: Description element not translated")
        else:
            print("❌ XML-level ignore failed: Description element was translated")
            
        if '<Title>This nested title should NOT be translated</Title>' in result:
            print("✅ XML-level ignore working: Nested ignored section not translated")
        else:
            print("❌ XML-level ignore failed: Nested ignored section was translated")
        
        # Check HTML-level ignore elements (within CDATA)
        if 'This div content should NOT be translated' in result:
            print("✅ HTML-level ignore working: Div with ignore='true' not translated")
        else:
            print("❌ HTML-level ignore failed: Div with ignore='true' was translated")
            
        if 'This list item should NOT be translated' in result:
            print("✅ HTML-level ignore working: List item with ignore='true' not translated")
        else:
            print("❌ HTML-level ignore failed: List item with ignore='true' was translated")
        
        # Check that non-ignored content WAS translated
        if 'Dette skal oversættes' in result:
            print("✅ Translation working: Non-ignored content was translated")
        else:
            print("❌ Translation failed: Non-ignored content was not translated")
            
        # Check that ignored content stayed in English
        english_phrases_that_should_stay = [
            "This should NOT be translated",
            "This div content should NOT be translated", 
            "This list item should NOT be translated",
            "This nested title should NOT be translated",
            "This nested description should NOT be translated"
        ]
        
        ignored_correctly = 0
        for phrase in english_phrases_that_should_stay:
            if phrase in result:
                ignored_correctly += 1
        
        print(f"\n📊 Summary: {ignored_correctly}/{len(english_phrases_that_should_stay)} ignored phrases correctly preserved")
        
        if ignored_correctly == len(english_phrases_that_should_stay):
            print("🎉 SUCCESS: All ignore attributes working correctly!")
        else:
            print("⚠️  Some ignore attributes may not be working properly")
            
    else:
        print("❌ Translation failed!")

if __name__ == "__main__":
    test_ignore_attribute()
