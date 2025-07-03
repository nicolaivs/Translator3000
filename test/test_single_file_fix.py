#!/usr/bin/env python3
"""
Test script to verify the single file output naming fix.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator3000 import CSVTranslator
from translator3000.config import TEST_SOURCE_DIR, TARGET_DIR

def test_single_file_naming():
    """Test that single file translation generates correct output filename."""
    print("=== Testing Single File Output Naming Fix ===\n")
    
    # Use test source directory from config
    source_dir = TEST_SOURCE_DIR
    target_dir = TARGET_DIR
    
    # Ensure directories exist
    source_dir.mkdir(exist_ok=True)
    target_dir.mkdir(exist_ok=True)
    
    # Look for sample files
    sample_files = list(source_dir.glob("*.csv"))
    if not sample_files:
        print(f"❌ No CSV files found in {source_dir} directory")
        print("Please add a CSV file to test with.")
        return
    
    test_file = sample_files[0]
    print(f"📁 Using test file: {test_file}")
    
    # Create translator
    translator = CSVTranslator(
        source_lang='en',
        target_lang='sv',  # English to Swedish
        delay_between_requests=0.1
    )
    
    # Test the filename generation directly
    from translator3000.utils.language_utils import generate_output_filename
    
    expected_filename = generate_output_filename(test_file.name, 'sv', is_root_file=True)
    print(f"📝 Expected output filename: {expected_filename}")
    
    # Create expected output path
    expected_output = target_dir / expected_filename
    print(f"📁 Expected output path: {expected_output}")
    
    # Test actual translation with a few columns
    try:
        import pandas as pd
        df = pd.read_csv(test_file)
        columns = list(df.columns)
        print(f"📊 Available columns: {columns}")
        
        # Take first 2 columns or all if less than 2
        test_columns = columns[:2] if len(columns) >= 2 else columns
        print(f"🔤 Testing with columns: {test_columns}")
        
        # Perform translation
        print("\n🔄 Starting translation...")
        success = translator.translate_csv(
            input_file=str(test_file),
            output_file=str(expected_output),
            columns_to_translate=test_columns,
            append_suffix='_swedish'
        )
        
        if success:
            print(f"✅ Translation completed successfully!")
            print(f"📁 Output file: {expected_output}")
            
            # Check if file exists
            if expected_output.exists():
                print(f"✅ Output file exists with correct name!")
                print(f"📊 File size: {expected_output.stat().st_size} bytes")
            else:
                print(f"❌ Output file not found at expected location!")
        else:
            print(f"❌ Translation failed!")
            
    except Exception as e:
        print(f"❌ Error during translation: {e}")
    
    # Check for any incorrectly named files
    print("\n🔍 Checking for incorrectly named files...")
    
    # Check for "None" file
    none_file = Path("None")
    if none_file.exists():
        print(f"❌ Found 'None' file - bug still exists!")
    else:
        print(f"✅ No 'None' file found - bug appears to be fixed!")
    
    # List all files in target directory
    target_files = list(target_dir.glob("*"))
    print(f"\n📂 Files in target directory:")
    for file in target_files:
        print(f"  📄 {file.name}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_single_file_naming()
