"""
XML processing module for Translator3000 with robust HTML handling.

This module handles XML file translation while preserving structure, attributes,
and CDATA sections with a focus on 100% structure preservation and robust HTML handling.
Uses BeautifulSoup for HTML content parsing and translation.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag, CData
import html

from ..config import get_config

logger = logging.getLogger(__name__)


class XMLProcessor:
    """Handles XML file translation with BeautifulSoup for robust HTML processing."""
    
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
        logger.info("Using BeautifulSoup-based XML processing for maximum HTML compatibility")
        return self.translate_xml_sequential(input_file, output_file)

    def translate_xml_sequential(self, input_file: str, output_file: str) -> tuple[bool, int]:
        """
        Translate text content in XML file sequentially using BeautifulSoup for HTML.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            
        Returns:
            Tuple of (success, characters_translated)
        """
        try:
            logger.info(f"Reading XML file: {input_file}")
            
            # Read the raw XML content first to preserve CDATA and structure
            with open(input_file, 'r', encoding='utf-8') as f:
                raw_xml_content = f.read()
            
            # Parse the XML file
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Collect all text elements that need translation
            text_elements = []
            self._collect_text_elements(root, text_elements, raw_xml_content)
            
            total_elements = len(text_elements)
            logger.info(f"Found {total_elements} text elements to translate")
            
            if total_elements == 0:
                # No text to translate, just copy the file
                logger.info("No text elements found, copying file as-is")
                self._save_xml_with_structure_preservation(tree, output_file, raw_xml_content)
                return True, 0
            
            # Translate elements and apply changes
            success, chars_translated = self._translate_and_apply_robust(text_elements)
            
            if not success:
                logger.error("XML translation failed")
                return False, 0
            
            # Save the translated XML with structure preservation
            logger.info(f"Saving translated XML to: {output_file}")
            self._save_xml_with_structure_preservation(tree, output_file, raw_xml_content)
            
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
        logger.info("Using sequential processing for maximum reliability")
        return self.translate_xml_sequential(input_file, output_file)

    def _collect_text_elements(self, element, text_elements: List, raw_xml: str):
        """
        Collect all text elements that need translation with robust structure detection.
        """
        # Check if this element should be ignored (case-insensitive)
        ignore_value = element.get('ignore', '') or element.get('Ignore', '')
        if ignore_value.lower() == 'true':
            logger.debug(f"Skipping element marked with ignore=true: {element.tag}")
            return
            
        # Process element text content
        if element.text and element.text.strip():
            element_path = self._get_element_path(element)
            element_tag_lower = element.tag.lower()
            
            # Special handling for URL elements
            if element_tag_lower == 'url':
                self._handle_url_element(element, text_elements, element_path)
            else:
                # Determine content type and collect for translation
                content_info = self._analyze_content_type(element.text, element_tag_lower, raw_xml)
                text_elements.append({
                    'element': element,
                    'type': 'text',
                    'original': element.text.strip(),
                    'full_text': element.text,
                    'element_path': element_path,
                    'tag': element.tag,
                    'content_info': content_info
                })
        
        # Process tail text
        if element.tail and element.tail.strip():
            element_path = self._get_element_path(element)
            text_elements.append({
                'element': element,
                'type': 'tail',
                'original': element.tail.strip(),
                'full_text': element.tail,
                'element_path': element_path,
                'tag': element.tag,
                'content_info': {'type': 'plain_text'}
            })
        
        # Process children recursively
        for child in element:
            self._collect_text_elements(child, text_elements, raw_xml)

    def _handle_url_element(self, element, text_elements: List, element_path: str):
        """Handle URL elements with special path structure preservation."""
        url_text = element.text.strip()
        if url_text.startswith('/'):
            parts = url_text.split('/')
            if len(parts) > 2:
                lang_code = parts[1].lower()
                if lang_code in ('en', 'de', 'fr', 'es', 'it', 'da', 'sv', 'nb', 'nl'):
                    text_elements.append({
                        'element': element,
                        'type': 'url',
                        'original': '/'.join(parts[2:]),
                        'full_text': element.text,
                        'element_path': element_path,
                        'tag': element.tag,
                        'prefix': f'/{lang_code}/',
                        'content_info': {'type': 'url_path'}
                    })
                    return
        
        # If not a translatable URL format, mark as skip
        text_elements.append({
            'element': element,
            'type': 'skip',
            'original': url_text,
            'full_text': element.text,
            'element_path': element_path,
            'tag': element.tag,
            'content_info': {'type': 'skip'}
        })

    def _analyze_content_type(self, content: str, element_tag: str, raw_xml: str) -> Dict[str, Any]:
        """
        Analyze content to determine the best translation strategy.
        
        Returns detailed information about content type and structure.
        """
        import re  # Import re for regex operations
        
        content_info = {
            'type': 'plain_text',
            'has_html': False,
            'has_cdata': False,
            'has_entities': False,
            'is_complex': False,
            'needs_soup': False,
            'was_originally_cdata': False  # Track if this was originally in CDATA
        }
        
        # Check if this element was originally wrapped in CDATA by looking at the raw XML
        element_pattern = f'<{element_tag}[^>]*>.*?</{element_tag}>'
        element_matches = re.findall(element_pattern, raw_xml, re.DOTALL | re.IGNORECASE)
        for match in element_matches:
            if '<![CDATA[' in match and ']]>' in match:
                content_info['was_originally_cdata'] = True
                break
        
        # Check for CDATA sections in current content
        if '<![CDATA[' in content and ']]>' in content:
            content_info['has_cdata'] = True
            content_info['type'] = 'cdata_content'
            # Extract CDATA content for further analysis
            cdata_content = self._extract_cdata_content(content)
            if cdata_content and ('<' in cdata_content and '>' in cdata_content):
                content_info['has_html'] = True
                content_info['needs_soup'] = True
                content_info['type'] = 'cdata_html'
        
        # Check for escaped HTML entities
        elif '&lt;' in content and '&gt;' in content:
            content_info['has_entities'] = True
            content_info['has_html'] = True
            content_info['needs_soup'] = True
            content_info['type'] = 'escaped_html'
            # If this was originally CDATA, mark it as such
            if content_info['was_originally_cdata']:
                content_info['has_cdata'] = True
                content_info['type'] = 'cdata_html'
        
        # Check for raw HTML tags
        elif '<' in content and '>' in content:
            content_info['has_html'] = True
            content_info['needs_soup'] = True
            content_info['type'] = 'raw_html'
            # If this was originally CDATA, mark it as such
            if content_info['was_originally_cdata']:
                content_info['has_cdata'] = True
                content_info['type'] = 'cdata_html'
        
        # If content was originally in CDATA but doesn't have HTML tags now,
        # it might still need CDATA wrapping for special characters
        elif content_info['was_originally_cdata']:
            content_info['has_cdata'] = True
            content_info['needs_soup'] = True
        
        # Check complexity for HTML content
        if content_info['has_html']:
            # Count nested tags to determine complexity
            tag_count = content.count('<') + content.count('&lt;')
            if tag_count > 4:  # More than 2 tag pairs
                content_info['is_complex'] = True
        
        # Special elements that often contain HTML
        html_elements = [
            'content', 'description', 'title', 'banner', 'summary', 'body', 'text',
            'teaser', 'introduction', 'conclusion', 'excerpt', 'abstract',
            'details', 'info', 'note', 'comment', 'message', 'html'
        ]
        
        if element_tag.lower() in html_elements:
            content_info['is_special_element'] = True
            if content_info['has_html'] or content_info['was_originally_cdata']:
                content_info['needs_soup'] = True
                content_info['has_cdata'] = True
        
        return content_info

    def _translate_and_apply_robust(self, text_elements: List) -> Tuple[bool, int]:
        """
        Translate XML text elements using BeautifulSoup for HTML content.
        """
        try:
            total_elements = len(text_elements)
            total_characters = 0
            
            for idx, text_data in enumerate(text_elements):
                if (idx + 1) % self.config['progress_interval'] == 0 or (idx + 1) == total_elements:
                    logger.info(f"Progress: {idx + 1}/{total_elements} elements processed")
                
                original_text = text_data['original']
                element_type = text_data['type']
                element = text_data['element']
                content_info = text_data.get('content_info', {})
                
                # Skip elements marked for no translation
                if element_type == 'skip':
                    continue
                
                # Count characters for non-skipped elements
                total_characters += len(original_text)
                
                # Perform translation based on content type
                translated = self._translate_content_robust(
                    original_text, 
                    content_info, 
                    text_data.get('element_path', ''),
                    text_data.get('tag', '')
                )
                
                # Apply translation to element
                if translated and translated != original_text:
                    self._apply_translation_to_element(text_data, translated)
   
            logger.info(f"Robust XML translation completed")
            return True, total_characters
            
        except Exception as e:
            logger.error(f"Robust XML translation failed: {e}")
            return False, 0

    def _translate_content_robust(self, content: str, content_info: Dict, element_path: str, tag: str) -> str:
        """
        Translate content using the most appropriate method based on content analysis.
        """
        try:
            content_type = content_info.get('type', 'plain_text')
            
            if content_type == 'plain_text':
                return self.csv_processor.translate_text(content.strip())
            
            elif content_type == 'url_path':
                return self.csv_processor.translate_text(content.strip())
            
            elif content_info.get('needs_soup', False):
                return self._translate_html_with_soup(content, content_info)
            
            else:
                # Fallback to simple translation
                return self.csv_processor.translate_text(content.strip())
                
        except Exception as e:
            logger.warning(f"Content translation failed for {element_path}: {e}")
            return content

    def _translate_html_with_soup(self, html_content: str, content_info: Dict) -> str:
        """
        Translate HTML content using BeautifulSoup for robust parsing and structure preservation.
        """
        try:
            # Prepare content based on type
            if content_info.get('has_cdata'):
                # Extract content from CDATA
                working_content = self._extract_cdata_content(html_content)
                should_wrap_cdata = True
            elif content_info.get('has_entities'):
                # Unescape HTML entities
                working_content = html.unescape(html_content)
                should_wrap_cdata = False
            else:
                working_content = html_content
                should_wrap_cdata = False
            
            # Remove leading/trailing whitespace but preserve structure
            working_content = working_content.strip()
            
            # Handle simple single-tag content
            if self._is_simple_single_tag(working_content):
                return self._translate_simple_html(working_content, content_info)
            
            # Use BeautifulSoup for complex HTML
            try:
                # Parse HTML with BeautifulSoup - force HTML parsing
                soup = BeautifulSoup(working_content, 'html.parser')
                
                # Translate all text nodes while preserving structure
                self._translate_soup_text_nodes(soup)
                
                # Get the translated HTML
                translated_html = str(soup)
                
                # Clean up BeautifulSoup artifacts
                translated_html = self._clean_soup_output(translated_html, working_content)
                
                # IMPORTANT: For CDATA content, we return the raw HTML without CDATA wrapping
                # The CDATA wrapping will be handled during the final XML saving phase
                # This prevents double-escaping issues
                if should_wrap_cdata:
                    # Don't wrap in CDATA here - let the XML saving process handle it
                    return translated_html
                elif content_info.get('has_entities'):
                    # Re-escape for XML if original had entities
                    return html.escape(translated_html)
                else:
                    return translated_html
                    
            except Exception as soup_error:
                logger.warning(f"BeautifulSoup parsing failed: {soup_error}, falling back to regex")
                return self._translate_html_fallback(working_content, content_info)
                
        except Exception as e:
            logger.warning(f"HTML translation failed: {e}")
            return html_content

    def _translate_soup_text_nodes(self, soup):
        """
        Recursively translate all text nodes in a BeautifulSoup object while preserving structure.
        """
        for element in soup.descendants:
            if isinstance(element, NavigableString) and not isinstance(element, CData):
                text_content = element.string.strip()
                if text_content and len(text_content) > 1:  # Only translate meaningful text
                    # Check if this text node or any parent has ignore attribute
                    should_ignore = False
                    current = element.parent
                    
                    while current and isinstance(current, Tag):
                        # Check for ignore attribute (case-insensitive)
                        ignore_value = current.get('ignore', '') or current.get('Ignore', '')
                        if ignore_value.lower() == 'true':
                            should_ignore = True
                            break
                        current = current.parent
                    
                    if should_ignore:
                        logger.debug(f"Skipping translation due to ignore attribute: {text_content[:50]}")
                        continue  # Skip translation for ignored elements
                    
                    # Translate the text
                    try:
                        translated = self.csv_processor.translate_text(text_content)
                        if translated and translated != text_content:
                            # Preserve surrounding whitespace
                            original = element.string
                            leading_space = ''
                            trailing_space = ''
                            
                            # Extract leading whitespace
                            for char in original:
                                if char.isspace():
                                    leading_space += char
                                else:
                                    break
                            
                            # Extract trailing whitespace
                            for char in reversed(original):
                                if char.isspace():
                                    trailing_space = char + trailing_space
                                else:
                                    break
                            
                            # Replace with translated text preserving whitespace
                            element.replace_with(leading_space + translated + trailing_space)
                    except Exception as e:
                        logger.warning(f"Failed to translate text node: {e}")

    def _is_simple_single_tag(self, content: str) -> bool:
        """Check if content is a simple single HTML tag."""
        content = content.strip()
        if not content.startswith('<') or not content.endswith('>'):
            return False
        
        # Count opening and closing tags
        open_tags = content.count('<') - content.count('</')
        close_tags = content.count('</')
        
        # Simple single tag: one opening tag, one closing tag
        return open_tags == 1 and close_tags == 1

    def _translate_simple_html(self, content: str, content_info: Dict) -> str:
        """Translate simple HTML content with a single tag pair."""
        import re
        
        pattern = re.compile(r'^(<[^>]+>)(.*?)(<\/[^>]+>)$', re.DOTALL)
        match = pattern.match(content.strip())
        
        if match:
            opening_tag = match.group(1)
            inner_content = match.group(2).strip()
            closing_tag = match.group(3)
            
            if inner_content:
                translated = self.csv_processor.translate_text(inner_content)
                result = f"{opening_tag}{translated}{closing_tag}"
                
                # Don't wrap in CDATA here - let the XML saving process handle it
                if content_info.get('has_entities'):
                    return html.escape(result)
                else:
                    return result
        
        return content

    def _translate_html_fallback(self, content: str, content_info: Dict) -> str:
        """Fallback HTML translation using regex when BeautifulSoup fails."""
        import re
        
        # Enhanced pattern to match complete tag structures with content
        def should_translate_tag_content(preceding_tag):
            """Check if content within a tag should be translated."""
            # Look for ignore attribute in the preceding tag (case-insensitive)
            if ('ignore="true"' in preceding_tag.lower() or "ignore='true'" in preceding_tag.lower() or
                'Ignore="True"' in preceding_tag or "Ignore='True'" in preceding_tag):
                return False
            return True
        
        # Pattern to match tag followed by text content
        pattern = re.compile(r'(<[^>]*>)([^<]*)', re.DOTALL)
        
        def translate_match(match):
            html_tag = match.group(1)  # The HTML tag
            text_content = match.group(2)  # The text content
            
            # Check if the tag has ignore attribute
            if not should_translate_tag_content(html_tag):
                return match.group(0)  # Don't translate ignored content
            
            # Only translate non-empty content
            if text_content and text_content.strip():
                translated = self.csv_processor.translate_text(text_content.strip())
                # Preserve whitespace structure
                if text_content.startswith(' '):
                    return html_tag + ' ' + translated + text_content[len(text_content.strip())+1:]
                elif text_content.endswith(' '):
                    return html_tag + translated + ' '
                else:
                    return html_tag + translated
            
            return match.group(0)  # Keep empty content unchanged
        
        result = pattern.sub(translate_match, content)
        
        # Don't wrap in CDATA here - let the XML saving process handle it
        if content_info.get('has_entities'):
            return html.escape(result)
        else:
            return result

    def _clean_soup_output(self, soup_output: str, original_content: str) -> str:
        """Clean BeautifulSoup output to match original formatting and preserve raw HTML."""
        # Remove unwanted HTML tags that BeautifulSoup might add
        if not original_content.startswith('<html>') and soup_output.startswith('<html>'):
            soup_output = soup_output.replace('<html><body>', '').replace('</body></html>', '')
        
        # Remove extra html and body tags that BeautifulSoup adds
        if soup_output.startswith('<html>'):
            soup_output = soup_output.replace('<html>', '').replace('</html>', '')
        if soup_output.startswith('<body>'):
            soup_output = soup_output.replace('<body>', '').replace('</body>', '')
        
        # Preserve original line endings and whitespace structure where possible
        if '\n' in original_content and '\n' not in soup_output:
            # Try to preserve line breaks in a simple way
            soup_output = soup_output.replace('><', '>\n<')
        
        # Ensure we don't have HTML entity escaping in the output
        # BeautifulSoup should output raw HTML, not escaped HTML
        return soup_output.strip()

    def _apply_translation_to_element(self, text_data: Dict, translated: str):
        """Apply translation to the XML element preserving whitespace structure and CDATA."""
        element_type = text_data['type']
        element = text_data['element']
        original_text = text_data['original']
        full_text = text_data['full_text']
        content_info = text_data.get('content_info', {})
        
        if element_type == 'url':
            # Handle URL with prefix
            prefix = text_data.get('prefix', '/')
            element.text = f"{prefix}{translated}"
        elif element_type == 'text':
            # For CDATA content, we need to preserve it as CDATA in the final output
            if content_info.get('has_cdata', False):
                # The translated content should already be wrapped in CDATA if needed
                # Just set it directly - the _ensure_proper_cdata_wrapping will handle it
                element.text = translated
            else:
                # Preserve whitespace structure for regular text
                if full_text.startswith(' ') or full_text.startswith('\n'):
                    # Find leading whitespace
                    leading_ws = ''
                    for char in full_text:
                        if char.isspace():
                            leading_ws += char
                        else:
                            break
                    element.text = leading_ws + translated
                else:
                    element.text = translated
        elif element_type == 'tail':
            # Replace tail text preserving whitespace
            if full_text.startswith(' ') or full_text.startswith('\n'):
                element.tail = full_text.replace(original_text, translated)
            else:
                element.tail = translated

    def _extract_cdata_content(self, text: str) -> str:
        """Extract content from CDATA section."""
        if '<![CDATA[' in text and ']]>' in text:
            try:
                start = text.find('<![CDATA[') + 9
                end = text.rfind(']]>')
                if start > 9 and end > start:
                    return text[start:end]
            except:
                pass
        return text

    def _save_xml_with_structure_preservation(self, tree, output_file: str, original_raw_xml: str):
        """
        Save XML with maximum structure preservation including CDATA, formatting, and encoding.
        """
        try:
            # Generate the new XML content
            xml_string = ET.tostring(tree.getroot(), encoding='utf-8', method='xml').decode('utf-8')
            
            # Process and wrap HTML content in CDATA where appropriate
            processed_xml = self._ensure_proper_cdata_wrapping(xml_string, original_raw_xml)
            
            # Pretty print the XML
            try:
                dom = minidom.parseString(f'<?xml version="1.0" encoding="utf-8"?>\n{processed_xml}')
                pretty_xml = dom.toprettyxml(indent='    ', encoding='utf-8').decode('utf-8')
                
                # Fix HTML entity escaping inside CDATA sections
                # minidom incorrectly escapes & to &amp; even inside CDATA
                pretty_xml = self._fix_cdata_escaping(pretty_xml)
                
                # Clean up excessive whitespace from minidom
                lines = []
                for line in pretty_xml.split('\n'):
                    if line.strip():
                        lines.append(line)
                
                # Write to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                    f.write('\n')
                    
            except Exception as pretty_error:
                logger.warning(f"Pretty printing failed: {pretty_error}")
                # Fallback to direct write
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                    f.write(processed_xml)
        
        except Exception as e:
            logger.error(f"XML saving failed: {e}")
            # Last resort fallback
            tree.write(output_file, encoding='utf-8', xml_declaration=True)

    def _fix_cdata_escaping(self, xml_content: str) -> str:
        """
        Fix HTML entity escaping that occurs inside CDATA sections.
        minidom incorrectly escapes & to &amp; even inside CDATA.
        """
        import re
        
        # Pattern to match CDATA sections
        cdata_pattern = re.compile(r'<!\[CDATA\[(.*?)\]\]>', re.DOTALL)
        
        def fix_cdata_content(match):
            cdata_content = match.group(1)
            # Unescape HTML entities that were incorrectly escaped by minidom
            fixed_content = cdata_content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            return f'<![CDATA[{fixed_content}]]>'
        
        return cdata_pattern.sub(fix_cdata_content, xml_content)

    def _ensure_proper_cdata_wrapping(self, xml_string: str, original_xml: str) -> str:
        """
        Ensure HTML content is properly wrapped in CDATA sections based on original structure.
        Never add CDATA to empty or whitespace-only content.
        """
        import re
        
        # Tags that typically contain HTML and should be wrapped in CDATA
        # Include ALL possible HTML-containing elements
        html_tags = [
            'Content', 'Description', 'Title', 'Banner', 'Summary', 'Body', 'Text',
            'Teaser', 'Introduction', 'Conclusion', 'Excerpt', 'Abstract',
            'Details', 'Info', 'Note', 'Comment', 'Message', 'HTML', 'Image', 'URL'
        ]
        
        for tag in html_tags:
            # CRITICAL: Skip self-closing tags completely to prevent malformed XML
            # First, check for and skip self-closing tags
            self_closing_pattern = re.compile(f'<{tag}([^>]*?)/>', re.IGNORECASE)
            if self_closing_pattern.search(xml_string):
                # Self-closing tags found, skip processing for this tag entirely
                # They are already correctly formatted and don't need CDATA
                continue
            
            # Case-insensitive pattern matching - only match opening/closing tag pairs
            pattern = re.compile(f'<{tag}([^>]*?)>(.*?)</{tag}\\s*>', re.DOTALL | re.IGNORECASE)
            
            def wrap_if_needed(match):
                attributes = match.group(1)
                content = match.group(2)
                
                # CRITICAL: Never add CDATA to empty or whitespace-only content
                # This prevents illegal XML for empty/self-closing elements
                if not content or not content.strip():
                    # If content is empty, remove any existing CDATA as well
                    if '<![CDATA[' in content and ']]>' in content:
                        # Extract just the content between CDATA tags
                        cdata_content = self._extract_cdata_content(content)
                        if not cdata_content or not cdata_content.strip():
                            # Empty CDATA content, return element without CDATA
                            return f'<{tag}{attributes}></{tag}>'
                    return match.group(0)
                
                # Check if element has ignore attribute (case-insensitive)
                if ('ignore="true"' in attributes.lower() or "ignore='true'" in attributes.lower() or
                    'Ignore="True"' in attributes or "Ignore='True'" in attributes):
                    # For ignored elements, preserve CDATA exactly as is, but drop if empty
                    if '<![CDATA[' in content and ']]>' in content:
                        cdata_content = self._extract_cdata_content(content)
                        if not cdata_content or not cdata_content.strip():
                            # Drop empty CDATA for ignored elements too
                            return f'<{tag}{attributes}></{tag}>'
                        return match.group(0)  # Keep existing CDATA if not empty
                    else:
                        # If original had CDATA but content is not empty, restore it
                        original_pattern = f'<{tag}[^>]*>.*?</{tag}\\s*>'
                        original_matches = re.findall(original_pattern, original_xml, re.DOTALL | re.IGNORECASE)
                        for orig_match in original_matches:
                            if attributes.strip() in orig_match and '<![CDATA[' in orig_match:
                                if content.strip():  # Only restore if content is not empty
                                    return f'<{tag}{attributes}><![CDATA[{content}]]></{tag}>'
                    return match.group(0)
                
                # Skip if already has CDATA (but check if it's empty CDATA)
                if '<![CDATA[' in content:
                    cdata_content = self._extract_cdata_content(content)
                    if not cdata_content or not cdata_content.strip():
                        # Drop empty CDATA
                        return f'<{tag}{attributes}></{tag}>'
                    return match.group(0)
                
                # Check if content contains HTML or special characters
                if (('<' in content and '>' in content) or 
                    ('&lt;' in content and '&gt;' in content) or
                    ('&amp;' in content)):
                    
                    # If content has escaped HTML entities, unescape them first
                    if '&lt;' in content and '&gt;' in content:
                        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    
                    return f'<{tag}{attributes}><![CDATA[{content}]]></{tag}>'
                
                # Check if this element originally had CDATA (even without HTML)
                # This handles cases like URLs in Image elements
                original_pattern = f'<{tag}[^>]*>.*?</{tag}\\s*>'
                original_matches = re.findall(original_pattern, original_xml, re.DOTALL | re.IGNORECASE)
                for orig_match in original_matches:
                    if attributes.strip() in orig_match and '<![CDATA[' in orig_match:
                        # Original had CDATA, so restore it to prevent HTML escaping
                        return f'<{tag}{attributes}><![CDATA[{content}]]></{tag}>'
                
                return match.group(0)
            
            xml_string = pattern.sub(wrap_if_needed, xml_string)
        
        return xml_string

    def _get_element_path(self, element):
        """Generate a path string to identify the element in the XML tree."""
        path = element.tag
        
        # Add any identifiable attributes
        for attr in ['Title', 'Id', 'id', 'ID', 'name', 'Name']:
            if attr in element.attrib:
                path += f"[{attr}='{element.attrib[attr]}']"
                break
                
        return path
