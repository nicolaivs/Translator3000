#!/usr/bin/env python3
"""
Debug why numbers get ".0" added during CSV processing
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
from translator3000.processors.csv_processor import CSVProcessor

def debug_number_issue():
    """Debug why numbers get .0 added."""
    print("=== Debugging Number .0 Issue ===")
    
    # Create test CSV with the exact data
    test_csv_content = """col1,col2,col3
7131526,7131525,30000
1234567,8901234,50000"""
    
    print("Original CSV content:")
    print(test_csv_content)
    
    # Write test file
    with open("test_numbers.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    print("\n=== Step 1: Read CSV with pandas ===")
    df = pd.read_csv("test_numbers.csv", encoding='utf-8', delimiter=',')
    print("DataFrame after reading:")
    print(df)
    print("\nDataFrame dtypes:")
    print(df.dtypes)
    print("\nDataFrame info:")
    df.info()
    
    print("\n=== Step 2: Create copy (what CSVProcessor does) ===")
    result_df = df.copy()
    print("Result DataFrame after copy:")
    print(result_df)
    print("\nResult DataFrame dtypes:")
    print(result_df.dtypes)
    
    print("\n=== Step 3: Add a translated column ===")
    # Simulate adding a translated column (without actually translating)
    result_df['col1_translated'] = df['col1'].astype(str) + "_translated"
    print("After adding translated column:")
    print(result_df)
    print("\nResult DataFrame dtypes:")
    print(result_df.dtypes)
    
    print("\n=== Step 4: Save to CSV (what CSVProcessor does) ===")
    result_df.to_csv("test_numbers_output.csv", index=False, encoding='utf-8', sep=',')
    
    # Read back the output
    with open("test_numbers_output.csv", "r", encoding="utf-8") as f:
        output_content = f.read()
    print("Output CSV content:")
    print(output_content)
    
    print("\n=== Testing with different dtype settings ===")
    
    # Try reading with dtype=str for all columns
    print("Reading with dtype=str:")
    df_str = pd.read_csv("test_numbers.csv", encoding='utf-8', delimiter=',', dtype=str)
    print(df_str)
    print("dtypes:", df_str.dtypes)
    
    # Save it
    df_str.to_csv("test_numbers_str.csv", index=False, encoding='utf-8', sep=',')
    with open("test_numbers_str.csv", "r", encoding="utf-8") as f:
        str_output = f.read()
    print("Output with dtype=str:")
    print(str_output)
    
    # Clean up
    import os
    for file in ["test_numbers.csv", "test_numbers_output.csv", "test_numbers_str.csv"]:
        try:
            os.remove(file)
        except:
            pass

if __name__ == "__main__":
    debug_number_issue()
