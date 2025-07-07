"""
Text processing utilities for Translator3000.

This module contains helper functions for text processing, HTML detection,
glossary handling, and case preservation.
"""

import re
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def is_html_content(text: str) -> bool:
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


def load_glossary(glossary_file_path: Path) -> Dict[str, Dict[str, str]]:
    """
    Load the glossary CSV file for custom translation terms.
    
    Args:
        glossary_file_path: Path to the glossary.csv file
    
    Returns:
        Dictionary mapping source terms to target terms and case preferences
    """
    glossary = {}
    
    if not glossary_file_path.exists():
        logger.info(f"No glossary file found at {glossary_file_path}. Using translation API only.")
        return glossary
    
    try:
        # Read the glossary CSV
        with open(glossary_file_path, 'r', encoding='utf-8') as f:
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
            logger.info(f"Loaded {len(glossary)} terms from {glossary_file_path}")
        else:
            logger.info(f"Glossary file {glossary_file_path} is empty or contains no valid entries")
            
    except Exception as e:
        logger.warning(f"Error loading glossary from {glossary_file_path}: {e}")
    
    return glossary


def apply_glossary_replacements(text: str, glossary: Dict[str, Dict[str, str]]) -> str:
    """
    Apply glossary replacements to text before translation.
    
    Args:
        text: Text to process
        glossary: Glossary dictionary from load_glossary()
        
    Returns:
        Text with glossary terms replaced
    """
    if not glossary:
        return text
    
    result = text
    
    for source_term, config in glossary.items():
        target_term = config['target']
        keep_case = config['keep_case']
        
        # Create case-insensitive pattern for whole words
        pattern = re.compile(r'\b' + re.escape(source_term) + r'\b', re.IGNORECASE)
        
        def replace_match(match):
            matched_text = match.group(0)
            
            if keep_case:
                # For keep_case=True, use the target term exactly as specified in glossary
                return target_term
            else:
                # For keep_case=False, adapt target case to match the original text
                return preserve_case(matched_text, target_term)
        
        result = pattern.sub(replace_match, result)
    
    return result


def preserve_case(original: str, replacement: str) -> str:
    """
    Preserve the case pattern of the original word when applying replacement.
    
    Args:
        original: Original text with case pattern to preserve
        replacement: New text to apply case pattern to
        
    Returns:
        Replacement text with preserved case pattern
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


def clean_text_for_translation(text: str) -> str:
    """
    Clean text for better translation quality.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text or not isinstance(text, str):
        return text
    
    # Remove extra whitespace but preserve structure
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text


def extract_translatable_content(text: str) -> Optional[str]:
    """
    Extract content that should be translated from a text string.
    
    Args:
        text: Input text
        
    Returns:
        Translatable content or None if nothing to translate
    """
    if not text or not isinstance(text, str):
        return None
    
    # Remove only whitespace strings
    cleaned = text.strip()
    if not cleaned:
        return None
    
    # Skip very short strings that are likely codes/IDs
    if len(cleaned) < 2:
        return None
    
    # Skip strings that are mostly numbers
    if re.match(r'^[\d\s\-\.\,\(\)]+$', cleaned):
        return None
    
    return cleaned
