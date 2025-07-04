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
            
            # Special handling for URL elements - preserve the path structure
            if element.tag == 'Url':
                # URLs should be handled specially to maintain their structure
                url_text = element.text.strip()
                if url_text.startswith('/'):
                    # This is a path URL, only translate the parts after the language code
                    parts = url_text.split('/')
                    if len(parts) > 2:  # Has at least /en/something
                        # Replace the language code with a placeholder
                        lang_code = parts[1].lower()
                        if lang_code in ('en', 'de', 'fr', 'es', 'it', 'da', 'sv', 'nb', 'nl'):
                            # Collect for translation with special handling
                            text_elements.append({
                                'element': element,
                                'type': 'url',
                                'original': '/'.join(parts[2:]),  # Collect everything after language code
                                'full_text': element.text,
                                'element_path': element_path,
                                'tag': element.tag,
                                'prefix': f'/{lang_code}/'  # Store the prefix to restore later
                            })
                            return  # Skip normal text processing for URLs
            
            # Check if this is likely HTML content (common in CDATA sections)
            is_html = False
            if '<' in element.text and '>' in element.text:
                # Raw HTML tags
                is_html = True
            elif '&lt;' in element.text and '&gt;' in element.text:
                # Escaped HTML entities
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
                    'is_simple_html': self._is_simple_html_content(element.text.strip()),  # Flag for simple HTML
                    'has_entities': '&lt;' in element.text and '&gt;' in element.text  # Track if it contains HTML entities
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
                    
                    # Special handling based on element type
                    if text_data['type'] == 'html_content':
                        # Use our existing method to translate HTML content
                        translated = self._translate_html_content(original_text, element_path, tag)
                    elif text_data['type'] == 'url':
                        # Special handling for URLs
                        translated = self.csv_processor.translate_text(original_text)
                        # Preserve URL structure with the prefix
                        prefix = text_data.get('prefix', '/')
                        translated = f"{prefix}{translated}"
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
                        'translated': translated,
                        'element_path': element_path,  # Include path for debugging
                        'tag': tag  # Include tag for debugging
                    }
                except Exception as e:
                    logger.warning(f"Failed to translate XML text in {element_path}: {e}")
                    return {
                        'text_data': text_data,
                        'translated': original_text,  # Fallback to original
                        'element_path': element_path,
                        'tag': tag
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
                            'translated': text_data['original'],  # Fallback to original
                            'element_path': text_data.get('element_path', ''),
                            'tag': text_data.get('tag', '')
                        })
            
            # Sort results by the original order to ensure consistency
            # This is critical for thread safety as results can come back in any order
            original_order = {id(text_data): i for i, text_data in enumerate(text_elements)}
            results.sort(key=lambda r: original_order[id(r['text_data'])])
            
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
                
                # Special handling based on element type
                if text_data['type'] == 'html_content':
                    # Use a function to extract and translate text while preserving HTML tags
                    translated = self._translate_html_content(original_text, element_path, tag)
                elif text_data['type'] == 'url':
                    # Special handling for URLs
                    translated = self.csv_processor.translate_text(original_text)
                    # Preserve URL structure with the prefix
                    prefix = text_data.get('prefix', '/')
                    translated = f"{prefix}{translated}"
                else:
                    # Regular text translation
                    translated = self.csv_processor.translate_text(original_text)
                
                element = text_data['element']
                
                # Apply translation based on element type
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
                elif text_data['type'] == 'url':
                    # URL elements just get the translated text directly
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
            # Ensure we're working with a string
            if not isinstance(html_content, str):
                html_content = str(html_content)
                
            # Normalize line endings
            html_content = html_content.replace('\r\n', '\n')
            
            # First, check if HTML content is escaped and unescape it for processing
            unescaped_content = html_content
            if '&lt;' in html_content and '&gt;' in html_content:
                unescaped_content = html_content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                logger.debug(f"Unescaped HTML content for translation: {unescaped_content[:50]}...")
            
            # Simple regex-based HTML parser to extract text content
            import re
            
            # First check if the content is a simple HTML structure with a single tag (like <h1>Text</h1>)
            simple_html_pattern = re.compile(r'^<([a-zA-Z0-9]+)([^>]*)>(.*?)</\1>$', re.DOTALL)
            simple_match = simple_html_pattern.match(unescaped_content.strip())
            
            if simple_match:
                # It's a simple HTML element with a single tag, handle it directly
                tag_name = simple_match.group(1)
                tag_attrs = simple_match.group(2)
                content = simple_match.group(3).strip()
                
                if content:
                    # Check if this contains further HTML tags
                    if '<' in content and '>' in content:
                        # It has nested HTML, process it recursively
                        translated_content = self._translate_html_content(content, element_path, tag)
                        return f"<{tag_name}{tag_attrs}>{translated_content}</{tag_name}>"
                    else:
                        # It's simple text, translate directly
                        translated = self.csv_processor.translate_text(content)
                        logger.debug(f"Translated simple element: '{content[:30]}...' -> '{translated[:30]}...'")
                        return f"<{tag_name}{tag_attrs}>{translated}</{tag_name}>"
            
            # For more complex HTML, use a pattern that handles HTML tags and content between them
            pattern = re.compile(r'(<[^>]+>)([^<]*)(?=<|$)', re.DOTALL)
            
            def translate_match(match):
                tag = match.group(1)  # The HTML tag
                content = match.group(2)  # The text content
                
                # Only translate non-empty content
                if content and content.strip():
                    # Encode special characters if present to avoid encoding issues
                    translated = self.csv_processor.translate_text(content.strip())
                    
                    # Preserve whitespace structure
                    if content.startswith(' '):
                        return tag + ' ' + translated + content[len(content.strip())+1:]
                    elif content.endswith(' '):
                        return tag + translated + ' '
                    else:
                        return tag + translated
                
                return tag + content  # Keep empty content unchanged
            
            # Apply the translation to all matches
            result = pattern.sub(translate_match, unescaped_content)
            
            return result
            
        except Exception as e:
            logger.warning(f"HTML content translation failed for {element_path}: {e}")
            return html_content  # Return original on failure
    
    def _save_xml_pretty(self, tree, output_file: str):
        """
        Save XML with pretty formatting and CDATA preservation for HTML content.
        
        This method ensures HTML content is properly wrapped in CDATA sections and
        that character encoding is preserved correctly.
        """
        try:
            # Create a string representation of the XML with proper encoding
            xml_string = ET.tostring(tree.getroot(), encoding='utf-8', method='xml').decode('utf-8')
            
            # Process all tags that might contain HTML and wrap them in CDATA
            processed_xml = self._process_all_html_content(xml_string)
            
            try:
                # Parse the processed XML for pretty printing
                dom = minidom.parseString(f'<?xml version="1.0" encoding="utf-8" ?>{processed_xml}')
                pretty_xml = dom.toprettyxml(indent='    ', encoding='utf-8').decode('utf-8')
                
                # Clean up extra whitespace that minidom adds
                lines = []
                for line in pretty_xml.split('\n'):
                    if line.strip():  # Only keep non-empty lines
                        lines.append(line)
                
                # Write to file with explicit UTF-8 encoding
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                    f.write('\n')  # End with newline
            except Exception as pretty_error:
                logger.warning(f"Pretty printing failed: {pretty_error}. Writing processed XML directly.")
                # Fallback to direct write of processed XML
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="utf-8" ?>\n')
                    f.write(processed_xml)
        
        except Exception as e:
            logger.error(f"XML saving failed: {e}. Using basic output.")
            # Last resort fallback
            try:
                tree.write(output_file, encoding='utf-8', xml_declaration=True)
            except Exception as write_error:
                logger.error(f"Basic XML writing failed: {write_error}")
                # Try to save raw string
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="utf-8" ?>\n')
                    f.write(ET.tostring(tree.getroot(), encoding='utf-8').decode('utf-8'))

    def _process_all_html_content(self, xml_str: str) -> str:
        """
        Process all elements that might contain HTML content in the XML.
        
        This is a comprehensive method that handles all types of HTML content,
        ensuring proper CDATA wrapping and character encoding.
        """
        try:
            import re
            
            # Define all possible tag patterns that might contain HTML
            patterns = {
                'Content': re.compile(r'<Content>(.*?)</Content>', re.DOTALL),
                'Title': re.compile(r'<Title>(.*?)</Title>', re.DOTALL),
                'Description': re.compile(r'<Description>(.*?)</Description>', re.DOTALL),
                'Url': re.compile(r'<Url([^>]*)>(.*?)</Url>', re.DOTALL),
                # Add other element types as needed
            }
            
            processed_xml = xml_str
            
            # Process each tag type
            for tag_name, pattern in patterns.items():
                def process_tag_content(match):
                    # Handle tags with attributes (like Url)
                    if tag_name == 'Url':
                        attributes = match.group(1)
                        content = match.group(2)
                        
                        # Check if content needs CDATA wrapping
                        if self._should_wrap_in_cdata(content):
                            return f'<Url{attributes}><![CDATA[{self._unescape_html(content)}]]></Url>'
                        return match.group(0)
                    else:
                        content = match.group(1)
                        
                        # Check if content needs CDATA wrapping
                        if self._should_wrap_in_cdata(content):
                            return f'<{tag_name}><![CDATA[{self._unescape_html(content)}]]></{tag_name}>'
                        return match.group(0)
                
                # Apply the processing for this tag type
                processed_xml = pattern.sub(process_tag_content, processed_xml)
            
            return processed_xml
            
        except Exception as e:
            logger.warning(f"HTML content processing failed: {e}. Returning original XML.")
            return xml_str
    
    def _should_wrap_in_cdata(self, content: str) -> bool:
        """
        Determine if content should be wrapped in CDATA.
        
        Returns True if content contains HTML tags or HTML entities.
        """
        # Check for HTML tags or entities
        return (('<' in content and '>' in content) or 
                ('&lt;' in content and '&gt;' in content) or
                ('&amp;' in content))
    
    def _unescape_html(self, content: str) -> str:
        """
        Unescape HTML entities in content.
        
        This converts &lt; to <, &gt; to >, etc.
        """
        if '&lt;' in content or '&gt;' in content or '&amp;' in content:
            return content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return content
    
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
        
        # First, check if content contains HTML entities that need to be unescaped
        if '&lt;' in content and '&gt;' in content:
            content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            
        # Pattern to match content with a single HTML tag pair
        pattern = re.compile(r'^<([a-zA-Z0-9]+)([^>]*)>(.*?)</\1>$', re.DOTALL)
        match = pattern.match(content.strip())
        
        if match:
            inner_content = match.group(3).strip()
            # If inner content has no HTML tags, it's simple
            return '<' not in inner_content
            
        return False
