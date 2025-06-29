"""
Utility modules for Translator3000.

This package contains various utility functions for logging, file handling,
text processing, language handling, and other common operations.
"""

from .logging_utils import get_logger, setup_logging
from .language_utils import (
    get_language_suffix, get_language_name, generate_output_filename,
    generate_output_directory, get_language_preferences, SUPPORTED_LANGUAGES
)
from .file_utils import (
    discover_files_and_folders, print_discovered_files, ensure_directory_exists,
    is_supported_file, get_relative_path
)
from .text_utils import (
    is_html_content, load_glossary, apply_glossary_replacements,
    preserve_case, clean_text_for_translation, extract_translatable_content
)

__all__ = [
    'get_logger', 'setup_logging',
    'get_language_suffix', 'get_language_name', 'generate_output_filename',
    'generate_output_directory', 'get_language_preferences', 'SUPPORTED_LANGUAGES',
    'discover_files_and_folders', 'print_discovered_files', 'ensure_directory_exists',
    'is_supported_file', 'get_relative_path',
    'is_html_content', 'load_glossary', 'apply_glossary_replacements',
    'preserve_case', 'clean_text_for_translation', 'extract_translatable_content'
]
