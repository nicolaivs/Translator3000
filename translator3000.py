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
import asyncio
import io
from typing import List, Dict, Optional
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
import concurrent.futures
import threading
from collections import deque

# Configure logging with UTF-8 encoding and Unicode-safe console output
import io

# Create a UTF-8 compatible stdout wrapper for Windows
if sys.platform.startswith('win'):
    # On Windows, wrap stdout to handle Unicode characters
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
else:
    utf8_stdout = sys.stdout

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log', encoding='utf-8'),
        logging.StreamHandler(utf8_stdout)
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

# Default configuration values
# Performance optimized settings - see PERFORMANCE.md for detailed analysis
DEFAULT_CONFIG = {
    'delay': 5,  # milliseconds between requests (optimal: 4.6 trans/sec vs 3.7 at 50ms)
    'max_retries': 3,
    'retry_base_delay': 20,
    'csv_max_workers': 4,
    'xml_max_workers': 4,
    'multithreading_threshold': 2,
    'progress_interval': 10,
    'translation_services': 'deep_translator,googletrans,libretranslate',
    'libretranslate_selfhost_enabled': True,
    'libretranslate_selfhost_port': 5000,
    'libretranslate_selfhost_timeout': 2,
    'libretranslate_selfhost_url': 'http://localhost:5000/translate',
    'libretranslate_url': 'https://libretranslate.com/translate',
    'libretranslate_api_key': ''
}

def load_config() -> Dict:
    """Load configuration from translator3000.config file."""
    config = DEFAULT_CONFIG.copy()
    config_file = PROJECT_ROOT / "translator3000.config"
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.split('#')[0].strip()  # Remove inline comments
                        
                        if key in config:
                            try:
                                # Convert to appropriate type (check bool first, since bool is subclass of int)
                                if isinstance(config[key], bool) or value.lower() in ('true', 'false'):
                                    config[key] = value.lower() == 'true'
                                elif isinstance(config[key], int):
                                    config[key] = int(value)
                                elif isinstance(config[key], float):
                                    config[key] = float(value)
                                else:
                                    config[key] = value
                            except ValueError:
                                logger.warning(f"Invalid config value at line {line_num}: {line}")
                        else:
                            # Add new config keys that aren't in DEFAULT_CONFIG yet
                            config[key] = value
            
            logger.info(f"Loaded configuration: delay={config['delay']}ms, max_workers={config['csv_max_workers']}")
        except Exception as e:
            logger.warning(f"Error loading config file: {e}. Using defaults.")
    else:
        logger.info(f"No config file found. Using defaults: delay={config['delay']}ms")
    
    return config

# Load configuration
CONFIG = load_config()

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

# Try to import translation libraries based on config preference
AVAILABLE_TRANSLATORS = {}

# Check for LibreTranslate support (requests library)
try:
    import requests
    AVAILABLE_TRANSLATORS['libretranslate'] = True
    logger.info("LibreTranslate support available (requests library found)")
except ImportError:
    AVAILABLE_TRANSLATORS['libretranslate'] = False
    logger.info("LibreTranslate support unavailable (requests library not found)")

# Check for deep_translator
try:
    from deep_translator import GoogleTranslator
    AVAILABLE_TRANSLATORS['deep_translator'] = True
    logger.info("deep-translator library available")
except ImportError:
    AVAILABLE_TRANSLATORS['deep_translator'] = False
    logger.info("deep-translator library not available")

# Check for googletrans
try:
    from googletrans import Translator
    import googletrans
    
    # Check if this is googletrans 4.x (has async methods)
    googletrans_version = getattr(googletrans, '__version__', '3.x')
    is_googletrans_4x = googletrans_version.startswith('4.')
    
    if is_googletrans_4x:
        # For googletrans 4.x, create a synchronous wrapper
        class GoogleTranslator4xWrapper:
            """Synchronous wrapper for googletrans 4.x async API."""
            
            def __init__(self):
                self.translator = Translator()
            
            def translate(self, text: str, src: str, dest: str):
                """Synchronous translation method that wraps the async API."""
                try:
                    # Create a new event loop if none exists
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            raise RuntimeError("Event loop is closed")
                    except RuntimeError:
                        # No event loop exists, create a new one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Run the async translation
                    result = loop.run_until_complete(
                        self.translator.translate(text, src=src, dest=dest)
                    )
                    return result
                except Exception as e:
                    # If async fails, try the synchronous method (fallback)
                    try:
                        return self.translator.translate(text, src=src, dest=dest)
                    except:
                        raise e
        
        # Use the wrapper for 4.x
        GoogleTranslatorClass = GoogleTranslator4xWrapper
        logger.info("googletrans 4.x library available (using async wrapper)")
    else:
        # For googletrans 3.x, use the translator directly
        GoogleTranslatorClass = Translator
        logger.info("googletrans 3.x library available")
    
    AVAILABLE_TRANSLATORS['googletrans'] = True
    
except ImportError:
    AVAILABLE_TRANSLATORS['googletrans'] = False
    GoogleTranslatorClass = None
    logger.info("googletrans library not available")

def is_libretranslate_selfhost_available() -> bool:
    """Check if LibreTranslate is running on self-hosted server."""
    if not CONFIG.get('libretranslate_selfhost_enabled', True):
        return False
        
    try:
        import requests
        selfhost_url = CONFIG.get('libretranslate_selfhost_url', 'http://localhost:5000/translate')
        timeout = CONFIG.get('libretranslate_selfhost_timeout', 2)
        
        # Extract base URL for health check
        if '/translate' in selfhost_url:
            base_url = selfhost_url.replace('/translate', '')
        else:
            base_url = selfhost_url
            
        # Simple GET request to check if service is responding
        response = requests.get(base_url, timeout=timeout)
        
        # Check if it responds with expected LibreTranslate content
        if response.status_code == 200:
            # LibreTranslate usually has "LibreTranslate" in the HTML title or content
            content = response.text.lower()
            if 'libretranslate' in content or 'translate' in content:
                logger.info(f"✓ Self-hosted LibreTranslate detected at {selfhost_url}")
                return True
            else:
                logger.debug(f"Service at {base_url} doesn't appear to be LibreTranslate")
                return False
        else:
            logger.debug(f"Self-hosted service at {base_url} responded with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.debug(f"selfhost LibreTranslate check failed: {e}")
        return False


def get_optimized_translation_services() -> List[str]:
    """Get translation services in optimal order, prioritizing selfhost if available."""
    base_services = CONFIG.get('translation_services', 'deep_translator,googletrans,libretranslate').split(',')
    base_services = [s.strip() for s in base_services]
    
    # Check if selfhost LibreTranslate is available
    if is_libretranslate_selfhost_available():
        # If selfhost is available, prioritize it by putting it first
        # and ensure we only have one libretranslate entry
        optimized_services = ['libretranslate']  # selfhost version goes first
        for service in base_services:
            if service != 'libretranslate':  # avoid duplicates
                optimized_services.append(service)
        
        logger.info("🚀 Self-hosted LibreTranslate prioritized for optimal performance")
        return optimized_services
    else:
        # No selfhost, use configured order
        logger.info("Using configured service order (no self-hosted LibreTranslate detected)")
        return base_services


# Determine available translation services based on config preference
def get_translation_services():
    """Get available translation services in optimal order, prioritizing localhost if available."""
    # Get optimized service order (this handles localhost detection and prioritization)
    optimized_services = get_optimized_translation_services()
    available_services = []
    
    for service in optimized_services:
        service = service.strip()
        if service in AVAILABLE_TRANSLATORS and AVAILABLE_TRANSLATORS[service]:
            available_services.append(service)
    
    if not available_services:
        logger.error("No translation services available! Please install at least one: requests, deep-translator, or googletrans")
        return []
    
    logger.info(f"Available translation services (in order): {', '.join(available_services)}")
    return available_services

# Get the ordered list of translation services
TRANSLATION_SERVICES = get_translation_services()

# Try to import BeautifulSoup for better HTML handling
try:
    from bs4 import BeautifulSoup
    HTML_PARSER_AVAILABLE = True
    logger.info("BeautifulSoup available for advanced HTML parsing")
except ImportError:
    HTML_PARSER_AVAILABLE = False
    logger.info("BeautifulSoup not available, using regex for HTML parsing")


class LibreTranslateService:
    """LibreTranslate API service wrapper."""
    
    def __init__(self, source_lang: str, target_lang: str, api_url: str, api_key: str = ""):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_url = api_url
        self.api_key = api_key
        
        # Validate that requests is available
        if 'libretranslate' not in AVAILABLE_TRANSLATORS or not AVAILABLE_TRANSLATORS['libretranslate']:
            raise ImportError("LibreTranslate requires the 'requests' library")
    
    def translate(self, text: str) -> str:
        """Translate text using LibreTranslate API."""
        if not text or not text.strip():
            return text
            
        payload = {
            "q": text.strip(),
            "source": self.source_lang,
            "target": self.target_lang
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Add API key if provided
        if self.api_key:
            payload["api_key"] = self.api_key
        
        try:
            import requests
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 429:
                raise Exception("Rate limit exceeded - consider using an API key")
            elif response.status_code == 403:
                raise Exception("Access forbidden - check API key")
            elif response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            if 'translatedText' in result:
                return result['translatedText']
            else:
                raise Exception(f"Unexpected response format: {result}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request timeout - LibreTranslate server may be overloaded")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check internet connection")
        except Exception as e:
            if "Rate limit" in str(e) or "429" in str(e):
                raise Exception("LibreTranslate rate limit hit - falling back to next service")
            raise Exception(f"LibreTranslate API error: {e}")


class CSVTranslator:
    """A class to handle CSV file translation between different languages."""
    
    def __init__(self, source_lang: str = 'en', target_lang: str = 'nl', delay_between_requests: float = None):
        """
        Initialize the CSV translator with multiple translation service support.
        
        Args:
            source_lang: Source language code (e.g., 'en', 'da')
            target_lang: Target language code (e.g., 'nl', 'sv')
            delay_between_requests: Delay in seconds between translation requests
                                  (if None, uses config file setting)
        """
        if not TRANSLATION_SERVICES:
            raise ImportError("No translation services available. Please install at least one: requests, deep-translator, or googletrans")
        
        # Validate language codes
        if source_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: {source_lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")
        if target_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language: {target_lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")
        
        # Use config delay if not explicitly provided (convert from ms to seconds)
        if delay_between_requests is None:
            self.delay = CONFIG['delay'] / 1000.0  # Convert ms to seconds
        else:
            self.delay = delay_between_requests
        
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        logger.info(f"Translator configured: {SUPPORTED_LANGUAGES[source_lang]} -> {SUPPORTED_LANGUAGES[target_lang]}")
        logger.info(f"Request delay: {self.delay*1000:.1f}ms between requests")
        
        # Initialize translation services in order of preference
        self.translators = []
        self._initialize_translators()
        
        # Load glossary for custom translations
        self.glossary = self._load_glossary()
    
    def _initialize_translators(self):
        """Initialize available translation services in order of preference."""
        for service in TRANSLATION_SERVICES:
            try:
                if service == 'libretranslate':
                    # Choose URL based on selfhost availability
                    if is_libretranslate_selfhost_available():
                        api_url = CONFIG['libretranslate_selfhost_url']
                        logger.info("🚀 Using self-hosted LibreTranslate instance for optimal performance")
                    else:
                        api_url = CONFIG['libretranslate_url']
                        logger.info("Using remote LibreTranslate service")
                    
                    translator = LibreTranslateService(
                        source_lang=self.source_lang,
                        target_lang=self.target_lang,
                        api_url=api_url,
                        api_key=CONFIG['libretranslate_api_key']
                    )
                    self.translators.append(('libretranslate', translator))
                    logger.info(f"✓ LibreTranslate service initialized")
                
                elif service == 'deep_translator':
                    from deep_translator import GoogleTranslator
                    translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)
                    self.translators.append(('deep_translator', translator))
                    logger.info(f"✓ deep-translator service initialized")
                
                elif service == 'googletrans':
                    translator = GoogleTranslatorClass()
                    self.translators.append(('googletrans', translator))
                    logger.info(f"✓ googletrans service initialized")
                    
            except Exception as e:
                logger.warning(f"Failed to initialize {service}: {e}")
        
        if not self.translators:
            raise ImportError("No translation services could be initialized")
        
        logger.info(f"Active translation services: {[name for name, _ in self.translators]}")
    
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

    def translate_column(self, df: pd.DataFrame, column_name: str, use_multithreading: bool = True, max_workers: int = None) -> pd.Series:
        """
        Translate an entire column of the DataFrame.
        
        Args:
            df: DataFrame containing the data
            column_name: Name of the column to translate
            use_multithreading: Whether to use multithreading (default: True)
            max_workers: Number of worker threads (uses config if None)
            
        Returns:
            Series with translated values
        """
        if column_name not in df.columns:
            logger.error(f"Column '{column_name}' not found in DataFrame")
            return pd.Series()
        
        # Use config default if not specified
        if max_workers is None:
            max_workers = CONFIG['csv_max_workers']
          # Choose between multithreaded and single-threaded approach
        if use_multithreading and len(df) > CONFIG['multithreading_threshold']:
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
            if idx % CONFIG['progress_interval'] == 0:  # Progress update based on config
                logger.info(f"Progress: {idx + 1}/{total_rows} rows processed")
                
            translated_value = self.translate_text(value)
            translated_values.append(translated_value)
            
        logger.info(f"Completed translation of column: {column_name}")
        return pd.Series(translated_values, index=df.index)
    
    def translate_column_multithreaded(self, df: pd.DataFrame, column_name: str, max_workers: int = None) -> pd.Series:
        """
        Translate an entire column using multithreading for improved performance.
        
        Args:
            df: DataFrame containing the data
            column_name: Name of the column to translate
            max_workers: Number of worker threads (uses config if None)
            
        Returns:
            Series with translated values
        """
        if column_name not in df.columns:
            logger.error(f"Column '{column_name}' not found in DataFrame")
            return pd.Series()
        
        # Use config default if not specified
        if max_workers is None:
            max_workers = CONFIG['csv_max_workers']
        
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
                if progress_counter[0] % CONFIG['progress_interval'] == 0:
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
    
    def _translate_with_retry(self, text: str, max_retries: int = None, base_delay: float = None) -> str:
        """
        Translate text with exponential backoff retry mechanism using multiple services.
        
        Args:
            text: Text to translate
            max_retries: Maximum number of retry attempts (uses config if None)
            base_delay: Base delay in seconds (uses config if None)
            
        Returns:
            Translated text
        """
        if not text or len(text.strip()) <= 1:
            return text
        
        # Use config values if not provided
        if max_retries is None:
            max_retries = CONFIG['max_retries']
        if base_delay is None:
            base_delay = CONFIG['retry_base_delay'] / 1000.0  # Convert ms to seconds
            
        text_clean = text.strip()
        
        # Try each translation service in order
        for service_name, translator in self.translators:
            logger.debug(f"Trying translation with {service_name}...")
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    # Translate using the current service
                    if service_name == "libretranslate":
                        translated = translator.translate(text_clean)
                    elif service_name == "deep_translator":
                        translated = translator.translate(text_clean)
                    elif service_name == "googletrans":
                        result = translator.translate(
                            text_clean, 
                            src=self.source_lang, 
                            dest=self.target_lang
                        )
                        translated = result.text
                    else:
                        continue  # Skip unknown service
                    
                    # Success! Add delay and return
                    if attempt == 0:
                        # First attempt - use configured delay
                        time.sleep(self.delay)
                    else:
                        # Retry succeeded - use slightly longer delay to be respectful
                        time.sleep(self.delay * 2)
                        logger.debug(f"Translation succeeded on attempt {attempt + 1} with {service_name}")
                    
                    logger.debug(f"✓ Translation successful with {service_name}")
                    return translated
                    
                except Exception as e:
                    if attempt < max_retries:
                        # Calculate exponential backoff delay
                        retry_delay = base_delay * (2 ** attempt) + (0.01 * attempt)  # 10ms extra per retry
                        logger.debug(f"{service_name} attempt {attempt + 1} failed: {e}. Retrying in {retry_delay:.3f}s...")
                        time.sleep(retry_delay)
                    else:
                        # All retries exhausted for this service
                        logger.warning(f"{service_name} failed after {max_retries + 1} attempts: {e}")
        
        # If we get here, all services failed
        logger.warning(f"All translation services failed for '{text[:50]}...'. Returning original text.")
        return text

    def _translate_plain_text(self, text: str) -> str:
        """
        Translate plain text without HTML using multiple services with fallback.
        
        Args:
            text: Plain text to translate
            
        Returns:
            Translated text
        """
        if not text or len(text.strip()) <= 1:
            return text
            
        try:
            text_clean = text.strip()
            
            # Try each translation service in order
            for service_name, translator in self.translators:
                try:
                    # Translate using the current service
                    if service_name == "libretranslate":
                        translated = translator.translate(text_clean)
                    elif service_name == "deep_translator":
                        translated = translator.translate(text_clean)
                    elif service_name == "googletrans":
                        result = translator.translate(
                            text_clean, 
                            src=self.source_lang, 
                            dest=self.target_lang
                        )
                        translated = result.text
                    else:
                        continue  # Skip unknown service
                    
                    # Success! Add delay and return
                    time.sleep(self.delay)
                    logger.debug(f"✓ Translation successful with {service_name}")
                    return translated
                    
                except Exception as e:
                    logger.debug(f"{service_name} failed: {e}. Trying next service...")
                    continue
            
            # If we get here, all services failed
            logger.warning(f"All translation services failed for '{text}'. Returning original text.")
            return text
            
        except Exception as e:
            logger.warning(f"Translation error for '{text}': {e}")
            return text

    def translate_xml(self, input_file: str, output_file: str, use_multithreading: bool = True, max_workers: int = None) -> bool:
        """
        Translate text content in XML file while preserving structure and attributes.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            use_multithreading: Whether to use multithreading (default: True)
            max_workers: Number of worker threads (uses config if None)
            
        Returns:
            True if successful, False otherwise
        """
        # Use config default if not specified
        if max_workers is None:
            max_workers = CONFIG['xml_max_workers']
            
        if use_multithreading:
            return self.translate_xml_multithreaded(input_file, output_file, max_workers)
        else:
            return self.translate_xml_sequential(input_file, output_file)

    def translate_xml_sequential(self, input_file: str, output_file: str) -> bool:
        """
        Translate text content in XML file sequentially (original method).
        
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
            
            # Collect all text elements that need translation
            text_elements = []
            self._collect_text_elements(root, text_elements)
            
            total_elements = len(text_elements)
            logger.info(f"Found {total_elements} text elements to translate")
            
            if total_elements == 0:
                # No text to translate, just copy the file
                logger.info("No text elements found, copying file as-is")
                tree.write(output_file, encoding='utf-8', xml_declaration=True)
                return True
            
            # Use sequential translation
            logger.info("Using single-threaded XML translation")
            success = self._translate_xml_elements_sequential(text_elements)
            
            if not success:
                logger.error("XML translation failed")
                return False
            
            # Save the translated XML
            logger.info(f"Saving translated XML to: {output_file}")
            self._save_xml_pretty(tree, output_file)
            
            logger.info(f"XML translation completed successfully!")
            logger.info(f"Translated {total_elements} text elements")
            
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
    
    def translate_xml_multithreaded(self, input_file: str, output_file: str, max_workers: int = None) -> bool:
        """
        Translate text content in XML file using multithreading for better performance.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file
            max_workers: Number of worker threads (uses config if None)
            
        Returns:
            True if successful, False otherwise
        """
        # Use config default if not specified
        if max_workers is None:
            max_workers = CONFIG['xml_max_workers']
            
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
                return True
            
            # Use multithreading if we have enough elements
            if total_elements > CONFIG['multithreading_threshold'] and max_workers > 1:
                logger.info(f"Using multithreaded XML translation with {max_workers} workers")
                success = self._translate_xml_elements_multithreaded(text_elements, max_workers)
            else:
                logger.info("Using single-threaded XML translation")
                success = self._translate_xml_elements_sequential(text_elements)
            
            if not success:
                logger.error("XML translation failed")
                return False
            
            # Save the translated XML
            logger.info(f"Saving translated XML to: {output_file}")
            self._save_xml_pretty(tree, output_file)
            
            logger.info(f"XML translation completed successfully!")
            logger.info(f"Translated {total_elements} text elements")
            
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

    def _translate_xml_elements_multithreaded(self, text_elements: List, max_workers: int) -> bool:
        """Translate XML text elements using multithreading."""
        try:
            # Thread-safe progress tracking
            progress_lock = threading.Lock()
            progress_counter = [0]
            total_elements = len(text_elements)
            
            def translate_element_text(text_data):
                """Translate a single text element."""
                try:
                    original_text = text_data['original']
                    translated = self.translate_text(original_text)
                    
                    # Update progress in thread-safe manner
                    with progress_lock:
                        progress_counter[0] += 1
                        if progress_counter[0] % CONFIG['progress_interval'] == 0 or progress_counter[0] == total_elements:
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
            return True
            
        except Exception as e:
            logger.error(f"Multithreaded XML translation failed: {e}")
            return False

    def _translate_xml_elements_sequential(self, text_elements: List) -> bool:
        """Translate XML text elements sequentially (fallback method)."""
        try:
            total_elements = len(text_elements)
            
            for idx, text_data in enumerate(text_elements):
                if (idx + 1) % CONFIG['progress_interval'] == 0 or (idx + 1) == total_elements:
                    logger.info(f"Progress: {idx + 1}/{total_elements} elements processed")
                
                original_text = text_data['original']
                translated = self.translate_text(original_text)
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
            
            return True
            
        except Exception as e:
            logger.error(f"Sequential XML translation failed: {e}")
            return False
    
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
    
    # Display detected columns for user confirmation
    print(f"\nDetected CSV structure:")
    for col in df_preview.columns:
        print(f"  - {col}")
    
    # Ask user to confirm or re-select columns
    columns_to_translate = list(df_preview.columns)  # Default to all columns
    confirm = input("\nTranslate all columns? (Y/n): ").strip().lower()
    if confirm == 'n':
        # Let user select specific columns
        columns_to_translate = []
        while True:
            col_choice = input("Enter column name (or blank to finish): ").strip()
            if not col_choice:
                break
            if col_choice in df_preview.columns:
                columns_to_translate.append(col_choice)
            else:
                print(f"Column '{col_choice}' not found. Please enter a valid column name.")
    
    # Generate column suffix based on target language
    suffix = f"_{get_language_suffix(lang_prefs['target_lang'])}"
    
    return {
        'mode': 'single',
        'selected_file': selected_file,
        'output_file': None,  # To be generated
        'columns_to_translate': columns_to_translate,
        'delimiter': chosen_delimiter,
        'append_suffix': suffix,
        'source_lang': lang_prefs['source_lang'],
        'target_lang': lang_prefs['target_lang'],
        'source_name': lang_prefs['source_name'],
        'target_name': lang_prefs['target_name']
    }

def get_batch_folder_selection(discovered: Dict[str, List[Path]]) -> Dict[str, any]:
    """Get user selection for which folders to process in batch mode."""
    print("\nBatch folder selection:")
    
    options = []
    
    # Option 1: Root files only
    if discovered['root_files']:
        root_count = len(discovered['root_files'])
        options.append(('root', f"Process root directory only ({root_count} files)"))
    
    # Option 2: Individual folders
    for folder_name, files in discovered['folders'].items():
        file_count = len(files)
        options.append(('folder', f"Process '{folder_name}' folder only ({file_count} files)", folder_name))
    
    # Option 3: All files
    total_files = len(discovered['root_files']) + sum(len(files) for files in discovered['folders'].values())
    options.append(('all', f"Process all files and folders ({total_files} files)"))
    
    # Display options
    for i, option in enumerate(options, 1):
        if option[0] == 'folder':
            print(f"  {i}. {option[1]}")
        else:
            print(f"  {i}. {option[1]}")
    
    # Get user choice
    while True:
        try:
            choice = input(f"Enter choice (1-{len(options)}): ").strip()
            if not choice:
                choice = "1"  # Default to first option
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_option = options[choice_idx]
                
                if selected_option[0] == 'root':
                    return {'type': 'root'}
                elif selected_option[0] == 'folder':
                    return {'type': 'folder', 'folder_name': selected_option[2]}
                elif selected_option[0] == 'all':
                    return {'type': 'all'}
            else:
                print(f"Invalid choice! Please enter a number between 1-{len(options)}.")
        except ValueError:
            print("Invalid input! Please enter a number.")

def get_xml_input_single(selected_file: Path, input_file: str, output_dir: Path, lang_prefs: Dict) -> Dict[str, any]:
    """Get XML-specific input parameters for single file mode."""
    
    # For XML files, we don't need column selection - just generate output filename
    output_filename = generate_output_filename(selected_file.name, lang_prefs['target_lang'], is_root_file=True)
    output_file = output_dir / output_filename
    
    print(f"\n📋 XML Translation Summary:")
    print(f"  📁 Input file: {selected_file.name}")
    print(f"  📁 Output file: {output_filename}")
    print(f"  🌐 Translation: {lang_prefs['source_name']} -> {lang_prefs['target_name']}")
    print(f"  🏷️  Processing: All text content (preserving XML structure)")
    
    return {
        'mode': 'single',
        'selected_file': selected_file,
        'output_file': output_file,
        'source_lang': lang_prefs['source_lang'],
        'target_lang': lang_prefs['target_lang'],
        'source_name': lang_prefs['source_name'],
        'target_name': lang_prefs['target_name']
    }

def main():
    """Main interactive workflow for the translation script."""
    try:
        print("=" * 60)
        print("🌍 Translator3000 - Multi-Language CSV & XML Translation")
        print("=" * 60)
        print()
        
        # Ensure source and target directories exist
        SOURCE_DIR.mkdir(exist_ok=True)
        TARGET_DIR.mkdir(exist_ok=True)
        
        # Get user input for batch processing (which includes language and file selection)
        user_input = get_batch_processing_input()
        
        if not user_input:
            print("❌ Translation cancelled or no valid input provided.")
            return
        
        # Create translator with selected languages (using config defaults)
        translator = CSVTranslator(
            source_lang=user_input['source_lang'],
            target_lang=user_input['target_lang']
            # delay_between_requests will use config file value automatically
        )
        
        print(f"\n🔧 Translator initialized: {user_input['source_name']} -> {user_input['target_name']}")
        
        # Process based on mode
        if user_input['mode'] == 'batch':
            print("\n🚀 Starting batch processing...")
            success = process_batch_mode(translator, user_input)
        else:
            print("\n🚀 Starting single file processing...")
            success = process_single_file_mode(translator, user_input)
        
        if success:
            print("\n✅ Translation completed successfully!")
            print(f"📁 Check the output files in: {TARGET_DIR}")
        else:
            print("\n❌ Translation completed with some errors.")
            print("📋 Check translation.log for details.")
            
    except KeyboardInterrupt:
        print("\n❌ Translation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error in main workflow: {e}")
        print(f"\n❌ An unexpected error occurred: {e}")
        print("📋 Check translation.log for details.")

def process_batch_mode(translator: CSVTranslator, user_input: Dict) -> bool:
    """Process files in batch mode."""
    discovered = user_input['discovered']
    folder_choice = user_input['folder_choice']
    target_lang = user_input['target_lang']
    
    # Determine which files to process
    files_to_process = []
    
    if folder_choice['type'] == 'root':
        files_to_process = [(f, 'root') for f in discovered['root_files']]
    elif folder_choice['type'] == 'folder':
        folder_name = folder_choice['folder_name']
        files_to_process = [(f, folder_name) for f in discovered['folders'][folder_name]]
    elif folder_choice['type'] == 'all':
        # Add root files
        files_to_process.extend([(f, 'root') for f in discovered['root_files']])
        # Add folder files
        for folder_name, files in discovered['folders'].items():
            files_to_process.extend([(f, folder_name) for f in files])
    
    success_count = 0
    total_files = len(files_to_process)
    
    print(f"\n📊 Processing {total_files} files...")
    
    for idx, (file_path, location) in enumerate(files_to_process, 1):
        print(f"\n[{idx}/{total_files}] Processing: {file_path.name}")
        
        # Generate output directory and filename
        if location == 'root':
            output_dir = TARGET_DIR
            output_filename = generate_output_filename(file_path.name, target_lang, is_root_file=True)
        else:
            output_dir = generate_output_directory(TARGET_DIR, location, target_lang, is_batch_folder=True)
            output_filename = generate_output_filename(file_path.name, target_lang, is_root_file=False)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / output_filename
        
        # Process file based on type
        success = False
        if file_path.suffix.lower() == '.csv':
            success = process_csv_file_batch(translator, file_path, output_file)
        elif file_path.suffix.lower() == '.xml':
            success = translator.translate_xml(str(file_path), str(output_file))
        
        if success:
            success_count += 1
            print(f"✅ {file_path.name} -> {output_filename}")
        else:
            print(f"❌ Failed to process {file_path.name}")
    
    print(f"\n📊 Batch processing complete: {success_count}/{total_files} files processed successfully")
    return success_count > 0

def process_csv_file_batch(translator: CSVTranslator, input_file: Path, output_file: Path) -> bool:
    """Process a single CSV file in batch mode with automatic column detection."""
    try:
        # Auto-detect delimiter
        delimiter = detect_csv_delimiter(str(input_file))
        print(f"  📄 Detected delimiter: '{delimiter}'")
        
        # Read CSV to analyze columns
        df = pd.read_csv(input_file, nrows=5, delimiter=delimiter)
        
        # Auto-detect text columns (columns likely to contain translatable text)
        text_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':  # Text columns
                # Check if column contains substantial text (not just codes/IDs)
                sample_text = df[col].dropna().astype(str).iloc[0] if not df[col].dropna().empty else ""
                if len(sample_text) > 10:  # Likely to be translatable text
                    text_columns.append(col)
        
        if not text_columns:
            print(f"  ⚠️  No suitable text columns found for translation")
            return False
        
        print(f"  🔤 Auto-detected text columns: {text_columns}")
        
        # Generate column suffix based on target language
        suffix = f"_{get_language_suffix(translator.target_lang)}"
        
        # Translate the file
        success = translator.translate_csv(
            input_file=str(input_file),
            output_file=str(output_file),
            columns_to_translate=text_columns,
            append_suffix=suffix,
            delimiter=delimiter
        )
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing CSV file {input_file}: {e}")
        return False

def process_single_file_mode(translator: CSVTranslator, user_input: Dict) -> bool:
    """Process a single file based on user selection."""
    selected_file = user_input['selected_file']
    output_file = user_input['output_file']
    
    print(f"📄 Processing: {selected_file.name}")
    print(f"💾 Output: {output_file}")
    
    if selected_file.suffix.lower() == '.csv':
        # For CSV, use the column and delimiter info from user input
        columns_to_translate = user_input['columns_to_translate']
        delimiter = user_input['delimiter']
        suffix = user_input['append_suffix']
        
        print(f"🔤 Translating columns: {columns_to_translate}")
        print(f"📄 Using delimiter: '{delimiter}'")
        
        success = translator.translate_csv(
            input_file=str(selected_file),
            output_file=str(output_file),
            columns_to_translate=columns_to_translate,
            append_suffix=suffix,
            delimiter=delimiter
        )
    elif selected_file.suffix.lower() == '.xml':
        print("🏷️  Processing XML file...")
        success = translator.translate_xml(str(selected_file), str(output_file))
    else:
        print(f"❌ Unsupported file type: {selected_file.suffix}")
        return False
    
    return success

def detect_csv_delimiter(file_path: str) -> str:
    """
    Auto-detect CSV delimiter by analyzing the first few lines.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Detected delimiter (comma or semicolon)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few lines to analyze
            sample_lines = []
            for i, line in enumerate(f):
                if i >= 3:  # Analyze first 3 lines
                    break
                sample_lines.append(line.strip())
        
        if not sample_lines:
            return ","  # Default to comma
        
        # Count commas and semicolons in the sample
        comma_count = sum(line.count(',') for line in sample_lines)
        semicolon_count = sum(line.count(';') for line in sample_lines)
        
        # Return the more frequent delimiter
        if semicolon_count > comma_count:
            logger.debug(f"Auto-detected semicolon delimiter (commas: {comma_count}, semicolons: {semicolon_count})")
            return ";"
        else:
            logger.debug(f"Auto-detected comma delimiter (commas: {comma_count}, semicolons: {semicolon_count})")
            return ","
            
    except Exception as e:
        logger.warning(f"Error detecting CSV delimiter: {e}. Using comma as default.")
        return ","

if __name__ == "__main__":
    main()