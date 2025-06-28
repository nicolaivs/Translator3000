#!/usr/bin/env python3
"""
Test translation with a real XML file.
"""

import sys
import os
sys.path.append(os.getcwd())

from translator3000 import CSVTranslator

def test_real_xml():
    """Test with a real XML file."""
    
    # Initialize translator
    translator = CSVTranslator(source_lang='en', target_lang='da')  # English to Danish
    
    # Test files
    input_file = r"c:\Users\nicolai\OneDrive - Easyday ApS\Code\Python\Translator3000\source\sample_products.xml"
    output_file = r"c:\Users\nicolai\OneDrive - Easyday ApS\Code\Python\Translator3000\target\sample_products_danish.xml"
    
    # Create target directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print("Testing XML translation with real product data...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print("Input file not found. Checking available files...")
        source_dir = os.path.dirname(input_file)
        if os.path.exists(source_dir):
            files = [f for f in os.listdir(source_dir) if f.endswith('.xml')]
            print(f"Available XML files: {files}")
        return
    
    # Translate
    success = translator.translate_xml(input_file, output_file)
    
    if success:
        print("\n=== Translation completed successfully! ===")
        
        # Show first few lines of output
        print("\n=== First 20 lines of output ===")
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:20]):
                print(f"{i+1:2d}: {line.rstrip()}")
    else:
        print("Translation failed!")

if __name__ == "__main__":
    test_real_xml()
