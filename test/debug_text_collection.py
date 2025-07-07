#!/usr/bin/env python3
"""
Debug script to see what text elements are being collected.
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xml.etree.ElementTree as ET
from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def debug_text_collection():
    """Debug what text elements are being collected."""
    
    input_file = "test_ignore_case_fix.xml"
    
    # Read the raw XML content
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_xml_content = f.read()
    
    # Parse the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Create processors
    csv_processor = CSVProcessor('en', 'da')
    xml_processor = XMLProcessor(csv_processor)
    
    # Collect text elements
    text_elements = []
    xml_processor._collect_text_elements(root, text_elements, raw_xml_content)
    
    print(f"Found {len(text_elements)} text elements:")
    for i, element_data in enumerate(text_elements):
        print(f"\n{i+1}. Element: {element_data['tag']}")
        print(f"   Type: {element_data['type']}")
        print(f"   Original: {repr(element_data['original'])}")
        print(f"   Full text: {repr(element_data['full_text'])}")
        element = element_data['element']
        print(f"   Attributes: {element.attrib}")
        print(f"   Element path: {element_data['element_path']}")

if __name__ == "__main__":
    debug_text_collection()
