#!/usr/bin/env python3
"""
Quick test of XML translation with HTML/CDATA content.
"""

import sys
import os
sys.path.append(os.getcwd())

import sys
import os
# Add parent directory to path so we can import translator3000
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from translator3000 import CSVTranslator

def test_xml_html_translation():
    """Test XML translation with HTML and CDATA content."""
    
    # Initialize translator
    translator = CSVTranslator(source_lang='en', target_lang='no')
    
    # Test files (using relative paths from the main project directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "source", "test_html_xml.xml")
    output_file = os.path.join(project_root, "target", "test_html_xml_translated.xml")
    
    # Create target directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print("Testing XML translation with HTML/CDATA content...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    # Translate
    success = translator.translate_xml(input_file, output_file)
    
    if success:
        print("\n=== Translation completed successfully! ===")
        
        # Show the output
        print("\n=== Output file content ===")
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    else:
        print("Translation failed!")

if __name__ == "__main__":
    test_xml_html_translation()
