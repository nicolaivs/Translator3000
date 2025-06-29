#!/usr/bin/env python3
"""
Quick test to verify glossary behavior with company name capitalization.
"""

import sys
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000 import CSVTranslator

def test_company_name():
    """Test that company names are handled correctly with glossary."""
    
    # Create translator instance
    translator = CSVTranslator(source_lang='en', target_lang='da')
    
    # Test multiple cases where company name might get capitalized
    test_cases = [
        "ajax provides excellent service",
        "We work with ajax company",
        "ajax is a great company",  # Already capitalized
        "The ajax team is professional"
    ]
    
    print("=== Company Name Capitalization Test ===")
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_text}'")
        
        # Test direct glossary application (access through csv_processor)
        if hasattr(translator.csv_processor, '_apply_glossary_replacements'):
            glossary_applied = translator.csv_processor._apply_glossary_replacements(test_text)
            print(f"  After glossary: '{glossary_applied}'")
        else:
            print(f"  Glossary functionality not available in modular version")
        
        # Test full translation (includes before + translation + after glossary)
        translated = translator.translate_text(test_text)
        print(f"  Full translation: '{translated}'")
        
        # Check if ajax stayed lowercase
        import re
        ajax_matches = re.findall(r'\bajax\b', translated, re.IGNORECASE)
        if ajax_matches:
            actual_case = ajax_matches[0]
            if actual_case == 'ajax':
                print(f"  ✓ SUCCESS: 'ajax' remained lowercase")
            else:
                print(f"  ✗ ISSUE: 'ajax' was changed to '{actual_case}'")
        else:
            print(f"  ? No 'ajax' found in result")
    
    print(f"\nGlossary contains {len(translator.glossary)} terms:")
    for source, config in translator.glossary.items():
        print(f"  '{source}' -> '{config['target']}' (keep_case: {config['keep_case']})")

if __name__ == "__main__":
    test_company_name()
