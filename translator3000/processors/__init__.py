"""
Processing modules for Translator3000.

This package contains the CSV and XML processing logic extracted from
the legacy monolithic file for better maintainability and performance.
"""

from .csv_processor import CSVProcessor
from .xml_processor import XMLProcessor

__all__ = ['CSVProcessor', 'XMLProcessor']
