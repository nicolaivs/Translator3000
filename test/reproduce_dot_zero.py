#!/usr/bin/env python3
"""
Test with a CSV that has numeric columns and NaN values like the user described
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
import numpy as np

def reproduce_dot_zero_issue():
    """Reproduce the .0 issue with numeric data and NaN."""
    print("=== Reproducing .0 Issue ===")
    
    # Create test CSV similar to user's issue: "7131526;7131525;30000;" becomes "7131526;7131525.0;30000;"
    test_csv_content = """col1;col2;col3
7131526;7131525;30000
1234567;;50000
9999999;8888888;"""
    
    print("Original CSV content:")
    print(test_csv_content)
    
    # Write test file
    with open("test_nan_numbers.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    print("\n=== Reading CSV with NaN values ===")
    df = pd.read_csv("test_nan_numbers.csv", encoding='utf-8', delimiter=';')
    print("DataFrame:")
    print(df)
    print("\nDataFrame dtypes:")
    print(df.dtypes)
    print("\nNaN counts:")
    print(df.isnull().sum())
    
    print("\n=== Creating result DataFrame (like CSVProcessor) ===")
    result_df = df.copy()
    
    # Add a translated column (simulate translation without touching col2)
    result_df['col1_translated'] = df['col1'].astype(str) + "_translated"
    
    print("Result DataFrame:")
    print(result_df)
    print("\nResult dtypes:")
    print(result_df.dtypes)
    
    print("\n=== Saving to CSV ===")
    result_df.to_csv("test_nan_output.csv", index=False, encoding='utf-8', sep=';')
    
    # Read back the output
    with open("test_nan_output.csv", "r", encoding="utf-8") as f:
        output_content = f.read()
    print("Output CSV content:")
    print(output_content)
    
    print("\n=== The Problem ===")
    print("Notice how empty values become NaN, and when pandas saves them back,")
    print("numeric columns with NaN get saved with .0 formatting!")
    
    print("\n=== Solution: Use keep_default_na=False ===")
    df_no_na = pd.read_csv("test_nan_numbers.csv", encoding='utf-8', delimiter=';', keep_default_na=False)
    print("DataFrame with keep_default_na=False:")
    print(df_no_na)
    print("\nDataFrame dtypes:")
    print(df_no_na.dtypes)
    
    result_df_no_na = df_no_na.copy()
    result_df_no_na['col1_translated'] = df_no_na['col1'] + "_translated"
    
    result_df_no_na.to_csv("test_no_na_output.csv", index=False, encoding='utf-8', sep=';')
    
    with open("test_no_na_output.csv", "r", encoding="utf-8") as f:
        no_na_output = f.read()
    print("\nOutput with keep_default_na=False:")
    print(no_na_output)
    
    # Clean up
    for file in ["test_nan_numbers.csv", "test_nan_output.csv", "test_no_na_output.csv"]:
        try:
            os.remove(file)
        except:
            pass

if __name__ == "__main__":
    reproduce_dot_zero_issue()
