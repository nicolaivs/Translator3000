#!/usr/bin/env python3
"""
Test edge cases for CSV auto-detection.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_edge_cases():
    """Test CSV delimiter auto-detection with edge cases."""
    
    # Create test CSV files with edge cases
    test_dir = Path(__file__).parent / "test_edge_cases"
    test_dir.mkdir(exist_ok=True)
    
    print("=== Testing CSV Auto-Detection Edge Cases ===\n")
    
    # Test case 1: Single column (should default to comma)
    single_column_data = """ProductName
Product A with comma, in name
Product B with semicolon; in name
Product C normal name"""
    
    single_file = test_dir / "single_column.csv"
    with open(single_file, 'w', encoding='utf-8') as f:
        f.write(single_column_data)
    
    # Test case 2: Comma in quoted fields with semicolon delimiter
    quoted_semicolon_data = '''Name;Description;Price
"Product A";"Great product, with comma in description";19.99
"Product B";"Another item, also with comma";29.50'''
    
    quoted_file = test_dir / "quoted_semicolon.csv"
    with open(quoted_file, 'w', encoding='utf-8') as f:
        f.write(quoted_semicolon_data)
    
    def test_detection_logic(file_path, description):
        print(f"Testing: {description}")
        print(f"File: {file_path.name}")
        
        delimiters = [',', ';']
        detected_delimiter = ','
        columns_found = 0
        
        for delimiter in delimiters:
            try:
                df_test = pd.read_csv(file_path, nrows=5, delimiter=delimiter)
                if len(df_test.columns) > columns_found:
                    columns_found = len(df_test.columns)
                    detected_delimiter = delimiter
            except Exception as e:
                print(f"  Error with {delimiter}: {e}")
                continue
        
        delimiter_name = "Semicolon (;)" if detected_delimiter == ';' else "Comma (,)"
        print(f"Detected delimiter: {delimiter_name}")
        print(f"Columns found: {columns_found}")
        
        try:
            df_final = pd.read_csv(file_path, delimiter=detected_delimiter)
            print(f"Sample data preview:")
            print(df_final.head(2))
        except Exception as e:
            print(f"Error reading final file: {e}")
        
        print("-" * 60)
    
    # Test both edge cases
    test_detection_logic(single_file, "Single column file")
    test_detection_logic(quoted_file, "Quoted fields with commas")
    
    # Clean up
    single_file.unlink()
    quoted_file.unlink()
    test_dir.rmdir()
    
    print("Edge case testing completed!")

if __name__ == "__main__":
    test_edge_cases()
