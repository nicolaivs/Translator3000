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
    
    def __init__(self, source_lang: str = 'en', target_lang: str = 'nl', delay_between_requests: float = 0.1):
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
        
    def translate_text(self, text: str) -> str:
        """
        Translate a single text string from source to target language.
        Automatically detects and handles HTML content properly.
        
        Args:
            text: Text to translate (can contain HTML)
            
        Returns:
            Translated text with preserved HTML structure
        """
        if not text or pd.isna(text):
            return text
            
        try:
            # Convert to string and strip whitespace
            text_str = str(text).strip()
            if not text_str:
                return text
            
            # Check if content contains HTML
            if self.is_html_content(text_str):
                logger.debug(f"Detected HTML content, using HTML-aware translation")
                translated = self.translate_html_content(text_str)
            else:
                # Plain text translation
                translated = self._translate_plain_text(text_str)
                
            logger.debug(f"Translated: '{text_str[:50]}...' -> '{translated[:50]}...'")            
            return translated
            
        except Exception as e:
            logger.warning(f"Translation failed for '{text}': {e}")
            return text  # Return original text if translation fails
    
    def translate_column(self, df: pd.DataFrame, column_name: str) -> pd.Series:
        """
        Translate an entire column of the DataFrame.
        
        Args:
            df: DataFrame containing the data
            column_name: Name of the column to translate
            
        Returns:
            Series with translated values
        """
        if column_name not in df.columns:
            logger.error(f"Column '{column_name}' not found in DataFrame")
            return pd.Series()
            
        logger.info(f"Translating column: {column_name}")
        
        translated_values = []
        total_rows = len(df[column_name])
        
        for idx, value in enumerate(df[column_name]):
            if idx % 10 == 0:  # Progress update every 10 rows
                logger.info(f"Progress: {idx + 1}/{total_rows} rows processed")
                
            translated_value = self.translate_text(value)
            translated_values.append(translated_value)
            
        logger.info(f"Completed translation of column: {column_name}")
        return pd.Series(translated_values, index=df.index)
    
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
        """Save XML with pretty formatting."""
        # Convert to string
        xml_str = ET.tostring(tree.getroot(), encoding='unicode')
        
        # Parse with minidom for pretty printing
        dom = minidom.parseString(xml_str)
        
        # Save with pretty formatting
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dom.toprettyxml(indent="  "))

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

def get_language_preferences() -> Dict[str, str]:
    """Get source and target language preferences from user."""
    print("=== Language Configuration ===")
    
    # Source language selection    print("\nSelect source language (language of your CSV content):")
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
            target_choice = input("Enter choice (1-10): ").strip()
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
    # Get CSV delimiter preference
    print("\nChoose CSV delimiter:")
    print("  1. Comma (,) - Standard CSV format")
    print("  2. Semicolon (;) - European CSV format")
    delimiter_choice = input("Enter choice (1 or 2, default: 1): ").strip()
    
    if delimiter_choice == "2":
        delimiter = ";"
        print("Selected: Semicolon (;) delimiter")
    else:
        delimiter = ","
        print("Selected: Comma (,) delimiter")
    print()
    
    # Load CSV to show available columns
    try:
        df_preview = pd.read_csv(input_file, nrows=0, delimiter=delimiter)
        print(f"\nAvailable columns in '{selected_file.name}':")
        columns_list = list(df_preview.columns)
        for i, col in enumerate(columns_list, 1):
            print(f"  {i}. {col}")
    except Exception as e:
        print(f"Error reading CSV file with {delimiter} delimiter: {e}")
        print("Try using the other delimiter option.")
        return {}
    
    # Get columns to translate by numbers
    print("\nWhich columns would you like to translate?")
    print("Enter column numbers separated by commas (e.g., 1,3 or 2,4,5)")
    columns_input = input("Column numbers: ").strip()
    
    if not columns_input:
        print("No columns specified!")
        return {}
    
    # Parse column numbers and convert to column names
    try:
        column_numbers = [int(num.strip()) for num in columns_input.split(',')]
        columns_to_translate = []
        
        for num in column_numbers:
            if 1 <= num <= len(columns_list):
                columns_to_translate.append(columns_list[num - 1])
            else:
                print(f"Invalid column number: {num}. Must be between 1 and {len(columns_list)}")
                return {}
        
        print(f"Selected columns: {', '.join(columns_to_translate)}")
        
    except ValueError:
        print("Invalid input! Please enter numbers separated by commas.")
        return {}
    
    # Generate output file path
    output_filename = selected_file.stem + '_translated.csv'
    output_file = str(output_dir / output_filename)
    print(f"\nOutput will be saved to: {output_file}")
    
    return {
        'mode': 'single',
        'file_type': 'csv',
        'input_file': input_file,
        'output_file': output_file,
        'columns_to_translate': columns_to_translate,
        'delimiter': delimiter,
        'source_lang': lang_prefs['source_lang'],
        'target_lang': lang_prefs['target_lang'],
        'source_name': lang_prefs['source_name'],
        'target_name': lang_prefs['target_name']
    }

def get_xml_input_single(selected_file: Path, input_file: str, output_dir: Path, lang_prefs: Dict) -> Dict[str, any]:
    """Get XML-specific input parameters for single file mode."""
    print(f"\nXML file selected: {selected_file.name}")
    print("XML translation will translate all text content while preserving structure and attributes.")
    
    # Generate output file path
    output_filename = selected_file.stem + '_translated.xml'
    output_file = str(output_dir / output_filename)
    print(f"Output will be saved to: {output_file}")
    
    return {
        'mode': 'single',
        'file_type': 'xml',
        'input_file': input_file,
        'output_file': output_file,
        'source_lang': lang_prefs['source_lang'],
        'target_lang': lang_prefs['target_lang'],
        'source_name': lang_prefs['source_name'],
        'target_name': lang_prefs['target_name']
    }

def process_batch_files(params: Dict[str, any]) -> bool:
    """
    Process selected files in batch mode based on folder choice.
    
    Args:
        params: Parameters from get_batch_processing_input()
        
    Returns:
        True if all files processed successfully, False otherwise
    """
    discovered = params['discovered']
    folder_choice = params['folder_choice']
    source_lang = params['source_lang']
    target_lang = params['target_lang']
    
    # Create translator instance
    translator = CSVTranslator(
        source_lang=source_lang,
        target_lang=target_lang,
        delay_between_requests=0.1
    )
    
    successful_files = 0
    failed_files = []
    
    # Determine which files to process based on folder choice
    files_to_process = []
    
    if folder_choice['type'] == 'root':
        # Process only root files
        for file_path in discovered['root_files']:
            files_to_process.append((file_path, 'root'))
        print(f"\n[BATCH] Processing {len(files_to_process)} files from root directory...")
        
    elif folder_choice['type'] == 'folder':
        # Process only the selected folder
        folder_name = folder_choice['folder_name']
        for file_path in discovered['folders'][folder_name]:
            files_to_process.append((file_path, folder_name))
        print(f"\n[BATCH] Processing {len(files_to_process)} files from folder: {folder_name}")
        
    elif folder_choice['type'] == 'all':
        # Process all files (original behavior)
        for file_path in discovered['root_files']:
            files_to_process.append((file_path, 'root'))
        for folder_name, files in discovered['folders'].items():
            for file_path in files:
                files_to_process.append((file_path, folder_name))
        print(f"\n[BATCH] Processing {len(files_to_process)} files from all locations...")
    
    if not files_to_process:
        print("[WARNING] No files to process!")
        return True
    
    print(f"Language: {params['source_name']} -> {params['target_name']}")
    print()
    
    # Process the selected files
    for current_file, (file_path, location) in enumerate(files_to_process, 1):
        if location == 'root':
            print(f"[FILE] Processing file {current_file}/{len(files_to_process)}: {file_path.name}")
            output_dir = TARGET_DIR
        else:
            relative_path = file_path.relative_to(SOURCE_DIR)
            print(f"[FILE] Processing file {current_file}/{len(files_to_process)}: {relative_path}")
            # Create target subfolder
            output_dir = TARGET_DIR / location
            output_dir.mkdir(parents=True, exist_ok=True)
            if current_file == 1 or location not in [loc for _, loc in files_to_process[:current_file-1]]:
                print(f"[FOLDER] Created target folder: {output_dir}")
        
        if process_single_file_batch(file_path, output_dir, translator, target_lang):
            successful_files += 1
            if location == 'root':
                print(f"[SUCCESS] Successfully processed: {file_path.name}")
            else:
                relative_path = file_path.relative_to(SOURCE_DIR)
                print(f"[SUCCESS] Successfully processed: {relative_path}")
        else:
            if location == 'root':
                failed_files.append(str(file_path.name))
                print(f"[FAILED] Failed to process: {file_path.name}")
            else:
                relative_path = file_path.relative_to(SOURCE_DIR)
                failed_files.append(str(relative_path))
                print(f"[FAILED] Failed to process: {relative_path}")
        print()
    
    # Print summary
    print("=" * 60)
    print("[SUMMARY] BATCH PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total files: {len(files_to_process)}")
    print(f"Successfully processed: {successful_files}")
    print(f"Failed: {len(failed_files)}")
    
    if failed_files:
        print("\n[FAILED] Failed files:")
        for failed_file in failed_files:
            print(f"  • {failed_file}")
    
    if successful_files > 0:
        print(f"\n[SUCCESS] Successfully translated files are saved in: {TARGET_DIR}")
        print(f"[LOG] Check the log file for detailed information: translation.log")
    
    return len(failed_files) == 0

def process_single_file_batch(file_path: Path, output_dir: Path, translator: 'CSVTranslator', target_lang: str) -> bool:
    """
    Process a single file in batch mode.
    
    Args:
        file_path: Path to the source file
        output_dir: Directory where output should be saved
        translator: Configured translator instance
        target_lang: Target language code
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_type = file_path.suffix.lower()
        
        if file_type == '.csv':
            return process_csv_file_batch(file_path, output_dir, translator, target_lang)
        elif file_type == '.xml':
            return process_xml_file_batch(file_path, output_dir, translator)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return False

def process_csv_file_batch(file_path: Path, output_dir: Path, translator: 'CSVTranslator', target_lang: str) -> bool:
    """Process a single CSV file in batch mode."""
    try:
        # Try different delimiters to determine the correct one
        delimiters = [',', ';']
        df = None
        chosen_delimiter = ','
        
        for delimiter in delimiters:
            try:
                df_test = pd.read_csv(file_path, nrows=5, delimiter=delimiter)
                if len(df_test.columns) > 1:  # Good indication of correct delimiter
                    df = pd.read_csv(file_path, delimiter=delimiter)
                    chosen_delimiter = delimiter
                    break
            except:
                continue
        
        if df is None:
            logger.error(f"Could not read CSV file with any known delimiter: {file_path}")
            return False
        
        logger.info(f"CSV file loaded with '{chosen_delimiter}' delimiter: {file_path}")
        logger.info(f"Available columns: {list(df.columns)}")
        
        # Auto-detect text columns for translation
        text_columns = []
        for col in df.columns:
            # Sample a few values to see if they contain text
            sample_values = df[col].dropna().head(3).astype(str)
            if any(len(str(val)) > 10 and any(c.isalpha() for c in str(val)) for val in sample_values):
                text_columns.append(col)
        
        if not text_columns:
            # Fallback: ask user or use all string columns
            string_columns = df.select_dtypes(include=['object']).columns.tolist()
            text_columns = string_columns[:2] if len(string_columns) >= 2 else string_columns
        
        if not text_columns:
            logger.warning(f"No suitable text columns found in {file_path}")
            return False
        
        logger.info(f"Auto-selected columns for translation: {text_columns}")
        
        # Generate output file path
        output_filename = file_path.stem + '_translated.csv'
        output_file = output_dir / output_filename
        
        # Generate language-specific suffix
        language_suffix = get_language_suffix(target_lang)
        
        # Translate the CSV
        success = translator.translate_csv(
            input_file=str(file_path),
            output_file=str(output_file),
            columns_to_translate=text_columns,
            append_suffix=language_suffix,
            delimiter=chosen_delimiter
        )
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing CSV file {file_path}: {e}")
        return False

def process_xml_file_batch(file_path: Path, output_dir: Path, translator: 'CSVTranslator') -> bool:
    """Process a single XML file in batch mode."""
    try:
        # Generate output file path
        output_filename = file_path.stem + '_translated.xml'
        output_file = output_dir / output_filename
        
        # Translate the XML
        success = translator.translate_xml(
            input_file=str(file_path),
            output_file=str(output_file)
        )
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing XML file {file_path}: {e}")
        return False

def get_batch_folder_selection(discovered: Dict[str, List[Path]]) -> Dict[str, any]:
    """
    Allow user to select which folder to batch process.
    
    Args:
        discovered: Dictionary from discover_files_and_folders()
        
    Returns:
        Dictionary with selection info: {'type': 'root'|'folder'|'all', 'folder_name': str}
    """
    options = []
    
    # Add root option if there are root files
    if discovered['root_files']:
        options.append(('root', f"Root directory only ({len(discovered['root_files'])} files)"))
    
    # Add individual folder options
    for folder_name, files in discovered['folders'].items():
        options.append(('folder', f"Folder '{folder_name}' only ({len(files)} files)", folder_name))
    
    # Add "all" option if there are both root files and folders
    if discovered['root_files'] and discovered['folders']:
        total_files = len(discovered['root_files']) + sum(len(files) for files in discovered['folders'].values())
        options.append(('all', f"All files and folders ({total_files} files total)"))
    
    if not options:
        print("No files available for batch processing.")
        return {}
    
    print("\nChoose what to batch process:")
    for i, option in enumerate(options, 1):
        if len(option) == 2:  # root or all
            print(f"  {i}. {option[1]}")
        else:  # specific folder
            print(f"  {i}. {option[1]}")
    
    while True:
        try:
            choice = input(f"Enter choice (1-{len(options)}): ").strip()
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_option = options[choice_idx]
                
                if selected_option[0] == 'root':
                    print(f"Selected: Root directory only")
                    return {'type': 'root'}
                elif selected_option[0] == 'folder':
                    folder_name = selected_option[2]
                    print(f"Selected: Folder '{folder_name}' only")
                    return {'type': 'folder', 'folder_name': folder_name}
                elif selected_option[0] == 'all':
                    print(f"Selected: All files and folders")
                    return {'type': 'all'}
                break
            else:
                print(f"Invalid choice! Please enter a number between 1-{len(options)}.")
        except ValueError:
            print("Invalid input! Please enter a number.")
    
    return {}

def main():
    """Main function to run the Translator3000 - Multi-Language CSV & XML Translation Script."""
    print("Translator3000 - Multi-Language CSV & XML Translation Script")
    print("=" * 70)
    
    # Display translator information
    if TRANSLATOR_TYPE == "deep_translator":
        print("[ENGINE] Translation Engine: deep-translator (preferred)")
    elif TRANSLATOR_TYPE == "googletrans":
        print("[ENGINE] Translation Engine: googletrans (fallback)")
    else:
        print("[ERROR] No translation engine available!")
        return
      # Ensure directories exist
    SOURCE_DIR.mkdir(exist_ok=True)
    TARGET_DIR.mkdir(exist_ok=True)
    
    print(f"[SOURCE] Source directory: {SOURCE_DIR}")
    print(f"[TARGET] Target directory: {TARGET_DIR}")
    print()
    
    # Example usage for automated processing (uncomment and modify as needed)
    # translator = CSVTranslator(source_lang='en', target_lang='nl', delay_between_requests=0.1)
    # For CSV:
    # success = translator.translate_csv(
    #     input_file=str(SOURCE_DIR / "products.csv"),
    #     output_file=str(TARGET_DIR / "products_translated.csv"),
    #     columns_to_translate=["name", "description"]
    # )
    # For XML:
    # success = translator.translate_xml(
    #     input_file=str(SOURCE_DIR / "content.xml"),
    #     output_file=str(TARGET_DIR / "content_translated.xml")
    # )
      # Interactive mode
    params = get_batch_processing_input()
    if not params:
        print("Exiting due to invalid input.")
        return
    
    if params.get('mode') == 'batch':
        # Batch processing mode
        success = process_batch_files(params)
        if success:
            print(f"\n🎉 All files processed successfully!")
        else:
            print(f"\n⚠️ Some files failed to process. Check the log for details.")
        return
    
    # Single file mode (original behavior)
    # Create translator instance with selected languages
    translator = CSVTranslator(
        source_lang=params['source_lang'],
        target_lang=params['target_lang'],
        delay_between_requests=0.1
    )
      # Perform translation based on file type
    print(f"\nStarting translation...")
    print(f"Language: {params['source_name']} -> {params['target_name']}")
    print(f"Input file: {params['input_file']}")
    print(f"Output file: {params['output_file']}")
    
    if params['file_type'] == 'csv':
        print(f"Columns to translate: {params['columns_to_translate']}")
        print(f"CSV delimiter: '{params['delimiter']}'")
        print("\nThis may take a while depending on the size of your file...")
        
        # Generate language-specific suffix
        language_suffix = get_language_suffix(params['target_lang'])
        
        success = translator.translate_csv(
            input_file=params['input_file'],
            output_file=params['output_file'],
            columns_to_translate=params['columns_to_translate'],
            append_suffix=language_suffix,
            delimiter=params['delimiter']
        )
    elif params['file_type'] == 'xml':
        print("File type: XML")
        print("\nThis may take a while depending on the size of your file...")
        
        success = translator.translate_xml(
            input_file=params['input_file'],
            output_file=params['output_file']
        )
    else:
        print("[ERROR] Unsupported file type!")
        return
    
    if success:
        print(f"\n[SUCCESS] Translation completed successfully!")
        print(f"[OUTPUT] Translated file saved as: {params['output_file']}")
        print(f"[LOG] Log file: translation.log")
        print(f"[OUTPUT] Check the 'target' folder for your translated file")
    else:
        print(f"\n[FAILED] Translation failed. Check the log file for details.")


if __name__ == "__main__":
    main()
