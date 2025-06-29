"""
Command Line Interface for Translator3000
==========================================

Interactive CLI for the Translator3000 translation package.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

from .translator import CSVTranslator
from .config import load_config, SOURCE_DIR, TARGET_DIR
from .utils.logging_utils import setup_logging, get_logger
from .utils.language_utils import get_language_suffix

# Set up logging
logger = get_logger(__name__)

# Import modular components
from .utils.file_utils import discover_files_and_folders, print_discovered_files
from .utils.language_utils import get_language_name, SUPPORTED_LANGUAGES


def main():
    """Main interactive workflow for the translation script."""
    try:
        print("=" * 60)
        print("🌍 Translator3000 - Multi-Language CSV & XML Translation")
        print("=" * 60)
        print()
        
        # Ensure source and target directories exist
        SOURCE_DIR.mkdir(exist_ok=True)
        TARGET_DIR.mkdir(exist_ok=True)
        
        # Get user input for batch processing (which includes language and file selection)
        user_input = get_batch_processing_input()
        
        if not user_input:
            print("❌ Translation cancelled or no valid input provided.")
            return
        
        # Create translator with selected languages (using config defaults)
        translator = CSVTranslator(
            source_lang=user_input['source_lang'],
            target_lang=user_input['target_lang']
            # delay_between_requests will use config file value automatically
        )
        
        print(f"\n🔧 Translator initialized: {user_input['source_name']} -> {user_input['target_name']}")
        
        # Process based on mode
        if user_input['mode'] == 'batch':
            print("\n🚀 Starting batch processing...")
            success = process_batch_mode(translator, user_input)
        else:
            print("\n🚀 Starting single file processing...")
            success = process_single_file_mode(translator, user_input)
        
        if success:
            print("\n✅ Translation completed successfully!")
            print(f"📁 Check the output files in: {TARGET_DIR}")
        else:
            print("\n❌ Translation completed with some errors.")
            print("📋 Check translation.log for details.")
            
    except KeyboardInterrupt:
        print("\n❌ Translation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error in main workflow: {e}")
        print(f"\n❌ An unexpected error occurred: {e}")
        print("📋 Check translation.log for details.")


def process_batch_mode(translator: CSVTranslator, user_input: Dict) -> bool:
    """Process files in batch mode."""
    discovered = user_input['discovered']
    folder_choice = user_input['folder_choice']
    target_lang = user_input['target_lang']
    
    # Determine which files to process
    files_to_process = []
    
    if folder_choice['type'] == 'root':
        files_to_process = [(f, 'root') for f in discovered['root_files']]
    elif folder_choice['type'] == 'folder':
        folder_name = folder_choice['folder_name']
        files_to_process = [(f, folder_name) for f in discovered['folders'][folder_name]]
    elif folder_choice['type'] == 'all':
        # Add root files
        files_to_process.extend([(f, 'root') for f in discovered['root_files']])
        # Add folder files
        for folder_name, files in discovered['folders'].items():
            files_to_process.extend([(f, folder_name) for f in files])
    
    success_count = 0
    total_files = len(files_to_process)
    
    print(f"\n📊 Processing {total_files} files...")
    
    for idx, (file_path, location) in enumerate(files_to_process, 1):
        print(f"\n[{idx}/{total_files}] Processing: {file_path.name}")
        
        # Generate output directory and filename
        if location == 'root':
            output_dir = TARGET_DIR
            output_filename = generate_output_filename(file_path.name, target_lang, is_root_file=True)
        else:
            output_dir = generate_output_directory(TARGET_DIR, location, target_lang, is_batch_folder=True)
            output_filename = generate_output_filename(file_path.name, target_lang, is_root_file=False)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / output_filename
        
        # Process file based on type
        success = False
        if file_path.suffix.lower() == '.csv':
            success = process_csv_file_batch(translator, file_path, output_file)
        elif file_path.suffix.lower() == '.xml':
            success = translator.translate_xml(str(file_path), str(output_file))
        
        if success:
            success_count += 1
            print(f"✅ {file_path.name} -> {output_filename}")
        else:
            print(f"❌ Failed to process {file_path.name}")
    
    print(f"\n📊 Batch processing complete: {success_count}/{total_files} files processed successfully")
    return success_count > 0


def process_csv_file_batch(translator: CSVTranslator, input_file: Path, output_file: Path) -> bool:
    """Process a single CSV file in batch mode with automatic column detection."""
    try:
        import pandas as pd
        
        # Auto-detect delimiter
        delimiter = detect_csv_delimiter(str(input_file))
        print(f"  📄 Detected delimiter: '{delimiter}'")
        
        # Read CSV to analyze columns
        df = pd.read_csv(input_file, nrows=5, delimiter=delimiter)
        
        # Auto-detect text columns (columns likely to contain translatable text)
        text_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':  # Text columns
                # Check if column contains substantial text (not just codes/IDs)
                sample_text = df[col].dropna().astype(str).iloc[0] if not df[col].dropna().empty else ""
                if len(sample_text) > 10:  # Likely to be translatable text
                    text_columns.append(col)
        
        if not text_columns:
            print(f"  ⚠️  No suitable text columns found for translation")
            return False
        
        print(f"  🔤 Auto-detected text columns: {text_columns}")
        
        # Generate column suffix based on target language
        suffix = f"_{get_language_suffix(translator.target_lang)}"
        
        # Translate the file
        success = translator.translate_csv(
            input_file=str(input_file),
            output_file=str(output_file),
            columns_to_translate=text_columns,
            append_suffix=suffix,
            delimiter=delimiter
        )
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing CSV file {input_file}: {e}")
        return False


def process_single_file_mode(translator: CSVTranslator, user_input: Dict) -> bool:
    """Process a single file based on user selection."""
    selected_file = user_input['selected_file']
    output_file = user_input['output_file']
    
    print(f"📄 Processing: {selected_file.name}")
    print(f"💾 Output: {output_file}")
    
    if selected_file.suffix.lower() == '.csv':
        # For CSV, use the column and delimiter info from user input
        columns_to_translate = user_input['columns_to_translate']
        delimiter = user_input['delimiter']
        suffix = user_input['append_suffix']
        
        print(f"🔤 Translating columns: {columns_to_translate}")
        print(f"📄 Using delimiter: '{delimiter}'")
        
        success = translator.translate_csv(
            input_file=str(selected_file),
            output_file=str(output_file),
            columns_to_translate=columns_to_translate,
            append_suffix=suffix,
            delimiter=delimiter
        )
    elif selected_file.suffix.lower() == '.xml':
        print("🏷️  Processing XML file...")
        success = translator.translate_xml(str(selected_file), str(output_file))
    else:
        print(f"❌ Unsupported file type: {selected_file.suffix}")
        return False
    
    return success


def detect_csv_delimiter(file_path: str) -> str:
    """
    Auto-detect CSV delimiter by analyzing the first few lines.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Detected delimiter (comma or semicolon)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few lines to analyze
            sample_lines = []
            for i, line in enumerate(f):
                if i >= 3:  # Analyze first 3 lines
                    break
                sample_lines.append(line.strip())
        
        if not sample_lines:
            return ","  # Default to comma
        
        # Count commas and semicolons in the sample
        comma_count = sum(line.count(',') for line in sample_lines)
        semicolon_count = sum(line.count(';') for line in sample_lines)
        
        # Return the more frequent delimiter
        if semicolon_count > comma_count:
            logger.debug(f"Auto-detected semicolon delimiter (commas: {comma_count}, semicolons: {semicolon_count})")
            return ";"
        else:
            logger.debug(f"Auto-detected comma delimiter (commas: {comma_count}, semicolons: {semicolon_count})")
            return ","
            
    except Exception as e:
        logger.warning(f"Error detecting CSV delimiter: {e}. Using comma as default.")
        return ","

# CLI helper functions using modular components

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


def get_batch_processing_input() -> Dict[str, any]:
    """Get user input for batch processing mode."""
    # Get language preferences first
    lang_prefs = get_language_preferences()
    if not lang_prefs:
        return {}
    
    print(f"\n=== Batch CSV & XML Translation Script ===")
    print(f"Translation: {lang_prefs['source_name']} -> {lang_prefs['target_name']}")
    print(f"Source files will be scanned from: {SOURCE_DIR}")
    print(f"Translated files will be saved to: {TARGET_DIR}")
    print()
    
    # Discover all files
    discovered = discover_files_and_folders(SOURCE_DIR)
    total_files = print_discovered_files(discovered, SOURCE_DIR)
    
    if total_files == 0:
        print(f"No CSV or XML files found in {SOURCE_DIR} or its subdirectories.")
        print("Please place your files in the 'source' folder and try again.")
        return {}
    
    print(f"[TOTAL] Total files found: {total_files}")
    print()
    
    # Ask user about processing mode
    print("Choose processing mode:")
    print("  1. Single file mode (original behavior)")
    print("  2. Batch mode (process all discovered files)")
    
    mode_choice = input("Enter choice (1 or 2, default: 1): ").strip()
    if mode_choice == "2":
        # Batch mode - allow folder selection
        folder_choice = get_batch_folder_selection(discovered)
        if not folder_choice:
            return {}
        
        print(f"\n[BATCH] Batch mode selected!")
        
        # Calculate files to process based on selection
        if folder_choice['type'] == 'root':
            files_to_process = len(discovered['root_files'])
            print(f"Processing {files_to_process} files from root directory.")
        elif folder_choice['type'] == 'folder':
            files_to_process = len(discovered['folders'][folder_choice['folder_name']])
            print(f"Processing {files_to_process} files from folder: {folder_choice['folder_name']}")
        elif folder_choice['type'] == 'all':
            files_to_process = total_files
            print(f"Processing all {files_to_process} files from all locations.")
        
        # For batch mode, we need to handle CSV column selection differently
        if any(f.suffix.lower() == '.csv' for f in discovered['root_files']) or \
           any(any(f.suffix.lower() == '.csv' for f in files) for files in discovered['folders'].values()):
            print("\n[CSV] CSV Column Selection:")
            print("Since multiple CSV files may have different structures,")
            print("you'll be prompted for column selection for each CSV file during processing.")
        
        return {
            'mode': 'batch',
            'discovered': discovered,
            'folder_choice': folder_choice,
            'source_lang': lang_prefs['source_lang'],
            'target_lang': lang_prefs['target_lang'],
            'source_name': lang_prefs['source_name'],
            'target_name': lang_prefs['target_name']
        }
    else:
        # Single file mode - use original logic
        return get_single_file_input(discovered, lang_prefs)


def get_batch_folder_selection(discovered: Dict[str, List[Path]]) -> Dict[str, any]:
    """Get user selection for which folders to process in batch mode."""
    print("\nBatch folder selection:")
    
    options = []
    
    # Option 1: Root files only
    if discovered['root_files']:
        root_count = len(discovered['root_files'])
        options.append(('root', f"Process root directory only ({root_count} files)"))
    
    # Option 2: Individual folders
    for folder_name, files in discovered['folders'].items():
        file_count = len(files)
        options.append(('folder', f"Process '{folder_name}' folder only ({file_count} files)", folder_name))
    
    # Option 3: All files
    total_files = len(discovered['root_files']) + sum(len(files) for files in discovered['folders'].values())
    options.append(('all', f"Process all files and folders ({total_files} files)"))
    
    # Display options
    for i, option in enumerate(options, 1):
        if option[0] == 'folder':
            print(f"  {i}. {option[1]}")
        else:
            print(f"  {i}. {option[1]}")
    
    # Get user choice
    while True:
        try:
            choice = input(f"Enter choice (1-{len(options)}): ").strip()
            if not choice:
                choice = "1"  # Default to first option
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_option = options[choice_idx]
                
                if selected_option[0] == 'root':
                    return {'type': 'root'}
                elif selected_option[0] == 'folder':
                    return {'type': 'folder', 'folder_name': selected_option[2]}
                elif selected_option[0] == 'all':
                    return {'type': 'all'}
            else:
                print(f"Invalid choice! Please enter a number between 1-{len(options)}.")
        except ValueError:
            print("Invalid input! Please enter a number.")


def get_single_file_input(discovered: Dict[str, List[Path]], lang_prefs: Dict) -> Dict[str, any]:
    """Get input for single file processing mode."""
    import pandas as pd
    
    # Create a flat list of all files for selection
    all_files = []
    file_locations = []  # Track where each file is located
    
    # Add root files
    for file_path in discovered['root_files']:
        all_files.append(file_path)
        file_locations.append('root')
    
    # Add folder files
    for folder_name, files in discovered['folders'].items():
        for file_path in files:
            all_files.append(file_path)
            file_locations.append(folder_name)
    
    if not all_files:
        print("No files available for selection.")
        return {}
    
    print("Select a file to translate:")
    for i, (file_path, location) in enumerate(zip(all_files, file_locations), 1):
        file_type = "CSV" if file_path.suffix.lower() == ".csv" else "XML"
        if location == 'root':
            print(f"  {i}. {file_path.name} ({file_type}) [root]")
        else:
            relative_path = file_path.relative_to(SOURCE_DIR)
            print(f"  {i}. {relative_path} ({file_type}) [in {location}/]")
    print()
    
    # Get file selection
    if len(all_files) == 1:
        selected_file = all_files[0]
        selected_location = file_locations[0]
        print(f"Auto-selected: {selected_file.name}")
    else:
        try:
            choice = int(input("Select a file (enter number): ").strip())
            if 1 <= choice <= len(all_files):
                selected_file = all_files[choice - 1]
                selected_location = file_locations[choice - 1]
            else:
                print("Invalid selection!")
                return {}
        except ValueError:
            print("Invalid input! Please enter a number.")
            return {}
    
    input_file = str(selected_file)
    file_type = selected_file.suffix.lower()
    
    # Determine output file path
    if selected_location == 'root':
        # File is in root - output to target root
        output_dir = TARGET_DIR
    else:
        # File is in subfolder - create corresponding target subfolder
        output_dir = TARGET_DIR / selected_location
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle different file types
    if file_type == ".csv":
        return get_csv_input_single(selected_file, input_file, output_dir, lang_prefs)
    elif file_type == ".xml":
        return get_xml_input_single(selected_file, input_file, output_dir, lang_prefs)
    else:
        print(f"Unsupported file type: {file_type}")
        return {}


def get_csv_input_single(selected_file: Path, input_file: str, output_dir: Path, lang_prefs: Dict) -> Dict[str, any]:
    """Get CSV-specific input parameters for single file mode."""
    import pandas as pd
    
    # Auto-detect CSV delimiter (same logic as batch mode)
    print("\nAuto-detecting CSV delimiter...")
    delimiters = [',', ';']
    df_preview = None
    chosen_delimiter = ','
    
    for delimiter in delimiters:
        try:
            df_test = pd.read_csv(input_file, nrows=5, delimiter=delimiter)
            if len(df_test.columns) > 1:  # Good indication of correct delimiter
                df_preview = pd.read_csv(input_file, nrows=0, delimiter=delimiter)
                chosen_delimiter = delimiter
                break
        except:
            continue
    
    if df_preview is None:
        print("Could not auto-detect delimiter. Trying manual selection...")
        # Fallback to manual selection  
        print("Choose CSV delimiter:")
        print("  1. Comma (,) - Standard CSV format")
        print("  2. Semicolon (;) - European CSV format")
        delimiter_choice = input("Enter choice (1 or 2, default: 1): ").strip()
        
        if delimiter_choice == "2":
            chosen_delimiter = ";"
        else:
            chosen_delimiter = ","
        
        try:
            df_preview = pd.read_csv(input_file, nrows=0, delimiter=chosen_delimiter)
        except Exception as e:
            print(f"Error reading CSV file with {chosen_delimiter} delimiter: {e}")
            return {}
    
    # Display detected columns for user confirmation
    print(f"\nDetected CSV structure:")
    for col in df_preview.columns:
        print(f"  - {col}")
    
    # Ask user to confirm or re-select columns
    columns_to_translate = list(df_preview.columns)  # Default to all columns
    confirm = input("\nTranslate all columns? (Y/n): ").strip().lower()
    if confirm == 'n':
        # Let user select specific columns
        columns_to_translate = []
        while True:
            col_choice = input("Enter column name (or blank to finish): ").strip()
            if not col_choice:
                break
            if col_choice in df_preview.columns:
                columns_to_translate.append(col_choice)
            else:
                print(f"Column '{col_choice}' not found. Please enter a valid column name.")
    
    # Generate column suffix based on target language
    suffix = f"_{get_language_suffix(lang_prefs['target_lang'])}"
    
    # Generate output file path using the new naming convention
    output_filename = generate_output_filename(selected_file.name, lang_prefs['target_lang'], is_root_file=True)
    output_file = output_dir / output_filename
    print(f"\nOutput will be saved to: {output_file}")
    
    return {
        'mode': 'single',
        'selected_file': selected_file,
        'output_file': output_file,
        'columns_to_translate': columns_to_translate,
        'delimiter': chosen_delimiter,
        'append_suffix': suffix,
        'source_lang': lang_prefs['source_lang'],
        'target_lang': lang_prefs['target_lang'],
        'source_name': lang_prefs['source_name'],
        'target_name': lang_prefs['target_name']
    }


def get_xml_input_single(selected_file: Path, input_file: str, output_dir: Path, lang_prefs: Dict) -> Dict[str, any]:
    """Get XML-specific input parameters for single file mode."""
    
    # For XML files, we don't need column selection - just generate output filename
    output_filename = generate_output_filename(selected_file.name, lang_prefs['target_lang'], is_root_file=True)
    output_file = output_dir / output_filename
    
    print(f"\n📋 XML Translation Summary:")
    print(f"  📁 Input file: {selected_file.name}")
    print(f"  📁 Output file: {output_filename}")
    print(f"  🌐 Translation: {lang_prefs['source_name']} -> {lang_prefs['target_name']}")
    print(f"  🏷️  Processing: All text content (preserving XML structure)")
    
    return {
        'mode': 'single',
        'selected_file': selected_file,
        'output_file': output_file,
        'source_lang': lang_prefs['source_lang'],
        'target_lang': lang_prefs['target_lang'],
        'source_name': lang_prefs['source_name'],
        'target_name': lang_prefs['target_name']
    }


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
