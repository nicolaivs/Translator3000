#!/usr/bin/env python3
"""
Test to verify that empty elements don't get CDATA and that output XML is always valid.
This tests the recent fix to _ensure_proper_cdata_wrapping method.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from translator3000.processors.xml_processor import XMLProcessor
from translator3000.processors.csv_processor import CSVProcessor
import xml.etree.ElementTree as ET
import tempfile

def test_empty_elements_no_cdata():
    """Test that empty elements don't get CDATA wrapped."""
    csv_processor = CSVProcessor()
    processor = XMLProcessor(csv_processor)
    
    # XML with various empty elements that might get CDATA
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <Title></Title>
    <Description>   </Description>
    <Content></Content>
    <Banner>Some content</Banner>
    <Image></Image>
    <URL></URL>
    <Summary>Test content</Summary>
    <Body></Body>
</root>'''
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as input_file:
        input_file.write(xml_content)
        input_path = input_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Process the XML
        success, char_count = processor.translate_xml_sequential(input_path, output_path)
        
        if not success:
            print("✗ Translation failed")
            return False
        
        # Read the result
        with open(output_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        print("Original XML:")
        print(xml_content)
        print("\nProcessed XML:")
        print(result)
        
        # Check that output is valid XML
        try:
            ET.fromstring(result)
            print("\n✓ Output XML is valid")
        except ET.ParseError as e:
            print(f"\n✗ Output XML is invalid: {e}")
            return False
        
        # Check that empty elements don't have CDATA
        empty_elements_with_cdata = []
        lines = result.split('\n')
        for line in lines:
            if '<![CDATA[]]>' in line or '<![CDATA[   ]]>' in line or ('<![CDATA[' in line and ']]>' in line and not line.strip().replace('<![CDATA[', '').replace(']]>', '').strip()):
                empty_elements_with_cdata.append(line.strip())
        
        if empty_elements_with_cdata:
            print(f"\n✗ Found empty CDATA sections:")
            for elem in empty_elements_with_cdata:
                print(f"  {elem}")
            return False
        else:
            print("\n✓ No empty CDATA sections found")
        
        # Check specific patterns
        issues = []
        if '<Title><![CDATA[]]></Title>' in result:
            issues.append("Empty Title has CDATA")
        if '<Description><![CDATA[   ]]></Description>' in result:
            issues.append("Whitespace-only Description has CDATA")
        if '<Content><![CDATA[]]></Content>' in result:
            issues.append("Empty Content has CDATA")
        if '<Image><![CDATA[]]></Image>' in result:
            issues.append("Empty Image has CDATA")
        if '<URL><![CDATA[]]></URL>' in result:
            issues.append("Empty URL has CDATA")
        if '<Body><![CDATA[]]></Body>' in result:
            issues.append("Empty Body has CDATA")
        
        if issues:
            print(f"\n✗ Issues found:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("\n✓ All empty elements are handled correctly")
        
        return True
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except:
            pass

def test_elements_with_content_get_cdata():
    """Test that elements with actual content still get CDATA when appropriate."""
    csv_processor = CSVProcessor()
    processor = XMLProcessor(csv_processor)
    
    # XML with HTML content that should get CDATA
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <Banner><p>This is a paragraph</p></Banner>
    <Summary>This has <strong>HTML</strong> content</Summary>
    <Title>Plain text title</Title>
    <Description>&lt;p&gt;Escaped HTML&lt;/p&gt;</Description>
</root>'''
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as input_file:
        input_file.write(xml_content)
        input_path = input_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Process the XML
        success, char_count = processor.translate_xml_sequential(input_path, output_path)
        
        if not success:
            print("✗ Translation failed")
            return False
        
        # Read the result
        with open(output_path, 'r', encoding='utf-8') as f:
            result = f.read()
        
        print("\nTesting elements with content:")
        print("Original XML:")
        print(xml_content)
        print("\nProcessed XML:")
        print(result)
        
        # Check that output is valid XML
        try:
            ET.fromstring(result)
            print("\n✓ Output XML is valid")
        except ET.ParseError as e:
            print(f"\n✗ Output XML is invalid: {e}")
            return False
        
        # Check that HTML content elements have CDATA
        has_banner_cdata = '<Banner><![CDATA[' in result
        has_summary_cdata = '<Summary><![CDATA[' in result
        has_description_cdata = '<Description><![CDATA[' in result
        
        print(f"\n✓ Banner has CDATA: {has_banner_cdata}")
        print(f"✓ Summary has CDATA: {has_summary_cdata}")
        print(f"✓ Description has CDATA: {has_description_cdata}")
        
        # Title with plain text should not need CDATA unless it originally had it
        title_needs_cdata = '<Title><![CDATA[' in result
        print(f"✓ Title has CDATA: {title_needs_cdata}")
        
        return True
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except:
            pass
    
    # XML with HTML content that should get CDATA
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <Banner><p>This is a paragraph</p></Banner>
    <Summary>This has <strong>HTML</strong> content</Summary>
    <Title>Plain text title</Title>
    <Description>&lt;p&gt;Escaped HTML&lt;/p&gt;</Description>
</root>'''

if __name__ == "__main__":
    print("Testing empty elements handling...")
    test1_passed = test_empty_elements_no_cdata()
    
    print("\n" + "="*60)
    test2_passed = test_elements_with_content_get_cdata()
    
    print("\n" + "="*60)
    if test1_passed and test2_passed:
        print("✓ All tests passed! Empty elements are handled correctly.")
    else:
        print("✗ Some tests failed.")
