"""
Test translation of HTML content with simple paragraph tags.

This test verifies that all paragraphs in HTML content are correctly translated,
especially focusing on the first paragraph which was previously not being translated.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to be able to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor
from translator3000.utils.logging_utils import setup_logging
from translator3000.config import load_config

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def test_paragraph_translation():
    """Test that all paragraphs in HTML content are translated correctly."""
    
    # Create a simple XML file with HTML content containing multiple paragraphs
    test_xml = """<?xml version="1.0" encoding="utf-8"?>
<root>
    <Content><![CDATA[<p>First paragraph that should be translated.</p>
<p>Second paragraph that should also be translated.</p>
<p data-attr="value">Third paragraph with attributes that should be translated.</p>]]></Content>
</root>
"""
    
    # Create test files
    test_input_file = "test_paragraph_translation_input.xml"
    test_output_file = "test_paragraph_translation_output.xml"
    
    # Write the test XML to a file
    with open(test_input_file, "w", encoding="utf-8") as f:
        f.write(test_xml)
    
    # Load configuration
    load_config()
    
    # Create processors
    csv_processor = CSVProcessor()
    xml_processor = XMLProcessor(csv_processor)
    
    # Set mock translation for testing
    csv_processor.translate_text = lambda text: f"[TRANSLATED] {text}"
    
    # Translate the XML
    success, chars = xml_processor.translate_xml(test_input_file, test_output_file)
    
    # Read the output file
    with open(test_output_file, "r", encoding="utf-8") as f:
        output_content = f.read()
    
    # Clean up
    try:
        os.remove(test_input_file)
        os.remove(test_output_file)
    except:
        pass
    
    # Check results
    logger.info(f"Translation success: {success}")
    logger.info(f"Characters translated: {chars}")
    logger.info(f"Output content: {output_content}")
    
    # Verify all paragraphs were translated
    assert "[TRANSLATED] First paragraph that should be translated." in output_content, "First paragraph was not translated"
    assert "[TRANSLATED] Second paragraph that should also be translated." in output_content, "Second paragraph was not translated"
    assert "[TRANSLATED] Third paragraph with attributes that should be translated." in output_content, "Third paragraph was not translated"
    
    logger.info("All paragraphs were successfully translated!")

if __name__ == "__main__":
    test_paragraph_translation()
