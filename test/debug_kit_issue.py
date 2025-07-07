#!/usr/bin/env python3
"""
Debug script to understand why "KIT 4" becomes "Kit 4"
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from translator3000.utils.text_utils import load_glossary, apply_glossary_replacements, preserve_case
import re

def test_kit_issue():
    print("=== Testing KIT 4 Issue ===")
    
    # Load the actual glossary
    from pathlib import Path
    glossary_path = Path("glossary.csv")
    glossary = load_glossary(glossary_path)
    print(f"Loaded glossary: {glossary}")
    
    # Test the specific case
    test_text = "KIT 4"
    print(f"Original text: '{test_text}'")
    
    result = apply_glossary_replacements(test_text, glossary)
    print(f"After glossary: '{result}'")
    
    # Test the preserve_case function directly
    print("\n=== Testing preserve_case function ===")
    print(f"preserve_case('KIT', 'KIT'): '{preserve_case('KIT', 'KIT')}'")
    print(f"'KIT'.isupper(): {'KIT'.isupper()}")
    print(f"'KIT'.islower(): {'KIT'.islower()}")
    print(f"'KIT'.istitle(): {'KIT'.istitle()}")
    
    # Test the regex pattern
    print("\n=== Testing regex pattern ===")
    pattern = re.compile(r'\b' + re.escape('KIT') + r'\b', re.IGNORECASE)
    matches = list(pattern.finditer("KIT 4"))
    print(f"Regex matches in 'KIT 4': {[(m.group(0), m.span()) for m in matches]}")
    
    # Step by step replacement
    print("\n=== Step by step replacement ===")
    for source_term, config in glossary.items():
        if source_term == 'kit':  # lowercase key
            print(f"Processing term: {source_term}")
            print(f"Config: {config}")
            
            target_term = config['target']
            keep_case = config['keep_case']
            
            # The pattern uses the source_term from glossary (lowercase)
            pattern = re.compile(r'\b' + re.escape(source_term) + r'\b', re.IGNORECASE)
            
            def replace_match(match):
                matched_text = match.group(0)
                print(f"  Match found: '{matched_text}'")
                
                if keep_case:
                    result = preserve_case(matched_text, target_term)
                    print(f"  preserve_case('{matched_text}', '{target_term}') = '{result}'")
                    return result
                else:
                    print(f"  Using target as-is: '{target_term}'")
                    return target_term
            
            result = pattern.sub(replace_match, "KIT 4")
            print(f"  Final result: '{result}'")

if __name__ == "__main__":
    test_kit_issue()
