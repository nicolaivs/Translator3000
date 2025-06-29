"""
Modular CSVTranslator class for Translator3000.

This is the new modular implementation that uses the extracted processors
for better maintainability and performance.
"""

import logging
from typing import List

from .processors import CSVProcessor, XMLProcessor
from .config import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)


class CSVTranslator:
    """
    Modular CSV and XML translator using the new processor architecture.
    
    This class provides the same API as the legacy implementation but uses
    the new modular processors for better performance and maintainability.
    """
    
    def __init__(self, source_lang: str = 'en', target_lang: str = 'nl', delay_between_requests: float = None):
        """
        Initialize the translator with the specified languages.
        
        Args:
            source_lang: Source language code (e.g., 'en', 'da')
            target_lang: Target language code (e.g., 'nl', 'sv')
            delay_between_requests: Delay in seconds between translation requests
        """
        # Initialize the CSV processor which handles text translation
        self.csv_processor = CSVProcessor(source_lang, target_lang, delay_between_requests)
        
        # Initialize the XML processor with the CSV processor for text handling
        self.xml_processor = XMLProcessor(self.csv_processor)
        
        # Store language info for compatibility
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Backward compatibility: expose attributes from csv_processor
        self.translators = getattr(self.csv_processor, 'translators', [])
        self.delay = getattr(self.csv_processor, 'delay_between_requests', 0.05)
        self.delay_between_requests = getattr(self.csv_processor, 'delay_between_requests', 0.05)
        self.glossary = getattr(self.csv_processor, 'glossary', {})
        
        logger.info(f"Modular Translator initialized: {SUPPORTED_LANGUAGES[source_lang]} -> {SUPPORTED_LANGUAGES[target_lang]}")
    
    def translate_csv(self, 
                     input_file: str, 
                     output_file: str, 
                     columns_to_translate: List[str],
                     append_suffix: str = "_translated",
                     delimiter: str = ",") -> bool:
        """
        Translate specified columns in a CSV file.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            columns_to_translate: List of column names to translate
            append_suffix: Suffix to append to translated column names
            delimiter: CSV delimiter
            
        Returns:
            True if successful, False otherwise
        """
        return self.csv_processor.translate_csv(
            input_file, output_file, columns_to_translate, append_suffix, delimiter
        )
    
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
        return self.xml_processor.translate_xml(input_file, output_file, use_multithreading, max_workers)
    
    def translate_text(self, text: str) -> str:
        """
        Translate a single text string.
        
        Args:
            text: Text to translate
            
        Returns:
            Translated text
        """
        return self.csv_processor.translate_text(text)
    
    # Additional methods for compatibility with legacy API
    def translate_column(self, df, column: str):
        """Translate all texts in a DataFrame column."""
        return self.csv_processor.translate_column(df, column)
    
    def is_html_content(self, text: str) -> bool:
        """Check if text contains HTML tags."""
        return self.csv_processor.is_html_content(text)
    
    def translate_html_content(self, html_text: str) -> str:
        """Translate HTML content while preserving structure."""
        return self.csv_processor.translate_html_content(html_text)
