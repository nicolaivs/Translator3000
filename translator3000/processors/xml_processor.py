"""
XML processing module for Translator3000 (Simplified Version).

This module handles XML file translation while preserving structure, attributes,
and CDATA sections with a focus on 100% structure preservation over speed.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from ..config import get_config

logger = logging.getLogger(__name__)


class XMLProcessor:
    """Handles XML file translation with maximum structure preservation."""
    
    def __init__(self, csv_processor):
        """
        Initialize XML processor with a CSV processor for text translation.
        
        Args:
            csv_processor: CSVProcessor instance for text translation logic
        """
        self.csv_processor = csv_processor
        self.config = get_config()
    
    def translate_xml(self, input_file: str, output_file: str, use_multithreading: bool = False, max_workers: int = None) -> tuple[bool, int]:
        """
        Translate text content in XML file while preserving structure and attributes.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            use_multithreading: Not used in this implementation, kept for API compatibility
            max_workers: Not used in this implementation, kept for API compatibility
            
        Returns:
            Tuple of (success, characters_translated)
        """
        # This implementation always uses sequential processing for reliability
        logger.info("Using simplified, sequential XML processing for maximum reliability")
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
                # Use our custom save method to ensure proper CDATA preservation
                self._save_xml_pretty(tree, output_file)
                return True, 0
            
            # Translate elements and apply changes
            success, chars_translated = self._translate_and_apply_sequential(text_elements)
            
            if not success:
                logger.error("XML translation failed")
                return False, 0
            
            # Save the translated XML with careful handling of CDATA and structure
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
        Alias for translate_xml_sequential - multithreading not supported in this version.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            max_workers: Not used in this implementation
            
        Returns:
            Tuple of (success, characters_translated)
        """
        logger.info("Multithreading not supported in simplified processor - using sequential processing")
        return self.translate_xml_sequential(input_file, output_file)

    def _collect_text_elements(self, element, text_elements: List):
        """
        Collect all text elements that need translation.
        
        This method carefully identifies elements with text content including:
        - Regular text elements
        - HTML content (with special handling)
        - URL elements (with structure preservation)
        """
        # First check if this element should be ignored
        if element.get('ignore', '').lower() == 'true':
            logger.debug(f"Skipping element marked with ignore=true: {element.tag}")
            return
            
        # Special handling for elements with CDATA that contain HTML
        if element.text and element.text.strip():
            # Get the element path to help identify specific elements
            element_path = self._get_element_path(element)
            element_tag_lower = element.tag.lower()
            
            # Special handling for URL elements - preserve the path structure
            if element_tag_lower == 'url':
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
                            # Skip normal text processing for URLs
                            return
                
                # If not a translatable URL format, just store it as-is without translation
                text_elements.append({
                    'element': element,
                    'type': 'skip',  # Mark to skip translation
                    'original': url_text,
                    'full_text': element.text,
                    'element_path': element_path,
                    'tag': element.tag
                })
                return  # Skip normal text processing for URLs
            
            # Check if this is likely HTML content (common in CDATA sections)
            is_html = False
            has_entities = False
            has_cdata = False
            
            # Check for CDATA sections
            if '<![CDATA[' in element.text:
                has_cdata = True
                # Extract content from CDATA to check for HTML
                cdata_content = self._extract_cdata_content(element.text)
                if cdata_content and ('<' in cdata_content and '>' in cdata_content):
                    is_html = True
            
            # Check for raw HTML tags
            if '<' in element.text and '>' in element.text:
                is_html = True
            
            # Check for escaped HTML entities
            if '&lt;' in element.text and '&gt;' in element.text:
                is_html = True
                has_entities = True
            
            # Special handling for common HTML container elements
            # These elements need special CDATA handling in output
            is_special_element = element_tag_lower in ('content', 'description', 'title', 'banner')
            
            # For special elements or HTML content, use specialized handling
            if is_html or is_special_element:
                # Store the element with special type for HTML/CDATA handling
                text_elements.append({
                    'element': element,
                    'type': 'html_content',  # Special marker for HTML content
                    'original': element.text.strip(),
                    'full_text': element.text,
                    'element_path': element_path,  # Store element path for context
                    'tag': element.tag,  # Store the element tag
                    'is_special_element': is_special_element,  # Flag for CDATA-needing element
                    'is_simple_html': self._is_simple_html_content(element.text.strip()),  # Flag for simple HTML
                    'has_entities': has_entities,  # Track if it contains HTML entities
                    'has_cdata': has_cdata,  # Track if it contains CDATA sections
                    'original_cdata': self._was_in_cdata(element.text)  # Track original CDATA state
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
            
    def _extract_cdata_content(self, text: str) -> str:
        """
        Extract content from CDATA section.
        
        Args:
            text: Text that may contain CDATA sections
            
        Returns:
            Content within CDATA section, or original text if no CDATA found
        """
        if '<![CDATA[' in text and ']]>' in text:
            try:
                start = text.find('<![CDATA[') + 9
                end = text.rfind(']]>')
                if start > 9 and end > start:
                    return text[start:end]
            except:
                pass
        return text

    def _translate_and_apply_sequential(self, text_elements: List) -> Tuple[bool, int]:
        """
        Translate XML text elements sequentially and apply translations directly.
        
        This method ensures each element is processed completely before moving to the next,
        maintaining the highest level of structural integrity.
        """
        try:
            total_elements = len(text_elements)
            total_characters = 0
            
            # Process each element one at a time
            for idx, text_data in enumerate(text_elements):
                if (idx + 1) % self.config['progress_interval'] == 0 or (idx + 1) == total_elements:
                    logger.info(f"Progress: {idx + 1}/{total_elements} elements processed")
                
                original_text = text_data['original']
                element_type = text_data['type']
                element = text_data['element']
                
                # Skip elements marked for no translation
                if element_type == 'skip':
                    continue
                
                # Count characters for non-skipped elements
                total_characters += len(original_text)
                
                # Get element context
                element_path = text_data.get('element_path', '')
                tag = text_data.get('tag', '')
                
                # Perform translation based on element type
                translated = None
                
                if element_type == 'html_content':
                    # Handle HTML content with special processing
                    translated = self._translate_html_content(
                        original_text, 
                        element_path, 
                        tag,
                        has_entities=text_data.get('has_entities', False)
                    )
                elif element_type == 'special_text':
                    # Handle special elements with plain text content
                    translated = self.csv_processor.translate_text(original_text)
                elif element_type == 'url':
                    # Special handling for URLs to preserve path structure
                    translated_path = self.csv_processor.translate_text(original_text)
                    prefix = text_data.get('prefix', '/')
                    translated = f"{prefix}{translated_path}"
                elif element_type in ('text', 'tail'):
                    # Regular text translation
                    translated = self.csv_processor.translate_text(original_text)
                
                # Apply the translation based on element type
                if translated:
                    if element_type in ('html_content', 'special_text'):
                        # Preserve whitespace in HTML content and special elements
                        if text_data['full_text'].startswith(' ') or text_data['full_text'].startswith('\n'):
                            # Find and preserve leading whitespace
                            leading_whitespace = ''
                            for char in text_data['full_text']:
                                if char in [' ', '\n', '\t']:
                                    leading_whitespace += char
                                else:
                                    break
                            element.text = leading_whitespace + translated
                        else:
                            element.text = translated
                    elif element_type == 'url':
                        # Direct replacement for URLs
                        element.text = translated
                    elif element_type == 'text':
                        # Replace element text while preserving whitespace
                        if element.text.startswith(' ') or element.text.startswith('\n'):
                            # Replace only the content part
                            element.text = element.text.replace(original_text, translated)
                        else:
                            element.text = translated
                    elif element_type == 'tail':
                        # Replace tail text while preserving whitespace
                        if element.tail.startswith(' ') or element.tail.startswith('\n'):
                            element.tail = element.tail.replace(original_text, translated)
                        else:
                            element.tail = translated
   
            logger.info(f"Sequential XML translation completed")
            return True, total_characters
            
        except Exception as e:
            logger.error(f"Sequential XML translation failed: {e}")
            return False, 0
    
    def _translate_html_content(self, html_content: str, element_path: str = None, tag: str = None, has_entities: bool = False) -> str:
        """
        Translate HTML content while carefully preserving the structure.
        
        This method preserves HTML tags and only translates the text content.
        
        Args:
            html_content: The HTML content to translate
            element_path: The XML path to the element (for context)
            tag: The element tag (for context)
            has_entities: Whether the content contains HTML entities
        """
        try:
            import re  # Import re at the beginning of the method to ensure it's available everywhere
            
            # Ensure we're working with a string
            if not isinstance(html_content, str):
                html_content = str(html_content)
                
            # Normalize line endings
            html_content = html_content.replace('\r\n', '\n')
            
            # Check for CDATA sections and extract content
            has_cdata = False
            cdata_content = None
            if '<![CDATA[' in html_content and ']]>' in html_content:
                has_cdata = True
                cdata_content = self._extract_cdata_content(html_content)
                if cdata_content:
                    # Process the content within CDATA
                    html_content = cdata_content
            
            # First, check if HTML content is escaped and unescape it for processing
            unescaped_content = html_content
            if has_entities or ('&lt;' in html_content and '&gt;' in html_content):
                unescaped_content = html_content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                logger.debug(f"Unescaped HTML content for translation: {unescaped_content[:50]}...")
            
            # Special case for simple HTML tags like <h1>Text</h1>
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
                        translated_content = self._translate_html_content(content, element_path, tag_name, has_entities)
                        result = f"<{tag_name}{tag_attrs}>{translated_content}</{tag_name}>"
                    else:
                        # It's simple text, translate directly
                        translated = self.csv_processor.translate_text(content)
                        result = f"<{tag_name}{tag_attrs}>{translated}</{tag_name}>"
                        
                    # Wrap back in CDATA if needed
                    if has_cdata:
                        return f"<![CDATA[{result}]]>"
                    
                    # Only re-escape if original content had entities and wasn't in CDATA
                    if has_entities and not has_cdata:
                        result = result.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
                    
                    return result
            
            # Check if we have multiple paragraphs - this is a special case that needs separate handling
            if '<p' in unescaped_content or '</p>' in unescaped_content:
                # Process paragraphs separately to ensure each is translated
                # Note: 're' is already imported at the beginning of the method
                
                # Pattern to match paragraphs with or without attributes
                p_pattern = re.compile(r'(<p\s*[^>]*>)(.*?)(</p>)', re.DOTALL)
                
                def translate_paragraph(match):
                    p_tag_start = match.group(1)  # Opening <p> tag with attributes
                    p_content = match.group(2)    # Content between the tags
                    p_tag_end = match.group(3)    # Closing </p> tag
                    
                    # Only translate if there's content
                    if p_content and p_content.strip():
                        # Check if paragraph content has nested HTML
                        if '<' in p_content and '>' in p_content and not p_content.startswith('<'):
                            # Has nested HTML, process recursively
                            translated_content = self._translate_html_content(p_content, element_path, 'p', has_entities)
                            return f"{p_tag_start}{translated_content}{p_tag_end}"
                        else:
                            # Simple text paragraph, translate directly
                            translated = self.csv_processor.translate_text(p_content.strip())
                            
                            # Preserve whitespace around the content
                            if p_content.startswith(' '):
                                translated = ' ' + translated
                            if p_content.endswith(' '):
                                translated = translated + ' '
                                
                            return f"{p_tag_start}{translated}{p_tag_end}"
                    
                    # Empty paragraph, return as is
                    return match.group(0)
                
                # Process all paragraphs in the HTML content
                processed_content = p_pattern.sub(translate_paragraph, unescaped_content)
                
                # Wrap back in CDATA if needed
                if has_cdata:
                    return f"<![CDATA[{processed_content}]]>"
                
                # If the original had HTML entities and wasn't in CDATA, re-escape HTML
                if has_entities and not has_cdata:
                    processed_content = processed_content.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
                
                return processed_content
            
            # For non-HTML content or simple text in Title, Description, etc.
            if not ('<' in unescaped_content and '>' in unescaped_content) or tag.lower() in ('title', 'description', 'banner'):
                # Just translate the text content directly
                translated = self.csv_processor.translate_text(unescaped_content.strip())
                
                # Wrap back in CDATA if needed
                if has_cdata:
                    return f"<![CDATA[{translated}]]>"
                
                return translated
            
            # For more complex HTML, use a pattern that handles HTML tags and content between them
            pattern = re.compile(r'(<[^>]+>)([^<]*)(?=<|$)', re.DOTALL)
            
            def translate_match(match):
                html_tag = match.group(1)  # The HTML tag
                content = match.group(2)  # The text content
                
                # Only translate non-empty content
                if content and content.strip():
                    # Translate the content
                    translated = self.csv_processor.translate_text(content.strip())
                    
                    # Preserve whitespace structure
                    if content.startswith(' '):
                        return html_tag + ' ' + translated + content[len(content.strip())+1:]
                    elif content.endswith(' '):
                        return html_tag + translated + ' '
                    else:
                        return html_tag + translated
                
                return html_tag + content  # Keep empty content unchanged
            
            # Apply the translation to all matches
            result = pattern.sub(translate_match, unescaped_content)
            
            # Wrap back in CDATA if needed
            if has_cdata:
                return f"<![CDATA[{result}]]>"
            
            # Important: if the original content had HTML entities, we need to keep the result in 
            # the same format for consistency - this avoids mixups with raw HTML
            if has_entities and not has_cdata:
                # Re-escape any raw HTML tags that might be in the result
                result = result.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            
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
            # The \s* allows for whitespace around the tag content
            patterns = {
                'Content': re.compile(r'<Content\s*>(.*?)</Content\s*>', re.DOTALL),
                'Title': re.compile(r'<Title\s*>(.*?)</Title\s*>', re.DOTALL),
                'Description': re.compile(r'<Description\s*>(.*?)</Description\s*>', re.DOTALL),
                'Url': re.compile(r'<Url\s*([^>]*)>(.*?)</Url\s*>', re.DOTALL),
                'Banner': re.compile(r'<Banner\s*>(.*?)</Banner\s*>', re.DOTALL),
                'Teaser': re.compile(r'<Teaser\s*>(.*?)</Teaser\s*>', re.DOTALL),
                # Add more HTML-containing elements here as needed
                'Summary': re.compile(r'<Summary\s*>(.*?)</Summary\s*>', re.DOTALL),
                'Body': re.compile(r'<Body\s*>(.*?)</Body\s*>', re.DOTALL),
                'Introduction': re.compile(r'<Introduction\s*>(.*?)</Introduction\s*>', re.DOTALL),
                'Conclusion': re.compile(r'<Conclusion\s*>(.*?)</Conclusion\s*>', re.DOTALL),
                'Text': re.compile(r'<Text\s*>(.*?)</Text\s*>', re.DOTALL),
                'HTML': re.compile(r'<HTML\s*>(.*?)</HTML\s*>', re.DOTALL)
            }
            
            processed_xml = xml_str
            
            # Process each tag type
            for tag_name, pattern in patterns.items():
                def process_tag_content(match):
                    # Handle tags with attributes (like Url)
                    if tag_name == 'Url':
                        attributes = match.group(1)
                        content = match.group(2)
                        
                        # Already has CDATA, leave it as is
                        if '<![CDATA[' in content and ']]>' in content:
                            return match.group(0)
                        
                        # Check if content needs CDATA wrapping
                        if self._should_wrap_in_cdata(content):
                            # Only unescape if it contains HTML entities
                            if '&lt;' in content or '&gt;' in content:
                                unescaped = self._unescape_html(content)
                                return f'<Url{attributes}><![CDATA[{unescaped}]]></Url>'
                            else:
                                # Content has raw HTML tags, wrap directly in CDATA
                                return f'<Url{attributes}><![CDATA[{content}]]></Url>'
                        return match.group(0)
                    else:
                        content = match.group(1)
                        
                        # Already has CDATA, leave it as is
                        if '<![CDATA[' in content and ']]>' in content:
                            return match.group(0)
                        
                        # Check if content needs CDATA wrapping (either has HTML or had CDATA originally)
                        # Always wrap HTML content in CDATA to ensure proper XML format
                        if self._should_wrap_in_cdata(content):
                            # Only unescape if it contains HTML entities
                            if '&lt;' in content or '&gt;' in content:
                                unescaped = self._unescape_html(content)
                                return f'<{tag_name}><![CDATA[{unescaped}]]></{tag_name}>'
                            else:
                                # Content has raw HTML tags, wrap directly in CDATA
                                return f'<{tag_name}><![CDATA[{content}]]></{tag_name}>'
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
        
        Returns True if content contains HTML tags, HTML entities, or any characters
        that might need escaping in XML.
        """
        # Check for HTML tags or entities
        if (('<' in content and '>' in content) or 
                ('&lt;' in content and '&gt;' in content) or
                ('&amp;' in content)):
            return True
            
        # Check for other characters that might need CDATA protection
        xml_special_chars = ['&', '<', '>', '"', "'"]
        for char in xml_special_chars:
            if char in content:
                return True
                
        return False
   
    def _unescape_html(self, content: str) -> str:
        """
        Unescape HTML entities in content.
        
        This converts &lt; to <, &gt; to >, etc.
        """
        if '&lt;' in content or '&gt;' in content or '&amp;' in content:
            return content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return content
    
    def _was_in_cdata(self, content: str) -> bool:
        """
        Check if content was likely originally in a CDATA section.
        
        This helps preserve the original structure of the XML.
        """
        # Look for common patterns in CDATA sections
        if '<![CDATA[' in content:
            return True
        # If it contains raw HTML tags (not entity-escaped), it was likely in CDATA
        if '<' in content and '>' in content and '&lt;' not in content:
            return True
        return False
    
    def _get_element_path(self, element):
        """Generate a path string to identify the element in the XML tree."""
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
