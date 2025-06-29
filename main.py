#!/usr/bin/env python3
"""
Translator3000 - Multi-Language CSV & XML Translation Script
===========================================================

Main entry point for the Translator3000 application.

This script translates CSV file columns and XML text content between multiple languages
using multiple translation services with automatic fallback.

Usage:
    python main.py

For the modular API:
    from translator3000 import CSVTranslator
    translator = CSVTranslator('en', 'da')
    translator.translate_csv('input.csv', 'output.csv')

Author: Generated for CSV Translation Project  
Date: June 2025
"""

# Use the new modular structure
from translator3000 import main

if __name__ == "__main__":
    main()
