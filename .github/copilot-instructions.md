<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# CSV Translation Project - Copilot Instructions

This is a Python project for translating CSV file columns and XML content between multiple languages using various translation APIs.

## Project Context
- Main entry point: `main.py` - entry point that calls the modular CLI
- CLI interface: `translator3000/cli.py` - interactive CLI with performance benchmarking
- Main orchestrator: `translator3000/translator.py` - handles translation coordination  
- Processors: `translator3000/processors/` - CSV and XML processing with accurate character counting
- Translation service priority: `deep-translator` (primary), `googletrans` (secondary), `LibreTranslate` (privacy fallback)
- Input files: CSV/XML files located in the `source/` folder
- Output files: Translated files saved in the `target/` folder
- Supports multiple languages and automatic column/element detection
- Designed for e-commerce product data and content translation
- Features real-time performance benchmarking and character counting

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
- Support batch processing for large CSV/XML files
- Preserve original data while adding translated columns/elements
- Provide accurate character counting for performance assessment
- Display real-time timing and benchmarking information

## Performance Features
- Real-time timing output (warmup, processing, total runtime)
- Accurate character counting (only actual translated text)
- Translation speed calculation (characters per second)
- Multithreading support for large files
- Configurable API delays and worker counts

## Dependencies
- pandas: For CSV file operations
- googletrans: For translation services  
- deep-translator: Primary translation service
- requests: For LibreTranslate API
- xml.etree.ElementTree: For XML processing
- concurrent.futures: For multithreading
- Standard library: logging, time, sys, os, typing
