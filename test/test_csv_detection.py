#!/usr/bin/env python3
"""
Test the CSV auto-detection functionality.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_csv_auto_detection():
    """Test CSV delimiter auto-detection logic."""
    
    # Create test CSV files with different delimiters
    test_dir = Path(__file__).parent / "test_csv_files"
    test_dir.mkdir(exist_ok=True)
    
    # Test data
    comma_data = """Name,Description,Price
Product A,Great product with features,19.99
Product B,Another excellent item,29.50
Product C,Premium quality product,39.99"""
    
    semicolon_data = """Name;Description;Price
Product A;Great product with features;19.99
Product B;Another excellent item;29.50
Product C;Premium quality product;39.99"""
    
    # Write test files
    comma_file = test_dir / "test_comma.csv"
    semicolon_file = test_dir / "test_semicolon.csv"
    
    with open(comma_file, 'w', encoding='utf-8') as f:
        f.write(comma_data)
    
    with open(semicolon_file, 'w', encoding='utf-8') as f:
        f.write(semicolon_data)
    
    print("=== Testing CSV Auto-Detection Logic ===\n")
    
    # Test the auto-detection logic (same as in the script)
    def test_file_detection(file_path, expected_delimiter):
        print(f"Testing: {file_path.name}")
        print(f"Expected delimiter: {expected_delimiter}")
        
        delimiters = [',', ';']
        detected_delimiter = ','
        df_preview = None
        
        for delimiter in delimiters:
            try:
                df_test = pd.read_csv(file_path, nrows=5, delimiter=delimiter)
                if len(df_test.columns) > 1:  # Good indication of correct delimiter
                    df_preview = pd.read_csv(file_path, nrows=0, delimiter=delimiter)
                    detected_delimiter = delimiter
                    break
            except:
                continue
        
        delimiter_name = "Semicolon (;)" if detected_delimiter == ';' else "Comma (,)"
        print(f"Detected delimiter: {delimiter_name}")
        
        if detected_delimiter == expected_delimiter:
            print("✓ SUCCESS: Correct delimiter detected")
        else:
            print("✗ FAILED: Wrong delimiter detected")
        
        if df_preview is not None:
            print(f"Columns found: {list(df_preview.columns)}")
        else:
            print("ERROR: Could not read file")
        
        print("-" * 50)
    
    # Test both files
    test_file_detection(comma_file, ',')
    test_file_detection(semicolon_file, ';')
    
    # Clean up test files
    comma_file.unlink()
    semicolon_file.unlink()
    test_dir.rmdir()
    
    print("Test completed!")

if __name__ == "__main__":
    test_csv_auto_detection()
