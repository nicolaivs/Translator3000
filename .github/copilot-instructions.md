<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# CSV Translation Project - Copilot Instructions

This is a Python project for translating CSV file columns from English to Dutch using the Google Translate API.

## Project Context
- Main script: `main.py` - handles CSV file reading, translation, and writing
- Translation service: `googletrans` - provides access to Google Translate API
- Translation service priority: `deep-translator` (primary), `googletrans` (secondary), `LibreTranslate` (privacy fallback)
- Input files: CSV files located in the `source/` folder
- Output files: Translated CSV files saved in the `target/` folder
- Uses `googletrans` library for free Google Translate API access
- Uses `pandas` for CSV file manipulation
- Target translation: English -> Dutch (Netherlands)
- Designed for e-commerce product data translation

## Code Style Guidelines
- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Include comprehensive error handling and logging
- Add docstrings for all classes and methods
- Use descriptive variable names

## Translation Best Practices
- Implement rate limiting to avoid API throttling
- Handle translation failures gracefully by returning original text
- Log translation progress and errors
- Support batch processing for large CSV files
- Preserve original data while adding translated columns

## Dependencies
- pandas: For CSV file operations
- googletrans: For translation services
- Standard library: logging, time, sys, os, typing
