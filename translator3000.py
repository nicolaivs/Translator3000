#!/usr/bin/env python3
"""
Translator3000 - Multi-Language CSV & XML Translation Script
===========================================================

This script translates CSV file columns and XML text content between multiple languages
using the Google Translate API via translation libraries.

Usage:
    python translator3000.py

Features:
- Reads CSV files and XML files from source directory and subdirectories
- Translates between 10 supported languages
- Preserves original data structure and adds translated versions
- Batch processing for multiple files and folders
- Handles translation errors gracefully
- Uses free Google Translate API (no API key required)
- Auto-detects CSV delimiters and text columns
- Preserves XML structure and attributes

Author: Generated for CSV Translation Project  
Date: June 2025
"""

import pandas as pd
import time
import sys
import os
import re
from typing import List, Dict, Optional
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
import concurrent.futures
import threading
from collections import deque

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define project directories
PROJECT_ROOT = Path(__file__).parent
SOURCE_DIR = PROJECT_ROOT / "source"
TARGET_DIR = PROJECT_ROOT / "target"

# Ensure directories exist
SOURCE_DIR.mkdir(exist_ok=True)
TARGET_DIR.mkdir(exist_ok=True)

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    'da': 'Danish',
    'nl': 'Dutch (Netherlands)',
    'nl-be': 'Dutch (Flemish)',
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'no': 'Norwegian (Bokmål)',
    'es': 'Spanish',
    'sv': 'Swedish'
}

# Try to import translation libraries in order of preference
TRANSLATOR_TYPE = None
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_TYPE = "deep_translator"
    logger.info("Using deep-translator library")
except ImportError:
    try:
        from googletrans import Translator
        TRANSLATOR_TYPE = "googletrans"
        logger.info("Using googletrans library")
    except ImportError:
        logger.error("No translation library available. Please install deep-translator or googletrans")
        TRANSLATOR_TYPE = None

# Try to import BeautifulSoup for better HTML handling
try:
    from bs4 import BeautifulSoup
    HTML_PARSER_AVAILABLE = True
    logger.info("BeautifulSoup available for advanced HTML parsing")
except ImportError:
    HTML_PARSER_AVAILABLE = False
    logger.info("BeautifulSoup not available, using regex for HTML parsing")


class CSVTranslator:
    """A class to handle CSV file translation between different languages."""
    
    def __init__(self, source_lang: str = 'en', target_lang: str = 'nl', delay_between_requests: float = 0.05):
        """
        Initialize the CSV translator.
        
        Args:
            source_lang: Source language code (e.g., 'en', 'da')
            target_lang: Target language code (e.g., 'nl', 'sv')
            delay_between_requests: Delay in seconds between translation requests
                                  to avoid rate limiting
        """
        if TRANSLATOR_TYPE is None:
            raise ImportError("No translation library available. Please install deep-translator or googletrans")
        
        # Validate language codes
        if source_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: {source_lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")
        if target_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language: {target_lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")
        
        self.delay = delay_between_requests
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        logger.info(f"Translator configured: {SUPPORTED_LANGUAGES[source_lang]} -> {SUPPORTED_LANGUAGES[target_lang]}")
          # Initialize the appropriate translator
        if TRANSLATOR_TYPE == "deep_translator":
            # For deep_translator, we create a translator instance with specific languages
            self.translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)        
        elif TRANSLATOR_TYPE == "googletrans":
            # For googletrans, we create a generic translator instance
            self.translator = Translator()
        else:
            raise ImportError("No valid translator found")
        
        # Load glossary for custom translations
        self.glossary = self._load_glossary()
    
    def translate_text(self, text: str) -> str:
        """
        Translate a single text string from source to target language.
        Automatically detects and handles HTML content properly.
        Applies glossary replacements before AND after translation.
        
        Args:
            text: Text to translate (can contain HTML)
            
        Returns:
            Translated text with preserved HTML structure and glossary terms applied
        """
        if not text or pd.isna(text):
            return text
            
        try:
            # Convert to string and strip whitespace
            text_str = str(text).strip()
            if not text_str:
                return text
            
            # Apply glossary replacements BEFORE translation
            text_with_glossary = self._apply_glossary_replacements(text_str)
            
            # Check if content contains HTML
            if self.is_html_content(text_with_glossary):
                logger.debug(f"Detected HTML content, using HTML-aware translation")
                translated = self.translate_html_content(text_with_glossary)
            else:
                # Plain text translation
                translated = self._translate_plain_text(text_with_glossary)
            
            # Apply glossary replacements AFTER translation to fix any capitalization issues
            final_result = self._apply_glossary_replacements(translated)
                
            logger.debug(f"Translated: '{text_str[:50]}...' -> '{final_result[:50]}...'")
            return final_result
            
        except Exception as e:
            logger.warning(f"Translation failed for '{text}': {e}")
            return text  # Return original text if translation fails

    def translate_column(self, df: pd.DataFrame, column_name: str, use_multithreading: bool = True, max_workers: int = 4) -> pd.Series:
        """
        Translate an entire column of the DataFrame.
        
        Args:
            df: DataFrame containing the data
            column_name: Name of the column to translate
            use_multithreading: Whether to use multithreading (default: True)
            max_workers: Number of worker threads for multithreading (default: 4)
            
        Returns:
            Series with translated values
        """
        if column_name not in df.columns:
            logger.error(f"Column '{column_name}' not found in DataFrame")
            return pd.Series()
        
        # Choose between multithreaded and single-threaded approach
        if use_multithreading and len(df) > 5:  # Only use multithreading for larger datasets
            return self.translate_column_multithreaded(df, column_name, max_workers)
        else:
            return self._translate_column_single_threaded(df, column_name)
    
    def _translate_column_single_threaded(self, df: pd.DataFrame, column_name: str) -> pd.Series:
        """
        Single-threaded translation method (original implementation).
        
        Args:
            df: DataFrame containing the data
            column_name: Name of the column to translate
            
        Returns:
            Series with translated values
        """            
        logger.info(f"Translating column: {column_name} (single-threaded)")
        
        translated_values = []
        total_rows = len(df[column_name])
        
        for idx, value in enumerate(df[column_name]):
            if idx % 10 == 0:  # Progress update every 10 rows
                logger.info(f"Progress: {idx + 1}/{total_rows} rows processed")
                
            translated_value = self.translate_text(value)
            translated_values.append(translated_value)
            
        logger.info(f"Completed translation of column: {column_name}")
        return pd.Series(translated_values, index=df.index)
    
    def translate_column_multithreaded(self, df: pd.DataFrame, column_name: str, max_workers: int = 4) -> pd.Series:
        """
        Translate an entire column using multithreading for improved performance.
        
        Args:
            df: DataFrame containing the data
            column_name: Name of the column to translate
            max_workers: Number of worker threads (default: 4)
            
        Returns:
            Series with translated values
        """
        if column_name not in df.columns:
            logger.error(f"Column '{column_name}' not found in DataFrame")
            return pd.Series()
        
        logger.info(f"Translating column: {column_name} (using {max_workers} threads)")
        
        # Prepare data for multithreading
        values_to_translate = [(idx, value) for idx, value in enumerate(df[column_name])]
        total_rows = len(values_to_translate)
        
        # Thread-safe progress tracking
        progress_lock = threading.Lock()
        progress_counter = [0]  # Use list for mutable reference
        
        def translate_with_progress(idx_value_pair):
            """Translate a single value with thread-safe progress tracking."""
            idx, value = idx_value_pair
            translated = self.translate_text(value)
            
            # Update progress in thread-safe manner
            with progress_lock:
                progress_counter[0] += 1
                if progress_counter[0] % 10 == 0:
                    logger.info(f"Progress: {progress_counter[0]}/{total_rows} rows processed")
            
            return idx, translated
        
        # Use ThreadPoolExecutor for concurrent translation
        results = [None] * total_rows  # Pre-allocate results array
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all translation tasks
                future_to_idx = {
                    executor.submit(translate_with_progress, (idx, value)): idx 
                    for idx, value in values_to_translate
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_idx):
                    try:
                        idx, translated_value = future.result()
                        results[idx] = translated_value
                    except Exception as e:
                        # Handle individual translation failures
                        original_idx = future_to_idx[future]
                        original_value = values_to_translate[original_idx][1]
                        logger.warning(f"Translation failed for row {original_idx}: {e}")
                        results[original_idx] = original_value  # Fallback to original
        
        except Exception as e:
            logger.error(f"Multithreaded translation failed: {e}")
            # Fallback to single-threaded approach
            logger.info("Falling back to single-threaded translation...")
            return self.translate_column(df, column_name)
        
        logger.info(f"Completed multithreaded translation of column: {column_name}")
        return pd.Series(results, index=df.index)

    def translate_csv(self, 
                     input_file: str, 
                     output_file: str, 
                     columns_to_translate: List[str],
                     append_suffix: str = "_translated",
                     delimiter: str = ",") -> bool:
        """
        Translate specified columns in a CSV file and save the result.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            columns_to_translate: List of column names to translate
            append_suffix: Suffix to append to translated column names (e.g., "_german", "_french")
            delimiter: CSV delimiter (comma "," or semicolon ";")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the CSV file with specified delimiter
            logger.info(f"Reading CSV file: {input_file} (delimiter: '{delimiter}')")
            df = pd.read_csv(input_file, encoding='utf-8', delimiter=delimiter)
            logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            
            # Log column names for reference
            logger.info(f"Available columns: {list(df.columns)}")
            
            # Validate columns exist
            missing_columns = [col for col in columns_to_translate if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing columns: {missing_columns}")
                return False
            
            # Create a copy of the original DataFrame
            result_df = df.copy()
            
            # Translate each specified column
            for column in columns_to_translate:
                logger.info(f"Starting translation of column: {column}")
                translated_column = self.translate_column(df, column)
                
                # Add translated column with suffix
                new_column_name = f"{column}{append_suffix}"
                result_df[new_column_name] = translated_column            # Save the result with the same delimiter
            logger.info(f"Saving translated CSV to: {output_file} (delimiter: '{delimiter}')")
            result_df.to_csv(output_file, index=False, encoding='utf-8', sep=delimiter)
            
            logger.info("Translation completed successfully!")
            logger.info(f"Original columns: {len(df.columns)}")
            logger.info(f"Final columns: {len(result_df.columns)}")
            
            return True
            
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            return False
        except Exception as e:
            logger.error(f"Error during translation: {e}")
            return False

    def is_html_content(self, text: str) -> bool:
        """
        Check if the text contains HTML tags.
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains HTML tags, False otherwise
        """
        if not text:
            return False
        
        # Simple regex to detect HTML tags
        html_pattern = re.compile(r'<[^>]+>')
        return bool(html_pattern.search(str(text)))
    
    def translate_html_content(self, html_text: str) -> str:
        """
        Translate HTML content while preserving HTML tags and structure.
        
        Args:
            html_text: HTML content to translate
            
        Returns:
            Translated HTML with preserved structure
        """
        if not html_text or pd.isna(html_text):
            return html_text
            
        try:
            html_str = str(html_text).strip()
            if not html_str:
                return html_text
                
            if HTML_PARSER_AVAILABLE:
                return self._translate_html_with_beautifulsoup(html_str)
            else:
                return self._translate_html_with_regex(html_str)
                
        except Exception as e:
            logger.warning(f"HTML translation failed for '{html_text[:50]}...': {e}")
            return html_text
    
    def _translate_html_with_beautifulsoup(self, html_text: str) -> str:
        """
        Translate HTML using BeautifulSoup for proper parsing.
        """
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Find all text nodes (not inside script/style tags)
            for text_node in soup.find_all(string=True):
                if text_node.parent.name not in ['script', 'style', 'meta', 'title']:
                    text_content = text_node.strip()
                    if text_content and len(text_content) > 1:
                        translated = self._translate_plain_text(text_content)
                        text_node.replace_with(translated)
            
            return str(soup)
            
        except Exception as e:
            logger.warning(f"BeautifulSoup HTML parsing failed: {e}")
            return self._translate_html_with_regex(html_text)
    
    def _translate_html_with_regex(self, html_text: str) -> str:
        """
        Translate HTML using regex (fallback method).
        """
        try:
            # Pattern to match text outside of HTML tags
            # This is a simplified approach - BeautifulSoup is preferred
            def translate_match(match):
                text_content = match.group(0).strip()
                if len(text_content) > 1 and not text_content.startswith('<'):
                    return self._translate_plain_text(text_content)
                return text_content
            
            # Find text outside of tags
            pattern = r'>([^<]+)<'
            translated = re.sub(pattern, lambda m: f'>{self._translate_plain_text(m.group(1))}<', html_text)
            
            # Handle text at the beginning and end
            if not html_text.startswith('<'):
                first_tag_pos = html_text.find('<')
                if first_tag_pos > 0:
                    prefix = html_text[:first_tag_pos].strip()
                    if prefix:
                        translated = self._translate_plain_text(prefix) + html_text[first_tag_pos:]
            
            return translated            
        except Exception as e:
            logger.warning(f"Regex HTML parsing failed: {e}")
            return html_text
    
    def _translate_with_retry(self, text: str, max_retries: int = 3, base_delay: float = 0.05) -> str:
        """
        Translate text with exponential backoff retry mechanism.
        
        Args:
            text: Text to translate
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds (will increase with each retry)
            
        Returns:
            Translated text
        """
        if not text or len(text.strip()) <= 1:
            return text
            
        text_clean = text.strip()
        last_exception = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Translate using the appropriate library
                if TRANSLATOR_TYPE == "deep_translator":
                    translated = self.translator.translate(text_clean)
                elif TRANSLATOR_TYPE == "googletrans":
                    result = self.translator.translate(
                        text_clean, 
                        src=self.source_lang, 
                        dest=self.target_lang
                    )
                    translated = result.text
                else:
                    return text
                
                # Success! Add minimal delay and return
                if attempt == 0:
                    # First attempt - use minimal delay
                    time.sleep(base_delay)
                else:
                    # Retry succeeded - use slightly longer delay to be respectful
                    time.sleep(base_delay * 2)
                    logger.debug(f"Translation succeeded on attempt {attempt + 1}")
                
                return translated
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    # Calculate exponential backoff delay
                    retry_delay = base_delay * (2 ** attempt) + (0.05 * attempt)  # 50ms extra per retry
                    logger.debug(f"Translation attempt {attempt + 1} failed: {e}. Retrying in {retry_delay:.3f}s...")
                    time.sleep(retry_delay)
                else:
                    # All retries exhausted
                    logger.warning(f"Translation failed after {max_retries + 1} attempts for '{text[:50]}...': {last_exception}")
        
        # If we get here, all attempts failed
        return text

    def _translate_plain_text(self, text: str) -> str:
        """
        Translate plain text without HTML.
        
        Args:
            text: Plain text to translate
            
        Returns:
            Translated text
        """
        if not text or len(text.strip()) <= 1:
            return text
            
        try:
            text_clean = text.strip()
              # Translate using the appropriate library
            if TRANSLATOR_TYPE == "deep_translator":
                # deep_translator: translator was initialized with languages, so only pass text
                translated = self.translator.translate(text_clean)
            elif TRANSLATOR_TYPE == "googletrans":
                # googletrans: generic translator, so pass text and language parameters
                result = self.translator.translate(
                    text_clean, 
                    src=self.source_lang, 
                    dest=self.target_lang
                )
                translated = result.text
            else:
                return text
                
            # Add delay to avoid rate limiting
            time.sleep(self.delay)
            
            return translated
            
        except Exception as e:
            logger.warning(f"Plain text translation failed for '{text}': {e}")
            return text

    def translate_xml(self, input_file: str, output_file: str) -> bool:
        """
        Translate text content in XML file while preserving structure and attributes.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Reading XML file: {input_file}")
            
            # Parse the XML file
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Count total text elements for progress tracking
            total_elements = self._count_text_elements(root)
            logger.info(f"Found {total_elements} text elements to translate")
            
            # Translate all text content recursively
            translated_count = self._translate_xml_element(root, 0, total_elements)
            
            # Save the translated XML
            logger.info(f"Saving translated XML to: {output_file}")
            self._save_xml_pretty(tree, output_file)
            
            logger.info(f"XML translation completed successfully!")
            logger.info(f"Translated {translated_count} text elements")
            
            return True
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return False
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            return False
        except Exception as e:
            logger.error(f"Error during XML translation: {e}")
            return False
    
    def _count_text_elements(self, element) -> int:
        """Count elements with text content for progress tracking."""
        count = 0
        if element.text and element.text.strip():
            count += 1
        if element.tail and element.tail.strip():
            count += 1
        for child in element:
            count += self._count_text_elements(child)
        return count
    
    def _translate_xml_element(self, element, current_count: int, total_count: int) -> int:
        """
        Recursively translate text content in XML elements.
        
        Args:
            element: XML element to process
            current_count: Current progress count
            total_count: Total elements to process
            
        Returns:
            Updated count of processed elements
        """
        processed_count = current_count
        
        # Translate element text content
        if element.text and element.text.strip():
            processed_count += 1
            if processed_count % 10 == 0:  # Progress update every 10 elements
                logger.info(f"Progress: {processed_count}/{total_count} elements processed")
            
            original_text = element.text.strip()
            translated_text = self.translate_text(original_text)
            
            # Preserve whitespace structure
            if element.text.startswith(' ') or element.text.startswith('\n'):
                element.text = element.text.replace(original_text, translated_text)
            else:
                element.text = translated_text
        
        # Translate tail text (text after closing tag)
        if element.tail and element.tail.strip():
            processed_count += 1
            if processed_count % 10 == 0:
                logger.info(f"Progress: {processed_count}/{total_count} elements processed")
            
            original_tail = element.tail.strip()
            translated_tail = self.translate_text(original_tail)
            
            # Preserve whitespace structure
            if element.tail.startswith(' ') or element.tail.startswith('\n'):
                element.tail = element.tail.replace(original_tail, translated_tail)
            else:
                element.tail = translated_tail
          # Recursively process child elements
        for child in element:
            processed_count = self._translate_xml_element(child, processed_count, total_count)
        
        return processed_count
    
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
            
            # Clean up extra blank lines that minidom adds
            lines = []
            for line in pretty_xml.split('\n'):
                line = line.rstrip()  # Remove trailing whitespace
                if line.strip():  # Only keep non-empty lines
                    lines.append(line)
            
            # Save with pretty formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
        except Exception as e:
            logger.warning(f"Error pretty-printing XML: {e}. Writing raw XML.")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(xml_str)
    
    def _restore_cdata_for_html_content(self, xml_str: str) -> str:
        """Restore CDATA sections for content that contains HTML tags."""
        import re
        
        # Look for content that has HTML entities (indicating original HTML/CDATA content)
        # Pattern to match element content that contains HTML entities
        pattern = r'(<([^>]+)>)([^<]*(?:&(?:lt|gt|amp|quot|apos);[^<]*)+)</\2>'
        
        def replace_with_cdata(match):
            opening_tag = match.group(1)
            tag_name = match.group(2)
            content = match.group(3)
            closing_tag = f'</{tag_name}>'
            
            # Unescape HTML entities
            unescaped_content = (content
                                .replace('&lt;', '<')
                                .replace('&gt;', '>')
                                .replace('&amp;', '&')
                                .replace('&quot;', '"')
                                .replace('&apos;', "'"))
            
            # If the unescaped content contains HTML tags, wrap in CDATA
            if '<' in unescaped_content and '>' in unescaped_content:
                return f'{opening_tag}<![CDATA[{unescaped_content}]]>{closing_tag}'
            
            return match.group(0)
        
        # Apply the replacement
        result = re.sub(pattern, replace_with_cdata, xml_str, flags=re.DOTALL)
        
        return result

    def _load_glossary(self) -> Dict[str, Dict[str, str]]:
        """
        Load the glossary CSV file for custom translation terms.
        
        Returns:
            Dictionary mapping source terms to target terms and case preferences
        """
        glossary = {}
        glossary_file = PROJECT_ROOT / "glossary.csv"
        
        if not glossary_file.exists():
            logger.info("No glossary.csv file found. Using translation API only.")
            return glossary
        
        try:
            # Read the glossary CSV
            with open(glossary_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip header and empty lines
            for line_num, line in enumerate(lines[1:], 2):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(';')
                if len(parts) != 3:
                    logger.warning(f"Glossary line {line_num} has wrong format (expected 3 columns): {line}")
                    continue
                
                source_term, target_term, keep_case = parts
                source_term = source_term.strip()
                target_term = target_term.strip()
                keep_case = keep_case.strip().lower() == 'true'
                
                if source_term and target_term:
                    glossary[source_term.lower()] = {
                        'target': target_term,
                        'keep_case': keep_case
                    }
            
            if glossary:
                logger.info(f"Loaded {len(glossary)} terms from glossary.csv")
            else:
                logger.info("Glossary.csv file is empty or contains no valid entries")
                
        except Exception as e:
            logger.warning(f"Error loading glossary.csv: {e}")
        
        return glossary
    
    def _apply_glossary_replacements(self, text: str) -> str:
        """
        Apply glossary replacements to text before translation.
        
        Args:
            text: Text to process
            
        Returns:
            Text with glossary terms replaced
        """
        if not hasattr(self, 'glossary') or not self.glossary:
            return text
        
        result = text
        
        for source_term, config in self.glossary.items():
            target_term = config['target']
            keep_case = config['keep_case']
            
            # Create case-insensitive pattern for whole words
            pattern = re.compile(r'\b' + re.escape(source_term) + r'\b', re.IGNORECASE)
            
            def replace_match(match):
                matched_text = match.group(0)
                
                if keep_case:
                    # Preserve the case pattern of the original match
                    return self._preserve_case(matched_text, target_term)
                else:
                    # Use target term as-is
                    return target_term
            
            result = pattern.sub(replace_match, result)
        
        return result
    
    def _preserve_case(self, original: str, replacement: str) -> str:
        """
        Preserve the case pattern of the original word when applying replacement.
        
        Args:
            original: Original word with case pattern to preserve
            replacement: Replacement word
            
        Returns:
            Replacement word with case pattern of original
        """
        if original.isupper():
            return replacement.upper()
        elif original.islower():
            return replacement.lower()
        elif original.istitle():
            return replacement.capitalize()
        else:
            # Mixed case - return replacement as-is
            return replacement

def get_language_suffix(lang_code: str) -> str:
    """Generate a column suffix based on language code."""
    # Create a mapping for cleaner suffixes
    suffix_mapping = {
        'da': '_danish',
        'nl': '_dutch',
        'nl-be': '_flemish',
        'en': '_english',
        'fr': '_french',
        'de': '_german',
        'it': '_italian',
        'no': '_norwegian',
        'es': '_spanish',
        'sv': '_swedish'
    }
    return suffix_mapping.get(lang_code, f'_{lang_code}')

def get_language_name(lang_code: str) -> str:
    """Get the full language name for a language code."""
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code)

def generate_output_filename(input_filename: str, lang_code: str, is_root_file: bool = True) -> str:
    """
    Generate output filename based on location and language.
    
    Args:
        input_filename: Original filename with extension
        lang_code: Target language code (e.g., 'sv', 'da')
        is_root_file: True if processing root file, False if in subfolder
        
    Returns:
        New filename with language suffix
    """
    path = Path(input_filename)
    stem = path.stem
    extension = path.suffix
    
    if is_root_file:
        # For root files: "filename - Language.ext"
        language_name = get_language_name(lang_code)
        return f"{stem} - {language_name}{extension}"
    else:
        # For batch subfolder files: keep original name
        return input_filename

def generate_output_directory(base_dir: Path, folder_name: str, lang_code: str, is_batch_folder: bool = False) -> Path:
    """
    Generate output directory path based on processing mode.
    
    Args:
        base_dir: Base target directory
        folder_name: Name of the source folder (or 'root')
        lang_code: Target language code
        is_batch_folder: True if processing a batch folder (not root)
        
    Returns:
        Target directory path
    """
    if folder_name == 'root' or not is_batch_folder:
        # For root files, use base target directory
        return base_dir
    else:
        # For batch folders: "foldername - Language"
        language_name = get_language_name(lang_code)
        return base_dir / f"{folder_name} - {language_name}"

def get_language_preferences() -> Dict[str, str]:
    """Get source and target language preferences from user."""
    print("=== Language Configuration ===")
    
    # Source language selection
    print("\nSelect source language (language of your CSV content):")
    print("  1. English (default)")
    print("  2. Danish")
    source_choice = input("Enter choice (1 or 2, default: 1): ").strip()
    
    if source_choice == "2":
        source_lang = "da"
        print("Selected: Danish")
    else:
        source_lang = "en"
        print("Selected: English")
    
    # Target language selection
    print(f"\nSelect target language (translate TO):")
    lang_options = [
        ('da', 'Danish'),
        ('nl', 'Dutch (Netherlands)'),
        ('nl-be', 'Dutch (Flemish)'),
        ('en', 'English'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('no', 'Norwegian (Bokmål)'),
        ('es', 'Spanish'),
        ('sv', 'Swedish')
    ]
    
    for i, (code, name) in enumerate(lang_options, 1):
        print(f"  {i}. {name} ({code})")
    
    while True:
        try:
            target_choice = input("Enter choice (1-10): ")

            # Check for empty input and set default
            if target_choice.strip() == "":
                target_choice = "1"
                print("No choice entered, defaulting to 1. English (en)")
            
            choice_idx = int(target_choice) - 1
            if 0 <= choice_idx < len(lang_options):
                target_lang, target_name = lang_options[choice_idx]
                print(f"Selected: {target_name}")
                break
            else:
                print("Invalid choice! Please enter a number between 1-10.")
        except ValueError:
            print("Invalid input! Please enter a number.")
    
    # Validate different languages
    if source_lang == target_lang:
        print("⚠️  Warning: Source and target languages are the same!")
        confirm = input("Do you want to continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return {}
    
    return {
        'source_lang': source_lang,
        'target_lang': target_lang,
        'source_name': SUPPORTED_LANGUAGES[source_lang],
        'target_name': SUPPORTED_LANGUAGES[target_lang]
    }


def discover_files_and_folders() -> Dict[str, List[Path]]:
    """
    Discover all CSV and XML files in source directory, including subdirectories.
    
    Returns:
        Dictionary with structure: {
            'root_files': [list of files in root source dir],
            'folders': {
                'folder_name': [list of files in that folder],
                ...
            }
        }
    """
    discovered = {
        'root_files': [],
        'folders': {}
    }
    
    # Find files in root source directory
    for file_path in SOURCE_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.xml']:
            discovered['root_files'].append(file_path)
    
    # Find subdirectories and their files
    for item in SOURCE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            folder_files = []
            # Look for CSV/XML files in subdirectory
            for file_path in item.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.xml']:
                    folder_files.append(file_path)
            
            if folder_files:  # Only include folders that have CSV/XML files
                discovered['folders'][item.name] = folder_files
    
    return discovered

def print_discovered_files(discovered: Dict[str, List[Path]]) -> int:
    """
    Print discovered files and return total count.
    
    Args:
        discovered: Dictionary from discover_files_and_folders()
        
    Returns:
        Total number of files found
    """
    total_files = 0
    
    # Print root files
    if discovered['root_files']:
        print("[ROOT] Files in source root:")
        for file_path in discovered['root_files']:
            file_type = "CSV" if file_path.suffix.lower() == ".csv" else "XML"
            print(f"  • {file_path.name} ({file_type})")
            total_files += 1
        print()
    
    # Print folder contents
    if discovered['folders']:
        print("[SUBDIRS] Files in subdirectories:")
        for folder_name, files in discovered['folders'].items():
            print(f"  [FOLDER] {folder_name}/")
            for file_path in files:
                file_type = "CSV" if file_path.suffix.lower() == ".csv" else "XML"
                relative_path = file_path.relative_to(SOURCE_DIR / folder_name)
                print(f"    • {relative_path} ({file_type})")
                total_files += 1
            print()
    
    return total_files

def get_batch_processing_input() -> Dict[str, any]:
    """Get user input for batch processing mode."""
    # Get language preferences first
    lang_prefs = get_language_preferences()
    if not lang_prefs:
        return {}
    
    print(f"\n=== Batch CSV & XML Translation Script ===")
    print(f"Translation: {lang_prefs['source_name']} -> {lang_prefs['target_name']}")
    print(f"Source files will be scanned from: {SOURCE_DIR}")
    print(f"Translated files will be saved to: {TARGET_DIR}")
    print()
    
    # Discover all files
    discovered = discover_files_and_folders()
    total_files = print_discovered_files(discovered)
    
    if total_files == 0:
        print(f"No CSV or XML files found in {SOURCE_DIR} or its subdirectories.")
        print("Please place your files in the 'source' folder and try again.")
        return {}
    
    print(f"[TOTAL] Total files found: {total_files}")
    print()
    
    # Ask user about processing mode
    print("Choose processing mode:")
    print("  1. Single file mode (original behavior)")
    print("  2. Batch mode (process all discovered files)")
    
    mode_choice = input("Enter choice (1 or 2, default: 1): ").strip()
    if mode_choice == "2":
        # Batch mode - allow folder selection
        folder_choice = get_batch_folder_selection(discovered)
        if not folder_choice:
            return {}
        
        print(f"\n[BATCH] Batch mode selected!")
        
        # Calculate files to process based on selection
        if folder_choice['type'] == 'root':
            files_to_process = len(discovered['root_files'])
            print(f"Processing {files_to_process} files from root directory.")
        elif folder_choice['type'] == 'folder':
            files_to_process = len(discovered['folders'][folder_choice['folder_name']])
            print(f"Processing {files_to_process} files from folder: {folder_choice['folder_name']}")
        elif folder_choice['type'] == 'all':
            files_to_process = total_files
            print(f"Processing all {files_to_process} files from all locations.")
          # For batch mode, we need to handle CSV column selection differently
        if any(f.suffix.lower() == '.csv' for f in discovered['root_files']) or \
           any(any(f.suffix.lower() == '.csv' for f in files) for files in discovered['folders'].values()):
            print("\n[CSV] CSV Column Selection:")
            print("Since multiple CSV files may have different structures,")
            print("you'll be prompted for column selection for each CSV file during processing.")
        
        return {
            'mode': 'batch',
            'discovered': discovered,
            'folder_choice': folder_choice,
            'source_lang': lang_prefs['source_lang'],
            'target_lang': lang_prefs['target_lang'],
            'source_name': lang_prefs['source_name'],
            'target_name': lang_prefs['target_name']
        }
    else:
        # Single file mode - use original logic
        return get_single_file_input(discovered, lang_prefs)

def get_single_file_input(discovered: Dict[str, List[Path]], lang_prefs: Dict) -> Dict[str, any]:
    """Get input for single file processing mode."""
    # Create a flat list of all files for selection
    all_files = []
    file_locations = []  # Track where each file is located
    
    # Add root files
    for file_path in discovered['root_files']:
        all_files.append(file_path)
        file_locations.append('root')
    
    # Add folder files
    for folder_name, files in discovered['folders'].items():
        for file_path in files:
            all_files.append(file_path)
            file_locations.append(folder_name)
    
    if not all_files:
        print("No files available for selection.")
        return {}
    
    print("Select a file to translate:")
    for i, (file_path, location) in enumerate(zip(all_files, file_locations), 1):
        file_type = "CSV" if file_path.suffix.lower() == ".csv" else "XML"
        if location == 'root':
            print(f"  {i}. {file_path.name} ({file_type}) [root]")
        else:
            relative_path = file_path.relative_to(SOURCE_DIR)
            print(f"  {i}. {relative_path} ({file_type}) [in {location}/]")
    print()
    
    # Get file selection
    if len(all_files) == 1:
        selected_file = all_files[0]
        selected_location = file_locations[0]
        print(f"Auto-selected: {selected_file.name}")
    else:
        try:
            choice = int(input("Select a file (enter number): ").strip())
            if 1 <= choice <= len(all_files):
                selected_file = all_files[choice - 1]
                selected_location = file_locations[choice - 1]
            else:
                print("Invalid selection!")
                return {}
        except ValueError:
            print("Invalid input! Please enter a number.")
            return {}
    
    input_file = str(selected_file)
    file_type = selected_file.suffix.lower()
    
    # Determine output file path
    if selected_location == 'root':
        # File is in root - output to target root
        output_dir = TARGET_DIR
    else:
        # File is in subfolder - create corresponding target subfolder
        output_dir = TARGET_DIR / selected_location
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle different file types
    if file_type == ".csv":
        return get_csv_input_single(selected_file, input_file, output_dir, lang_prefs)
    elif file_type == ".xml":
        return get_xml_input_single(selected_file, input_file, output_dir, lang_prefs)
    else:
        print(f"Unsupported file type: {file_type}")
        return {}

def get_csv_input_single(selected_file: Path, input_file: str, output_dir: Path, lang_prefs: Dict) -> Dict[str, any]:
    """Get CSV-specific input parameters for single file mode."""
    
    # Auto-detect CSV delimiter (same logic as batch mode)
    print("\nAuto-detecting CSV delimiter...")
    delimiters = [',', ';']
    df_preview = None
    chosen_delimiter = ','
    
    for delimiter in delimiters:
        try:
            df_test = pd.read_csv(input_file, nrows=5, delimiter=delimiter)
            if len(df_test.columns) > 1:  # Good indication of correct delimiter
                df_preview = pd.read_csv(input_file, nrows=0, delimiter=delimiter)
                chosen_delimiter = delimiter
                break
        except:
            continue
    
    if df_preview is None:
        print("Could not auto-detect delimiter. Trying manual selection...")
        # Fallback to manual selection  
        print("Choose CSV delimiter:")
        print("  1. Comma (,) - Standard CSV format")
        print("  2. Semicolon (;) - European CSV format")
        delimiter_choice = input("Enter choice (1 or 2, default: 1): ").strip()
        
        if delimiter_choice == "2":
            chosen_delimiter = ";"
        else:
            chosen_delimiter = ","
        
        try:
            df_preview = pd.read_csv(input_file, nrows=0, delimiter=chosen_delimiter)
        except Exception as e:
            print(f"Error reading CSV file with {chosen_delimiter} delimiter: {e}")
            return {}

if __name__ == "__main__":
    # Main execution would go here - currently handled by interactive mode
    pass