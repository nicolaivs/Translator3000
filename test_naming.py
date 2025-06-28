#!/usr/bin/env python3
"""
Test the new filename and directory naming conventions.
"""

import sys
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

from translator3000 import generate_output_filename, generate_output_directory, get_language_name

def test_naming_conventions():
    """Test the new naming conventions for files and directories."""
    
    print("=== Testing New Naming Conventions ===\n")
    
    # Test cases for different language codes
    test_languages = ['sv', 'da', 'nl', 'de', 'fr']
    test_files = ['products.csv', 'inventory.xml', 'catalog.csv']
    
    print("1. Root File Naming (filename - Language.ext):")
    print("-" * 50)
    for lang in test_languages:
        lang_name = get_language_name(lang)
        print(f"Language: {lang} ({lang_name})")
        for filename in test_files:
            new_name = generate_output_filename(filename, lang, is_root_file=True)
            print(f"  {filename} -> {new_name}")
        print()
    
    print("2. Batch Subfolder Naming (keep original filename):")
    print("-" * 50)
    for lang in test_languages:
        for filename in test_files:
            new_name = generate_output_filename(filename, lang, is_root_file=False)
            print(f"  {filename} -> {new_name}")
        break  # Same for all languages
    print()
    
    print("3. Target Directory Naming:")
    print("-" * 50)
    base_dir = Path("target")
    
    # Root files (no change to directory)
    print("Root files:")
    for lang in test_languages:
        target_dir = generate_output_directory(base_dir, 'root', lang, is_batch_folder=False)
        print(f"  Language {lang}: {target_dir}")
    print()
    
    # Batch folders (add language suffix)
    print("Batch folders:")
    test_folders = ['products', 'categories', 'suppliers']
    for folder in test_folders:
        for lang in test_languages:
            lang_name = get_language_name(lang)
            target_dir = generate_output_directory(base_dir, folder, lang, is_batch_folder=True)
            print(f"  {folder} -> {lang} ({lang_name}): {target_dir}")
        print()

if __name__ == "__main__":
    test_naming_conventions()
