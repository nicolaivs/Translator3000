#!/usr/bin/env python3
"""
CSV Translation Script
======================

This script translates specified columns in a CSV file from English to Dutch
using the Google Translate API via the googletrans library.

Usage:
    python csv_translator.py

Features:
- Reads CSV files with products or other data
- Translates specified columns from English to Dutch (Netherlands)
- Preserves original data and adds translated columns
- Handles translation errors gracefully
- Uses free Google Translate API (no API key required)

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log'),
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
        
        logger.info(f"Translator configured: {SUPPORTED_LANGUAGES[source_lang]} → {SUPPORTED_LANGUAGES[target_lang]}")
        
        # Initialize the appropriate translator
        if TRANSLATOR_TYPE == "deep_translator":            self.translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)
        elif TRANSLATOR_TYPE == "googletrans":
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
                     append_suffix: str = "_dutch",
                     delimiter: str = ",") -> bool:
        """
        Translate specified columns in a CSV file and save the result.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            columns_to_translate: List of column names to translate
            append_suffix: Suffix to append to translated column names
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
                result_df[new_column_name] = translated_column
                  # Save the result with the same delimiter
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
                translated = self.translator.translate(text_clean)
            elif TRANSLATOR_TYPE == "googletrans":
                result = self.translator.translate(
                    text_clean, 
                    src=self.source_lang, 
                    dest=self.target_lang
                )
                translated = result.text
            else:                return text
                
            # Add delay to avoid rate limiting
            time.sleep(self.delay)
            
            return translated
            
        except Exception as e:
            logger.warning(f"Plain text translation failed for '{text}': {e}")
            return text

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
    
def get_user_input() -> Dict[str, any]:
    """Get user input for translation parameters."""
    # Get language preferences first
    lang_prefs = get_language_preferences()
    if not lang_prefs:
        return {}
    
    print(f"\n=== CSV Translation Script ===")
    print(f"Translation: {lang_prefs['source_name']} → {lang_prefs['target_name']}")
    print(f"Source files should be placed in: {SOURCE_DIR}")
    print(f"Translated files will be saved to: {TARGET_DIR}")
    print()
    
    # List available CSV files in source directory
    csv_files = list(SOURCE_DIR.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {SOURCE_DIR}")
        print("Please place your CSV files in the 'source' folder and try again.")
        return {}
    
    print("Available CSV files in source folder:")
    for i, file_path in enumerate(csv_files, 1):
        print(f"  {i}. {file_path.name}")
    print()
    
    # Get file selection
    if len(csv_files) == 1:
        selected_file = csv_files[0]
        print(f"Auto-selected: {selected_file.name}")
    else:
        try:
            choice = int(input("Select a file (enter number): ").strip())
            if 1 <= choice <= len(csv_files):
                selected_file = csv_files[choice - 1]
            else:
                print("Invalid selection!")
                return {}
        except ValueError:
            print("Invalid input! Please enter a number.")
            return {}
    
    input_file = str(selected_file)
    
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
        df_preview = pd.read_csv(input_file, nrows=0, delimiter=delimiter)  # Just read headers
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
    
    # Generate output file path in target directory
    output_filename = selected_file.stem + '_translated.csv'
    output_file = str(TARGET_DIR / output_filename)
    print(f"\nOutput will be saved to: {output_file}")
    
    return {
        'input_file': input_file,
        'output_file': output_file,
        'columns_to_translate': columns_to_translate,
        'delimiter': delimiter,
        'source_lang': lang_prefs['source_lang'],
        'target_lang': lang_prefs['target_lang'],
        'source_name': lang_prefs['source_name'],
        'target_name': lang_prefs['target_name']
    }


def main():
    """Main function to run the CSV translation script."""
    print("CSV Translation Script - Multi-Language Support")
    print("=" * 55)
    
    # Ensure directories exist
    SOURCE_DIR.mkdir(exist_ok=True)
    TARGET_DIR.mkdir(exist_ok=True)
    
    print(f"📁 Source directory: {SOURCE_DIR}")
    print(f"📁 Target directory: {TARGET_DIR}")
    print()
    
    # Example usage for automated processing (uncomment and modify as needed)
    # translator = CSVTranslator(source_lang='en', target_lang='nl', delay_between_requests=0.1)
    # success = translator.translate_csv(
    #     input_file=str(SOURCE_DIR / "products.csv"),
    #     output_file=str(TARGET_DIR / "products_translated.csv"),
    #     columns_to_translate=["name", "description"]
    # )
    
    # Interactive mode
    params = get_user_input()
    if not params:
        print("Exiting due to invalid input.")
        return
    
    # Create translator instance with selected languages
    translator = CSVTranslator(
        source_lang=params['source_lang'],
        target_lang=params['target_lang'],
        delay_between_requests=0.1
    )
    
    # Perform translation
    print(f"\nStarting translation...")
    print(f"Language: {params['source_name']} → {params['target_name']}")
    print(f"Input file: {params['input_file']}")
    print(f"Output file: {params['output_file']}")
    print(f"Columns to translate: {params['columns_to_translate']}")
    print(f"CSV delimiter: '{params['delimiter']}'")
    print("\nThis may take a while depending on the size of your file...")
    
    success = translator.translate_csv(
        input_file=params['input_file'],
        output_file=params['output_file'],
        columns_to_translate=params['columns_to_translate'],
        delimiter=params['delimiter']
    )
    
    if success:
        print(f"\n✅ Translation completed successfully!")
        print(f"📁 Translated file saved as: {params['output_file']}")
        print(f"📋 Log file: translation.log")
        print(f"📂 Check the 'target' folder for your translated file")
    else:
        print(f"\n❌ Translation failed. Check the log file for details.")


if __name__ == "__main__":
    main()
