"""
Test for XML processor with CDATA handling to verify the fix for Banner/Title content issue.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path to be able to import translator3000 modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000.processors.csv_processor import CSVProcessor
from translator3000.processors.xml_processor import XMLProcessor
from translator3000.config import TEST_SOURCE_DIR, TARGET_DIR

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_xml_cdata_fix():
    """Test the fix for XML CDATA handling for Banner/Title content."""
    
    # Test file paths - using source directly since TEST_SOURCE_DIR may be customized
    source_dir = Path(__file__).parent.parent / "source"
    source_file = source_dir / "test_banner_issue.xml"
    output_file = TARGET_DIR / "test_banner_fix.xml"
    
    # Make sure source file exists
    if not source_file.exists():
        logger.error(f"Test source file not found: {source_file}")
        return False
    
    # Initialize processors
    csv_processor = CSVProcessor("en", "no", delay_between_requests=0.01)
    xml_processor = XMLProcessor(csv_processor)
    
    # Translate the XML file
    logger.info(f"Testing XML CDATA Banner/Title fix with source: {source_file}")
    success, chars = xml_processor.translate_xml(
        str(source_file), 
        str(output_file),
        use_multithreading=False  # Test sequential processing first
    )
    
    if success:
        logger.info(f"XML translation completed successfully: {output_file}")
        logger.info(f"Characters translated: {chars}")
        return True
    else:
        logger.error("XML translation failed")
        return False

if __name__ == "__main__":
    test_xml_cdata_fix()
