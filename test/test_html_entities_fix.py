"""
Test for XML processor with improved CDATA handling for HTML content.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path to be able to import translator3000 modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor
from translator3000.config import TARGET_DIR

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_xml_html_handling():
    """Test XML processing with HTML content handling."""
    
    # Test file paths
    source_dir = Path(__file__).parent.parent / "source"
    source_file = source_dir / "test_html_xml_2.xml"
    output_file = TARGET_DIR / "test_html_xml_2_fixed.xml"
    
    # Make sure source file exists
    if not source_file.exists():
        logger.error(f"Test source file not found: {source_file}")
        return False
    
    # Initialize processors
    csv_processor = CSVProcessor("en", "no", delay_between_requests=0.01)
    xml_processor = XMLProcessor(csv_processor)
    
    # Translate the XML file
    logger.info(f"Testing XML HTML handling with source: {source_file}")
    success, chars = xml_processor.translate_xml(
        str(source_file), 
        str(output_file),
        use_multithreading=False  # Test sequential processing
    )
    
    if success:
        logger.info(f"XML translation completed successfully: {output_file}")
        logger.info(f"Characters translated: {chars}")
        return True
    else:
        logger.error("XML translation failed")
        return False

if __name__ == "__main__":
    test_xml_html_handling()
