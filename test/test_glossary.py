#!/usr/bin/env python3
"""
Test script for glossary functionality.
"""

import pandas as pd
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def load_glossary():
    """Load the glossary CSV file for custom translation terms."""
    glossary = {}
    glossary_file = PROJECT_ROOT / "glossary.csv"
    
    if not glossary_file.exists():
        print("No glossary.csv file found.")
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
                print(f"Glossary line {line_num} has wrong format (expected 3 columns): {line}")
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
            print(f"Loaded {len(glossary)} terms from glossary.csv")
            for source, config in glossary.items():
                print(f"  {source} -> {config['target']} (keep_case: {config['keep_case']})")
        else:
            print("Glossary.csv file is empty or contains no valid entries")
            
    except Exception as e:
        print(f"Error loading glossary.csv: {e}")
    
    return glossary

def preserve_case(original, replacement):
    """Preserve the case pattern of the original word."""
    if original.isupper():
        return replacement.upper()
    elif original.islower():
        return replacement.lower()
    elif original.istitle():
        return replacement.capitalize()
    else:
        return replacement

def apply_glossary_replacements(text, glossary):
    """Apply glossary replacements to text."""
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
                # Preserve the case pattern of the original match
                return preserve_case(matched_text, target_term)
            else:
                # Use target term as-is
                return target_term
        
        result = pattern.sub(replace_match, result)
    
    return result

def test_glossary():
    """Test the glossary functionality."""
    print("=== Testing Glossary Functionality ===\n")
    
    # Load glossary
    glossary = load_glossary()
    
    # Test cases
    test_texts = [
        "Ajax is a powerful javascript library for API calls.",
        "The AJAX request uses JSON format for the API.",
        "Javascript and ajax work well together.",
        "This HTML page uses CSS styling and XML data."
    ]
    
    print("\n=== Test Results ===")
    for text in test_texts:
        processed = apply_glossary_replacements(text, glossary)
        print(f"Original:  {text}")
        print(f"Processed: {processed}")
        print()

if __name__ == "__main__":
    test_glossary()
