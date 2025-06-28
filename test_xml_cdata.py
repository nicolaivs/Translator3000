#!/usr/bin/env python3
"""
Test script to check how current XML translation handles CDATA and HTML content.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

def test_xml_parsing():
    """Test how ElementTree handles CDATA content."""
    
    # Read the test file
    input_file = r"c:\Users\nicolai\OneDrive - Easyday ApS\Code\Python\Translator3000\source\test_html_xml.xml"
    
    try:
        # Parse the XML file
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        print("=== Testing XML CDATA and HTML content ===\n")
        
        # Find the description elements with CDATA
        for product in root.findall('product'):
            print(f"Product ID: {product.get('id')}")
            
            # Check description content
            desc = product.find('description')
            if desc is not None:
                print(f"Description text: {repr(desc.text)}")
                print(f"Description text type: {type(desc.text)}")
                print(f"Description text stripped: {desc.text.strip() if desc.text else 'None'}")
                print()
            
            # Check features content
            features = product.find('features')
            if features is not None:
                print(f"Features text: {repr(features.text)}")
                print(f"Features text type: {type(features.text)}")
                print(f"Features text stripped: {features.text.strip() if features.text else 'None'}")
                print()
        
        # Test what happens when we convert back to string
        print("=== XML String Representation ===")
        xml_str = ET.tostring(root, encoding='unicode')
        print(xml_str[:500] + "..." if len(xml_str) > 500 else xml_str)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_xml_parsing()
