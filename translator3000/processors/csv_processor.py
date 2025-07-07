"""
CSV processing module for Translator3000.

This module handles CSV file translation with support for multiple columns,
HTML content detection, and glossary replacements.
"""

import pandas as pd
import logging
import re
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..config import get_config, SUPPORTED_LANGUAGES
from ..services import LibreTranslateService, DeepTranslatorService, GoogleTransService
from ..services.libre_translate import is_libretranslate_selfhost_available

# Try to import BeautifulSoup for HTML processing
try:
    from bs4 import BeautifulSoup
    HTML_PARSER_AVAILABLE = True
except ImportError:
    HTML_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Handles CSV file translation with multiple translation services."""
    
    def __init__(self, source_lang: str = 'en', target_lang: str = 'nl', delay_between_requests: float = None):
        """
        Initialize the CSV processor with translation services.
        
        Args:
            source_lang: Source language code (e.g., 'en', 'da')
            target_lang: Target language code (e.g., 'nl', 'sv')
            delay_between_requests: Delay in seconds between translation requests
        """
        config = get_config()
        
        # Validate language codes
        if source_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: {source_lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")
        if target_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language: {target_lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")
        
        # Use config delay if not explicitly provided (convert from ms to seconds)
        if delay_between_requests is None:
            self.delay = config['delay'] / 1000.0  # Convert ms to seconds
        else:
            self.delay = delay_between_requests
        
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        logger.info(f"CSV Processor configured: {SUPPORTED_LANGUAGES[source_lang]} -> {SUPPORTED_LANGUAGES[target_lang]}")
        logger.info(f"Request delay: {self.delay*1000:.1f}ms between requests")
        
        # Initialize translation services
        self.translators = []
        self._initialize_translators()
        
        # Load glossary
        self.glossary = self._load_glossary()
    
    def _initialize_translators(self):
        """Initialize available translation services in order of preference."""
        config = get_config()
        services = config.get('translation_services', 'deep_translator,googletrans,libretranslate').split(',')
        
        for service in [s.strip() for s in services]:
            try:
                if service == 'libretranslate':
                    # Choose URL based on selfhost availability
                    if is_libretranslate_selfhost_available():
                        api_url = config['libretranslate_selfhost_url']
                        logger.info("🚀 Using self-hosted LibreTranslate instance for optimal performance")
                    else:
                        api_url = config['libretranslate_url']
                        logger.info("Using remote LibreTranslate service")
                    
                    translator = LibreTranslateService(
                        source_lang=self.source_lang,
                        target_lang=self.target_lang,
                        api_url=api_url,
                        api_key=config['libretranslate_api_key']
                    )
                    self.translators.append(('libretranslate', translator))
                    logger.info(f"✓ LibreTranslate service initialized")
                
                elif service == 'deep_translator':
                    try:
                        from deep_translator import GoogleTranslator
                        translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)
                        self.translators.append(('deep_translator', translator))
                        logger.info(f"✓ deep-translator service initialized")
                    except ImportError:
                        logger.warning("deep-translator not available")
                
                elif service == 'googletrans':
                    translator = GoogleTransService(self.source_lang, self.target_lang)
                    self.translators.append(('googletrans', translator))
                    logger.info(f"✓ googletrans service initialized")
                    
            except Exception as e:
                logger.warning(f"Failed to initialize {service}: {e}")
        
        if not self.translators:
            raise ImportError("No translation services could be initialized")
        
        logger.info(f"Active translation services: {[name for name, _ in self.translators]}")
    
    def _load_glossary(self) -> Dict[str, Dict[str, str]]:
        """Load glossary for custom translations with case preservation support."""
        config = get_config()
        # Look for glossary.csv in the project root directory
        project_root = Path(__file__).parent.parent.parent
        glossary_file = project_root / "glossary.csv"
        
        glossary = {}
        if glossary_file.exists():
            try:
                # Try to read with semicolon delimiter first (original format)
                df = pd.read_csv(glossary_file, encoding='utf-8', sep=';', comment='#')
                
                # Check for standard format columns (source, target, keep_case)
                if 'source' in df.columns and 'target' in df.columns:
                    # Use the standard format
                    for _, row in df.iterrows():
                        source = str(row['source']).strip()
                        target = str(row['target']).strip()
                        keep_case = str(row.get('keep_case', 'False')).strip().lower() == 'true'
                        
                        if source and target:
                            # Store both original case and lowercase for lookup
                            glossary[source.lower()] = {
                                'target': target,
                                'keep_case': keep_case,
                                'original_source': source
                            }
                    logger.info(f"Loaded {len(glossary)} terms from glossary.csv")
                
                # Check for alternative format columns (original, translation)
                elif 'original' in df.columns and 'translation' in df.columns:
                    for _, row in df.iterrows():
                        original = str(row['original']).strip()
                        translation = str(row['translation']).strip()
                        if original and translation:
                            glossary[original.lower()] = {
                                'target': translation,
                                'keep_case': False,  # Default for old format
                                'original_source': original
                            }
                    logger.info(f"Loaded {len(glossary)} terms from glossary.csv (alternative format)")
                
                else:
                    logger.warning("Glossary file missing required columns: either 'source,target' or 'original,translation'")
                    
            except Exception as e:
                logger.warning(f"Error loading glossary: {e}")
        else:
            logger.info("No glossary.csv found - proceeding without custom terms")
        
        return glossary
    
    def translate_csv(self, 
                     input_file: str, 
                     output_file: str, 
                     columns_to_translate: List[str],
                     append_suffix: str = "_translated",
                     delimiter: str = ",") -> tuple[bool, int]:
        """
        Translate specified columns in a CSV file.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            columns_to_translate: List of column names to translate
            append_suffix: Suffix to append to translated column names
            delimiter: CSV delimiter
            
        Returns:
            Tuple of (success, characters_translated)
        """
        try:
            # Read the CSV file
            logger.info(f"Reading CSV file: {input_file} (delimiter: '{delimiter}')")
            df = pd.read_csv(input_file, encoding='utf-8', delimiter=delimiter)
            logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            
            # Validate columns exist
            missing_columns = [col for col in columns_to_translate if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing columns: {missing_columns}")
                return False, 0
            
            # Create result DataFrame
            result_df = df.copy()
            total_characters_translated = 0
            
            # Translate each specified column
            for column in columns_to_translate:
                logger.info(f"Starting translation of column: {column}")
                translated_column, column_chars = self.translate_column(df, column)
                total_characters_translated += column_chars
                
                # Add translated column with suffix
                new_column_name = f"{column}{append_suffix}"
                result_df[new_column_name] = translated_column
            
            # Save the result
            logger.info(f"Saving translated CSV to: {output_file} (delimiter: '{delimiter}')")
            result_df.to_csv(output_file, index=False, encoding='utf-8', sep=delimiter)
            
            logger.info("Translation completed successfully!")
            logger.info(f"Original columns: {len(df.columns)}")
            logger.info(f"Final columns: {len(result_df.columns)}")
            logger.info(f"Characters translated: {total_characters_translated}")
            
            return True, total_characters_translated
            
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            return False, 0
        except Exception as e:
            logger.error(f"Error during translation: {e}")
            return False, 0
    
    def translate_column(self, df: pd.DataFrame, column: str) -> tuple[List[str], int]:
        """Translate all texts in a DataFrame column."""
        translated_texts = []
        total_chars = 0
        
        for i, text in enumerate(df[column]):
            try:
                # Count characters of original text
                if text and not pd.isna(text):
                    total_chars += len(str(text))
                
                translated = self.translate_text(text)
                translated_texts.append(translated)
                
                # Add delay between requests
                if i < len(df) - 1:  # Don't delay after the last request
                    time.sleep(self.delay)
                    
            except Exception as e:
                logger.warning(f"Translation failed for row {i}: {e}")
                translated_texts.append(text)  # Use original text if translation fails
        
        return translated_texts, total_chars
    
    def translate_text(self, text: str) -> str:
        """Translate a single text string with HTML awareness and glossary support."""
        if not text or pd.isna(text):
            return text
            
        try:
            text_str = str(text).strip()
            if not text_str:
                return text
            
            # Apply glossary replacements before translation
            text_with_glossary = self._apply_glossary_replacements(text_str)
            
            # Check if content contains HTML
            if self.is_html_content(text_with_glossary):
                logger.debug(f"Detected HTML content, using HTML-aware translation")
                translated = self.translate_html_content(text_with_glossary)
            else:
                translated = self._translate_plain_text(text_with_glossary)
            
            # Apply glossary replacements after translation
            final_result = self._apply_glossary_replacements(translated)
                
            logger.debug(f"Translated: '{text_str[:50]}...' -> '{final_result[:50]}...'")
            return final_result
            
        except Exception as e:
            logger.warning(f"Translation failed for '{text}': {e}")
            return text
    
    def _translate_plain_text(self, text: str) -> str:
        """Translate plain text using available services with fallback."""
        import time
        
        for service_name, translator in self.translators:
            try:
                if service_name == 'libretranslate':
                    result = translator.translate(text)
                elif service_name == 'deep_translator':
                    result = translator.translate(text)
                elif service_name == 'googletrans':
                    result = translator.translate(text)
                
                if result and result.strip():
                    return result
                    
            except Exception as e:
                logger.warning(f"{service_name} failed: {e}")
                continue
        
        logger.warning(f"All translation services failed for: {text[:50]}...")
        return text
    
    def is_html_content(self, text: str) -> bool:
        """Check if text contains HTML tags."""
        if not text:
            return False
        html_pattern = re.compile(r'<[^>]+>')
        return bool(html_pattern.search(str(text)))
    
    def translate_html_content(self, html_text: str) -> str:
        """Translate HTML content while preserving structure."""
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
        """Translate HTML using BeautifulSoup with improved space preservation."""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            
            for text_node in soup.find_all(string=True):
                if text_node.parent.name not in ['script', 'style', 'meta', 'title']:
                    original_text = text_node.string
                    text_content = original_text.strip()
                    
                    if text_content and len(text_content) > 1:
                        # Check if this text node or any parent has ignore attribute
                        should_ignore = False
                        current = text_node.parent
                        
                        while current and hasattr(current, 'get'):
                            # Check for ignore attribute (case-insensitive)
                            ignore_value = current.get('ignore', '') or current.get('Ignore', '')
                            if ignore_value.lower() == 'true':
                                should_ignore = True
                                break
                            current = current.parent if hasattr(current, 'parent') else None
                        
                        if should_ignore:
                            continue  # Skip translation for ignored elements
                        
                        translated = self._translate_plain_text(text_content)
                        if translated and translated != text_content:
                            # IMPROVED: Preserve surrounding whitespace more accurately
                            leading_space = ''
                            trailing_space = ''
                            
                            # Extract leading whitespace - find where content starts
                            content_start = original_text.find(text_content)
                            if content_start > 0:
                                leading_space = original_text[:content_start]
                            
                            # Extract trailing whitespace - find where content ends
                            content_end = content_start + len(text_content)
                            if content_end < len(original_text):
                                trailing_space = original_text[content_end:]
                            
                            # Replace with translated text preserving exact whitespace
                            new_text = leading_space + translated + trailing_space
                            text_node.replace_with(new_text)
            
            return str(soup)
            
        except Exception as e:
            logger.warning(f"BeautifulSoup HTML translation failed: {e}")
            return self._translate_html_with_regex(html_text)
    
    def _translate_html_with_regex(self, html_text: str) -> str:
        """Translate HTML using regex (fallback method)."""
        try:
            def translate_match(match):
                text_content = match.group(1).strip()
                if text_content and len(text_content) > 1:
                    return self._translate_plain_text(text_content)
                return text_content
            
            # Simple regex to find text between tags
            text_pattern = re.compile(r'>([^<]+)<')
            translated_html = text_pattern.sub(lambda m: f'>{translate_match(m)}<', html_text)
            
            return translated_html
            
        except Exception as e:
            logger.warning(f"Regex HTML translation failed: {e}")
            return html_text
    
    def _apply_glossary_replacements(self, text: str) -> str:
        """Apply glossary term replacements with proper case preservation."""
        if not self.glossary or not text:
            return text
        
        result = text
        
        # Apply replacements for each glossary term
        for source_key, glossary_info in self.glossary.items():
            target = glossary_info['target']
            keep_case = glossary_info['keep_case']
            original_source = glossary_info['original_source']
            
            if keep_case:
                # For keep_case=True, always use the target exactly as specified in glossary
                # Use regex with word boundaries for accurate matching
                pattern = re.compile(r'\b' + re.escape(original_source) + r'\b', re.IGNORECASE)
                result = pattern.sub(target, result)
            else:
                # Case-insensitive replacement - replace with exact target
                # Use regex for case-insensitive replacement
                pattern = re.compile(re.escape(original_source), re.IGNORECASE)
                result = pattern.sub(target, result)
        
        return result
