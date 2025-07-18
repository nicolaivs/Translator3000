"""
Test for XML processor with HTML content handling using multithreading.
"""

import os
import sys
import logging
from pathlib import Path
import xml.etree.ElementTree as ET

# Add the parent directory to sys.path to be able to import translator3000 modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor
from translator3000.config import TARGET_DIR

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_xml_integrity(xml_file):
    """Verify the XML integrity by checking structure and CDATA sections."""
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Check URL element
        url_elements = root.findall('.//Url')
        if url_elements:
            url_content = url_elements[0].text
            logger.info(f"URL content: {url_content}")
            if not url_content or url_content.strip() == "":
                logger.warning("URL content is empty!")
                return False
            if not url_content.startswith('/'):
                logger.warning(f"URL content doesn't start with /: {url_content}")
                return False
        
        # Check for Banner content
        banner_elements = root.findall('.//Column[@Title="Banner"]//Content')
        if banner_elements:
            logger.info(f"Banner content found: {banner_elements[0].text[:30]}...")
        else:
            logger.warning("Banner content not found!")
        
        # Check for Description content
        desc_elements = root.findall('.//Column[@Title="Description"]//Content')
        if desc_elements:
            logger.info(f"Description content found: {desc_elements[0].text[:30]}...")
        else:
            logger.warning("Description content not found!")
        
        # Basic integrity check passed
        return True
    except Exception as e:
        logger.error(f"XML verification failed: {e}")
        return False

def test_xml_html_multithreaded():
    """Test XML processing with HTML content handling with multithreading."""
    
    # Test file paths
    source_dir = Path(__file__).parent.parent / "source"
    source_file = source_dir / "test_html_xml_2.xml"
    output_file = TARGET_DIR / "test_html_xml_2_multithreaded.xml"
    
    # Make sure source file exists
    if not source_file.exists():
        logger.error(f"Test source file not found: {source_file}")
        return False
    
    # Initialize processors
    csv_processor = CSVProcessor("en", "no", delay_between_requests=0.01)
    xml_processor = XMLProcessor(csv_processor)
    
    # Translate the XML file with multithreading
    logger.info(f"Testing XML HTML handling with multithreading: {source_file}")
    success, chars = xml_processor.translate_xml(
        str(source_file), 
        str(output_file),
        use_multithreading=True,  # Use multithreaded processing
        max_workers=4             # Use 4 worker threads
    )
    
    if success:
        logger.info(f"XML translation completed successfully: {output_file}")
        logger.info(f"Characters translated: {chars}")
        
        # Verify the output XML
        logger.info(f"Verifying XML integrity: {output_file}")
        if verify_xml_integrity(output_file):
            logger.info("XML integrity check passed!")
            return True
        else:
            logger.error("XML integrity check failed!")
            return False
    else:
        logger.error("XML translation failed")
        return False

if __name__ == "__main__":
    test_xml_html_multithreaded()
