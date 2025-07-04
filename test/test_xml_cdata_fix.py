"""
Test script to verify the XML CDATA translation fix.

This script specifically tests the handling of CDATA sections in XML files,
ensuring that HTML content in different sections is translated correctly
without mixing content between different elements.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000.config import TEST_SOURCE_DIR, TARGET_DIR
from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor
from translator3000.utils.language_utils import get_language_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("translation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_xml_cdata_translation():
    """Test XML translation with CDATA sections."""
    # Test translating a file with CDATA sections
    source_lang = 'en'
    target_lang = 'no'  # Norwegian
    
    # Use the source directory from the project root, not the custom test directory
    input_file = Path(__file__).parent.parent / "source" / "test_html_xml.xml"
    output_file = TARGET_DIR / "test_cdata_fix.xml"
    
    # Create processors
    csv_processor = CSVProcessor(
        source_lang=source_lang,
        target_lang=target_lang,
        delay_between_requests=0.01  # Fast for testing
    )
    
    xml_processor = XMLProcessor(csv_processor)
    
    # Translate the file
    logger.info(f"Testing XML CDATA translation from {source_lang} to {target_lang}")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    
    # Translate with single-threaded mode for predictable behavior
    success, chars = xml_processor.translate_xml(
        input_file=str(input_file),
        output_file=str(output_file),
        use_multithreading=False
    )
    
    if success:
        logger.info(f"Successfully translated XML file with CDATA sections")
        logger.info(f"Translated {chars} characters")
        logger.info(f"Output saved to: {output_file}")
        return True
    else:
        logger.error(f"Failed to translate XML file")
        return False


if __name__ == "__main__":
    try:
        test_xml_cdata_translation()
    except Exception as e:
        logger.exception(f"Error during test: {e}")
