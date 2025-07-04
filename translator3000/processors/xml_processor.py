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
        # Special handling for elements with CDATA that contain HTML
        if element.text and element.text.strip():
            # Get the element path to help identify specific elements
            element_path = self._get_element_path(element)
            
            # Check if this is likely HTML content (common in CDATA sections)
            is_html = False
            if '<' in element.text and '>' in element.text:
                # Further check the structure - is it a complete HTML element?
                is_html = True
            
            if is_html:
                # Store the element with special type for HTML/CDATA handling
                text_elements.append({
                    'element': element,
                    'type': 'html_content',  # Special marker for HTML content
                    'original': element.text.strip(),
                    'full_text': element.text,
                    'element_path': element_path,  # Store element path for context
                    'tag': element.tag,  # Store the element tag
                    'is_simple_html': self._is_simple_html_content(element.text.strip())  # Flag for simple HTML
                })
            else:
                # Regular text content
                text_elements.append({
                    'element': element,
                    'type': 'text',
                    'original': element.text.strip(),
                    'full_text': element.text,
                    'element_path': element_path,  # Store element path for context
                    'tag': element.tag  # Store the element tag
                })
        
        # Collect tail text
        if element.tail and element.tail.strip():
            element_path = self._get_element_path(element)
            text_elements.append({
                'element': element,
                'type': 'tail',
                'original': element.tail.strip(),
                'full_text': element.tail,
                'element_path': element_path,  # Store element path for context
                'tag': element.tag  # Store the element tag
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
                    element_path = text_data.get('element_path', '')
                    tag = text_data.get('tag', '')
                    
                    # Special handling for HTML content
                    if text_data['type'] == 'html_content':
                        # Use our existing method to translate HTML content
                        translated = self._translate_html_content(original_text, element_path, tag)
                    else:
                        # Regular text translation
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
                    logger.warning(f"Failed to translate XML text in {element_path}: {e}")
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
                
                if text_data['type'] == 'html_content':
                    # For HTML content, we need to preserve the original structure including whitespace
                    if text_data['full_text'].startswith(' ') or text_data['full_text'].startswith('\n'):
                        # Preserve leading whitespace
                        leading_whitespace = ''
                        for char in text_data['full_text']:
                            if char in [' ', '\n', '\t']:
                                leading_whitespace += char
                            else:
                                break
                        element.text = leading_whitespace + translated
                    else:
                        element.text = translated
                elif text_data['type'] == 'text':
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
                element_path = text_data.get('element_path', '')
                tag = text_data.get('tag', '')
                
                # Special handling for HTML content
                if text_data['type'] == 'html_content':
                    # Use a function to extract and translate text while preserving HTML tags
                    translated = self._translate_html_content(original_text, element_path, tag)
                else:
                    # Regular text translation
                    translated = self.csv_processor.translate_text(original_text)
                
                element = text_data['element']
                
                if text_data['type'] == 'html_content':
                    # For HTML content, we need to preserve the original structure including whitespace
                    if text_data['full_text'].startswith(' ') or text_data['full_text'].startswith('\n'):
                        # Preserve leading whitespace
                        leading_whitespace = ''
                        for char in text_data['full_text']:
                            if char in [' ', '\n', '\t']:
                                leading_whitespace += char
                            else:
                                break
                        element.text = leading_whitespace + translated
                    else:
                        element.text = translated
                elif text_data['type'] == 'text':
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
    
    def _translate_html_content(self, html_content: str, element_path: str = None, tag: str = None) -> str:
        """
        Translate HTML content while preserving the structure.
        
        This method preserves HTML tags and only translates the text content.
        
        Args:
            html_content: The HTML content to translate
            element_path: The XML path to the element (for context)
            tag: The element tag (for context)
        """
        try:
            # Simple regex-based HTML parser to extract text content
            import re
            
            # First check if the content is a simple HTML structure with a single tag (like <h1>Text</h1>)
            # This handles cases where we need to translate just a single element regardless of element name
            if self._is_simple_html_content(html_content):
                simple_html_pattern = re.compile(r'^<([a-zA-Z0-9]+)([^>]*)>(.*?)</\1>$', re.DOTALL)
                simple_match = simple_html_pattern.match(html_content.strip())
                
                if simple_match:
                    # It's a simple HTML element with a single tag, handle it directly
                    tag_name = simple_match.group(1)
                    tag_attrs = simple_match.group(2)
                    content = simple_match.group(3).strip()
                    
                    if content:
                        # It's simple text, translate directly
                        translated = self.csv_processor.translate_text(content)
                        logger.debug(f"Translated simple element: '{content[:30]}...' -> '{translated[:30]}...'")
                        return f"<{tag_name}{tag_attrs}>{translated}</{tag_name}>"
            
            # For more complex HTML, use the regular pattern matching
            # This pattern matches HTML tags and content between them
            pattern = re.compile(r'(<[^>]+>)([^<]*)(?=<)')
            
            def translate_match(match):
                tag = match.group(1)  # The HTML tag
                content = match.group(2)  # The text content
                
                # Only translate non-empty content
                if content and content.strip():
                    translated = self.csv_processor.translate_text(content.strip())
                    # Preserve whitespace structure
                    if content.startswith(' '):
                        return tag + ' ' + translated
                    else:
                        return tag + translated
                return tag + content  # Keep empty content unchanged
            
            # Apply the translation to all matches
            result = pattern.sub(translate_match, html_content)
            
            # Handle the last piece of text if it exists
            last_tag_end = html_content.rfind('>')
            if last_tag_end != -1 and last_tag_end < len(html_content) - 1:
                last_text = html_content[last_tag_end + 1:]
                if last_text.strip():
                    translated_last = self.csv_processor.translate_text(last_text.strip())
                    result += translated_last
            
            return result
            
        except Exception as e:
            logger.warning(f"HTML content translation failed for {element_path}: {e}")
            return html_content  # Return original on failure
    
    def _save_xml_pretty(self, tree, output_file: str):
        """Save XML with pretty formatting and CDATA preservation for HTML content."""
        try:
            # First, write the raw XML to a string
            raw_xml = ET.tostring(tree.getroot(), encoding='unicode')
            
            # Convert the XML to a minidom document for pretty printing
            dom = minidom.parseString(f'<?xml version="1.0" ?>{raw_xml}')
            pretty_xml = dom.toprettyxml(indent='    ')
            
            # Clean up extra whitespace that minidom adds
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            
            # Process the content to handle escaping and CDATA sections
            processed_lines = []
            for line in lines:
                # If line contains a content element with HTML inside (either raw or escaped)
                if '<Content>' in line and ('&lt;' in line or '<![CDATA[' in line):
                    # Extract the content
                    content_start = line.find('<Content>') + len('<Content>')
                    content_end = line.find('</Content>')
                    if content_start > 0 and content_end > content_start:
                        content = line[content_start:content_end]
                        
                        # Skip if already in CDATA
                        if '<![CDATA[' in content:
                            processed_lines.append(line)
                            continue
                            
                        # If it contains HTML entities, un-escape them for CDATA
                        if '&lt;' in content and '&gt;' in content:
                            # Un-escape the HTML entities inside CDATA
                            unescaped_content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                            prefix = line[:content_start]
                            suffix = line[content_end:]
                            processed_content = f"<![CDATA[{unescaped_content}]]>"
                            processed_lines.append(f"{prefix}{processed_content}{suffix}")
                            continue
                
                # Otherwise, keep the line as is
                processed_lines.append(line)
            
            # Write the processed content to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(processed_lines))
                f.write('\n')  # End with newline
                
        except Exception as e:
            logger.warning(f"Pretty printing failed: {e}. Saving without formatting.")
            # Fallback to direct write without pretty formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" ?>\n')
                f.write(ET.tostring(tree.getroot(), encoding='unicode'))
    
    def _restore_cdata_for_html_content(self, xml_str: str) -> str:
        """Restore CDATA sections for content that contains HTML tags."""
        try:
            # Extract each Content tag that contains HTML and wrap in CDATA
            content_pattern = re.compile(r'<Content>(.*?)</Content>', re.DOTALL)
            
            def process_content(match):
                content = match.group(1)
                # Check if it contains HTML tags (either raw or escaped)
                has_html_tags = ('<' in content and '>' in content) or ('&lt;' in content and '&gt;' in content)
                
                if has_html_tags:
                    # If it contains escaped HTML entities, convert them back to raw HTML inside CDATA
                    if '&lt;' in content and '&gt;' in content:
                        # Un-escape the HTML entities inside CDATA
                        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    
                    return f'<Content><![CDATA[{content}]]></Content>'
                return match.group(0)
            
            # Process Content elements
            xml_str = content_pattern.sub(process_content, xml_str)
            
            return xml_str
            
        except Exception as e:
            logger.warning(f"CDATA restoration failed: {e}. Returning original XML.")
            return xml_str
    
    def _get_element_path(self, element):
        """Generate a path string to identify the element in the XML tree."""
        # Just return the tag name and any title attribute for now
        # This is a simpler implementation that doesn't rely on parent tracking
        path = element.tag
        
        # Add any identifiable attributes
        if 'Title' in element.attrib:
            path += f"[Title='{element.attrib['Title']}']"
        elif 'Id' in element.attrib:
            path += f"[Id='{element.attrib['Id']}']"
        elif 'id' in element.attrib:
            path += f"[id='{element.attrib['id']}']"
        elif 'ID' in element.attrib:
            path += f"[ID='{element.attrib['ID']}']"
            
        return path
    
    def _is_simple_html_content(self, content: str) -> bool:
        """
        Check if the HTML content is a simple structure with a single root tag.
        
        This helps identify content like "<h1>Text</h1>" that should be handled differently
        from more complex nested HTML structures.
        """
        if not content or not isinstance(content, str):
            return False
            
        import re
        # Pattern to match content with a single HTML tag pair
        pattern = re.compile(r'^<([a-zA-Z0-9]+)([^>]*)>(.*?)</\1>$', re.DOTALL)
        match = pattern.match(content.strip())
        
        if match:
            inner_content = match.group(3).strip()
            # If inner content has no HTML tags, it's simple
            return '<' not in inner_content
            
        return False
