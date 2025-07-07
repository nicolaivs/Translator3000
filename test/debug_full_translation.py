#!/usr/bin/env python3
"""
Debug script to trace the full translation process for "KIT 4"
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from translator3000.translator import CSVTranslator
from translator3000.utils.text_utils import load_glossary, apply_glossary_replacements
from pathlib import Path

def test_full_translation():
    print("=== Full Translation Process Debug ===")
    
    # Initialize translator
    translator = CSVTranslator()
    
    # Load glossary
    glossary_path = Path("glossary.csv")
    glossary = load_glossary(glossary_path)
    print(f"Glossary for 'kit': {glossary.get('kit', 'Not found')}")
    
    # Test text
    test_text = "KIT 4"
    print(f"Original text: '{test_text}'")
    
    # Step 1: Apply glossary
    after_glossary = apply_glossary_replacements(test_text, glossary)
    print(f"After glossary: '{after_glossary}'")
    
    # Step 2: Test translation (using the translator's default target language)
    try:
        translated = translator.translate_text(after_glossary)
        print(f"After translation: '{translated}'")
    except Exception as e:
        print(f"Translation error: {e}")
        
    # Test some variations
    print("\n=== Testing variations ===")
    variations = ["KIT", "Kit", "kit", "KIT 4", "Kit 4", "kit 4"]
    for text in variations:
        after_glossary = apply_glossary_replacements(text, glossary)
        try:
            translated = translator.translate_text(after_glossary)
            print(f"'{text}' -> glossary: '{after_glossary}' -> translated: '{translated}'")
        except Exception as e:
            print(f"'{text}' -> error: {e}")

if __name__ == "__main__":
    test_full_translation()
