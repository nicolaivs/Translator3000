"""
XML processing module for Translator3000.

This module handles XML file translation while preserving structure, attributes,
and supporting multithreaded processing for performance.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
import threading
import concurrent.futures
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..config import get_config

logger = logging.getLogger(__name__)


class XMLProcessor:
    """Handles XML file translation with structure preservation."""
    
    def __init__(self, csv_processor):
        """
        Initialize XML processor with a CSV processor for text translation.
        
        Args:
            csv_processor: CSVProcessor instance for text translation logic
        """
        self.csv_processor = csv_processor
        self.config = get_config()
    
    def translate_xml(self, input_file: str, output_file: str, use_multithreading: bool = True, max_workers: int = None) -> tuple[bool, int]:
        """
        Translate text content in XML file while preserving structure and attributes.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            use_multithreading: Whether to use multithreading (default: True)
            max_workers: Number of worker threads (uses config if None)
            
        Returns:
            Tuple of (success, characters_translated)
        """
        # Use config default if not specified
        if max_workers is None:
            max_workers = self.config['xml_max_workers']
            
        if use_multithreading:
            return self.translate_xml_multithreaded(input_file, output_file, max_workers)
        else:
            return self.translate_xml_sequential(input_file, output_file)

    def translate_xml_sequential(self, input_file: str, output_file: str) -> tuple[bool, int]:
        """
        Translate text content in XML file sequentially.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            
        Returns:
            Tuple of (success, characters_translated)
        """
        try:
            logger.info(f"Reading XML file: {input_file}")
            
            # Parse the XML file
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Collect all text elements that need translation
            text_elements = []
            self._collect_text_elements(root, text_elements)
            
            total_elements = len(text_elements)
            logger.info(f"Found {total_elements} text elements to translate")
            
            if total_elements == 0:
                # No text to translate, just copy the file
                logger.info("No text elements found, copying file as-is")
                tree.write(output_file, encoding='utf-8', xml_declaration=True)
                return True, 0
            
            # Use sequential translation
            logger.info("Using single-threaded XML translation")
            success, chars_translated = self._translate_xml_elements_sequential(text_elements)
            
            if not success:
                logger.error("XML translation failed")
                return False, 0
            
            # Save the translated XML
            logger.info(f"Saving translated XML to: {output_file}")
            self._save_xml_pretty(tree, output_file)
            
            logger.info(f"XML translation completed successfully!")
            logger.info(f"Translated {total_elements} text elements")
            
            return True, chars_translated
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return False, 0
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            return False, 0
        except Exception as e:
            logger.error(f"Error during XML translation: {e}")
            return False, 0
    
    def translate_xml_multithreaded(self, input_file: str, output_file: str, max_workers: int = None) -> tuple[bool, int]:
        """
        Translate text content in XML file using multithreading for better performance.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            max_workers: Number of worker threads (uses config if None)
            
        Returns:
            Tuple of (success, characters_translated)
        """
        # Use config default if not specified
        if max_workers is None:
            max_workers = self.config['xml_max_workers']
            
        try:
            logger.info(f"Reading XML file: {input_file}")
            
            # Parse the XML file
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Collect all text elements that need translation
            text_elements = []
            self._collect_text_elements(root, text_elements)
            
            total_elements = len(text_elements)
            logger.info(f"Found {total_elements} text elements to translate")
            
            if total_elements == 0:
                # No text to translate, just copy the file
                logger.info("No text elements found, copying file as-is")
                tree.write(output_file, encoding='utf-8', xml_declaration=True)
                return True, 0
            
            # Use multithreading if we have enough elements
            if total_elements > self.config['multithreading_threshold'] and max_workers > 1:
                logger.info(f"Using multithreaded XML translation with {max_workers} workers")
                success, chars_translated = self._translate_xml_elements_multithreaded(text_elements, max_workers)
            else:
                logger.info("Using single-threaded XML translation")
                success, chars_translated = self._translate_xml_elements_sequential(text_elements)
            
            if not success:
                logger.error("XML translation failed")
                return False, 0
            
            # Save the translated XML
            logger.info(f"Saving translated XML to: {output_file}")
            self._save_xml_pretty(tree, output_file)
            
            logger.info(f"XML translation completed successfully!")
            logger.info(f"Translated {total_elements} text elements")
            
            return True, chars_translated
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return False, 0
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            return False, 0
        except Exception as e:
            logger.error(f"Error during XML translation: {e}")
            return False, 0

    def _collect_text_elements(self, element, text_elements: List):
        """Collect all text elements that need translation."""
        # Collect element text
        if element.text and element.text.strip():
            text_elements.append({
                'element': element,
                'type': 'text',
                'original': element.text.strip(),
                'full_text': element.text
            })
        
        # Collect tail text
        if element.tail and element.tail.strip():
            text_elements.append({
                'element': element,
                'type': 'tail',
                'original': element.tail.strip(),
                'full_text': element.tail
            })
        
        # Process children recursively
        for child in element:
            self._collect_text_elements(child, text_elements)

    def _translate_xml_elements_multithreaded(self, text_elements: List, max_workers: int) -> tuple[bool, int]:
        """Translate XML text elements using multithreading."""
        try:
            # Thread-safe progress tracking
            progress_lock = threading.Lock()
            progress_counter = [0]
            total_elements = len(text_elements)
            total_characters = sum(len(text_data['original']) for text_data in text_elements)
            
            def translate_element_text(text_data):
                """Translate a single text element."""
                try:
                    original_text = text_data['original']
                    translated = self.csv_processor.translate_text(original_text)
                    
                    # Update progress in thread-safe manner
                    with progress_lock:
                        progress_counter[0] += 1
                        if progress_counter[0] % self.config['progress_interval'] == 0 or progress_counter[0] == total_elements:
                            logger.info(f"Progress: {progress_counter[0]}/{total_elements} elements processed")
                    
                    return {
                        'text_data': text_data,
                        'translated': translated
                    }
                except Exception as e:
                    logger.warning(f"Failed to translate XML text '{original_text[:50]}...': {e}")
                    return {
                        'text_data': text_data,
                        'translated': original_text  # Fallback to original
                    }
            
            # Use ThreadPoolExecutor for concurrent translation
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all translation tasks
                future_to_element = {
                    executor.submit(translate_element_text, text_data): text_data 
                    for text_data in text_elements
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_element):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        # Handle individual translation failures
                        text_data = future_to_element[future]
                        logger.warning(f"Translation failed for XML element: {e}")
                        results.append({
                            'text_data': text_data,
                            'translated': text_data['original']  # Fallback to original
                        })
            
            # Apply the translated results back to the XML elements
            for result in results:
                text_data = result['text_data']
                translated = result['translated']
                element = text_data['element']
                
                if text_data['type'] == 'text':
                    # Replace element text while preserving whitespace structure
                    if element.text.startswith(' ') or element.text.startswith('\n'):
                        element.text = element.text.replace(text_data['original'], translated)
                    else:
                        element.text = translated
                elif text_data['type'] == 'tail':
                    # Replace tail text while preserving whitespace structure
                    if element.tail.startswith(' ') or element.tail.startswith('\n'):
                        element.tail = element.tail.replace(text_data['original'], translated)
                    else:
                        element.tail = translated
            
            logger.info(f"Completed multithreaded XML translation")
            return True, total_characters
            
        except Exception as e:
            logger.error(f"Multithreaded XML translation failed: {e}")
            return False, 0

    def _translate_xml_elements_sequential(self, text_elements: List) -> tuple[bool, int]:
        """Translate XML text elements sequentially (fallback method)."""
        try:
            total_elements = len(text_elements)
            total_characters = 0
            
            for idx, text_data in enumerate(text_elements):
                if (idx + 1) % self.config['progress_interval'] == 0 or (idx + 1) == total_elements:
                    logger.info(f"Progress: {idx + 1}/{total_elements} elements processed")
                
                original_text = text_data['original']
                total_characters += len(original_text)  # Count original characters
                translated = self.csv_processor.translate_text(original_text)
                element = text_data['element']
                
                if text_data['type'] == 'text':
                    # Replace element text while preserving whitespace structure
                    if element.text.startswith(' ') or element.text.startswith('\n'):
                        element.text = element.text.replace(original_text, translated)
                    else:
                        element.text = translated
                elif text_data['type'] == 'tail':
                    # Replace tail text while preserving whitespace structure
                    if element.tail.startswith(' ') or element.tail.startswith('\n'):
                        element.tail = element.tail.replace(original_text, translated)
                    else:
                        element.tail = translated
            
            return True, total_characters
            
        except Exception as e:
            logger.error(f"Sequential XML translation failed: {e}")
            return False, 0
    
    def _save_xml_pretty(self, tree, output_file: str):
        """Save XML with pretty formatting and CDATA preservation for HTML content."""
        # Convert to string
        xml_str = ET.tostring(tree.getroot(), encoding='unicode')
        
        # Restore CDATA sections for HTML content
        xml_str = self._restore_cdata_for_html_content(xml_str)
        
        # Parse with minidom for pretty printing
        try:
            dom = minidom.parseString(xml_str)
            # Get pretty formatted XML with 4-space indentation to match original
            pretty_xml = dom.toprettyxml(indent="    ")
            
            # Clean up extra whitespace that minidom adds
            lines = pretty_xml.split('\n')
            cleaned_lines = []
            for line in lines:
                if line.strip():  # Only keep non-empty lines
                    cleaned_lines.append(line)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(cleaned_lines))
                f.write('\n')  # End with newline
            
        except Exception as e:
            logger.warning(f"Pretty printing failed: {e}. Saving without formatting.")
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    def _restore_cdata_for_html_content(self, xml_str: str) -> str:
        """Restore CDATA sections for content that contains HTML tags."""
        def replace_html_content(match):
            content = match.group(1)
            # Check if content contains HTML tags
            if '<' in content and '>' in content:
                # Wrap in CDATA
                return f'<![CDATA[{content}]]>'
            return content
        
        # Look for escaped HTML content and wrap in CDATA
        html_pattern = re.compile(r'&lt;[^&]*&gt;.*?&lt;/[^&]*&gt;', re.DOTALL)
        xml_str = html_pattern.sub(lambda m: f'<![CDATA[{m.group(0).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")}]]>', xml_str)
        
        return xml_str
