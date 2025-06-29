"""
Language utility functions for Translator3000.

This module contains helper functions for language handling, naming conventions,
and file path generation.
"""

from typing import Dict
from pathlib import Path

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    'da': 'Danish',
    'nl': 'Dutch (Netherlands)', 
    'nl-be': 'Dutch (Flemish)',
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'no': 'Norwegian (Bokmål)',
    'es': 'Spanish',
    'sv': 'Swedish'
}


def get_language_suffix(lang_code: str) -> str:
    """Generate a column suffix based on language code in brackets format."""
    # Create a mapping for language codes in brackets
    suffix_mapping = {
        'da': '_[DA]',
        'nl': '_[NL]',
        'nl-be': '_[NL-BE]',
        'en': '_[EN]',
        'fr': '_[FR]',
        'de': '_[DE]',
        'it': '_[IT]',
        'no': '_[NO]',
        'es': '_[ES]',
        'sv': '_[SV]'
    }
    return suffix_mapping.get(lang_code, f'_[{lang_code.upper()}]')


def get_language_name(lang_code: str) -> str:
    """Get the full language name for a language code."""
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code)


def generate_output_filename(input_filename: str, lang_code: str, is_root_file: bool = True) -> str:
    """
    Generate output filename based on location and language.
    
    Args:
        input_filename: Original filename with extension
        lang_code: Target language code (e.g., 'sv', 'da')
        is_root_file: True if processing root file, False if in subfolder
        
    Returns:
        New filename with language suffix
    """
    path = Path(input_filename)
    stem = path.stem
    extension = path.suffix
    
    if is_root_file:
        # For root files: "filename - Language.ext"
        language_name = get_language_name(lang_code)
        return f"{stem} - {language_name}{extension}"
    else:
        # For batch subfolder files: keep original name
        return input_filename


def generate_output_directory(base_dir: Path, folder_name: str, lang_code: str, is_batch_folder: bool = False) -> Path:
    """
    Generate output directory path based on processing mode.
    
    Args:
        base_dir: Base target directory
        folder_name: Name of the source folder (or 'root')
        lang_code: Target language code
        is_batch_folder: True if processing a batch folder (not root)
        
    Returns:
        Target directory path
    """
    if folder_name == 'root' or not is_batch_folder:
        # For root files, use base target directory
        return base_dir
    else:
        # For batch folders: "foldername - Language"
        language_name = get_language_name(lang_code)
        return base_dir / f"{folder_name} - {language_name}"


def get_language_preferences() -> Dict[str, str]:
    """Get source and target language preferences from user."""
    print("=== Language Configuration ===")
    
    # Source language selection
    print("\nSelect source language (language of your CSV content):")
    print("  1. English (default)")
    print("  2. Danish")
    source_choice = input("Enter choice (1 or 2, default: 1): ").strip()
    
    if source_choice == "2":
        source_lang = "da"
        print("Selected: Danish")
    else:
        source_lang = "en"
        print("Selected: English")
    
    # Target language selection
    print(f"\nSelect target language (translate TO):")
    lang_options = [
        ('da', 'Danish'),
        ('nl', 'Dutch (Netherlands)'),
        ('nl-be', 'Dutch (Flemish)'),
        ('en', 'English'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('no', 'Norwegian (Bokmål)'),
        ('es', 'Spanish'),
        ('sv', 'Swedish')
    ]
    
    for i, (code, name) in enumerate(lang_options, 1):
        print(f"  {i}. {name} ({code})")
    
    while True:
        try:
            target_choice = input("Enter choice (1-10): ")

            # Check for empty input and set default
            if target_choice.strip() == "":
                target_choice = "1"
                print("No choice entered, defaulting to 1. English (en)")
            
            choice_idx = int(target_choice) - 1
            if 0 <= choice_idx < len(lang_options):
                target_lang, target_name = lang_options[choice_idx]
                print(f"Selected: {target_name}")
                break
            else:
                print("Invalid choice! Please enter a number between 1-10.")
        except ValueError:
            print("Invalid input! Please enter a number.")
    
    # Validate different languages
    if source_lang == target_lang:
        print("⚠️  Warning: Source and target languages are the same!")
        confirm = input("Do you want to continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return {}
    
    return {
        'source_lang': source_lang,
        'target_lang': target_lang,
        'source_name': SUPPORTED_LANGUAGES[source_lang],
        'target_name': SUPPORTED_LANGUAGES[target_lang]
    }
