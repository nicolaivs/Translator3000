#!/usr/bin/env python3
"""
Demonstrate the difference between old and new behavior for number formatting
"""
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import pandas as pd

def test_na_behavior():
    """Test the difference between keep_default_na=True vs False."""
    print("=== Demonstrating keep_default_na Behavior ===")
    
    # Create a CSV with empty cells that would cause the .0 issue
    test_csv_content = """ItemID;ProductID;Stock;Description
7131526;7131525;30000;Product A
1234567;;50000;Product B (empty ProductID)
9876543;8765432;;Product C (empty Stock)"""
    
    print("Test CSV content:")
    print(test_csv_content)
    print()
    
    # Write test file
    with open("test_na_behavior.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    print("=== OLD BEHAVIOR (keep_default_na=True - default) ===")
    df_old = pd.read_csv("test_na_behavior.csv", encoding='utf-8', delimiter=';')
    print("DataFrame dtypes:")
    print(df_old.dtypes)
    print("\nDataFrame content:")
    print(df_old)
    print("\nEmpty cells become:")
    for col in df_old.columns:
        for i, val in enumerate(df_old[col]):
            if pd.isna(val):
                print(f"  Row {i}, Column '{col}': {val} (type: {type(val)})")
    
    # Save and read back
    df_old.to_csv("test_na_old_output.csv", index=False, encoding='utf-8', sep=';')
    with open("test_na_old_output.csv", "r", encoding="utf-8") as f:
        old_result = f.read()
    print("\nAfter save/read cycle:")
    print(old_result)
    
    print("\n" + "="*60)
    print("=== NEW BEHAVIOR (keep_default_na=False - our fix) ===")
    df_new = pd.read_csv("test_na_behavior.csv", encoding='utf-8', delimiter=';', keep_default_na=False)
    print("DataFrame dtypes:")
    print(df_new.dtypes)
    print("\nDataFrame content:")
    print(df_new)
    print("\nEmpty cells become:")
    for col in df_new.columns:
        for i, val in enumerate(df_new[col]):
            if val == '' or pd.isna(val):
                print(f"  Row {i}, Column '{col}': '{val}' (type: {type(val)})")
    
    # Save and read back
    df_new.to_csv("test_na_new_output.csv", index=False, encoding='utf-8', sep=';')
    with open("test_na_new_output.csv", "r", encoding="utf-8") as f:
        new_result = f.read()
    print("\nAfter save/read cycle:")
    print(new_result)
    
    print("\n" + "="*60)
    print("=== COMPARISON ===")
    if ".0" in old_result:
        print("❌ OLD behavior: Found .0 in numbers due to NaN conversion")
    else:
        print("✅ OLD behavior: No .0 found")
        
    if ".0" in new_result:
        print("❌ NEW behavior: Found .0 in numbers")
    else:
        print("✅ NEW behavior: No .0 found - issue fixed!")
    
    # Clean up
    for file in ["test_na_behavior.csv", "test_na_old_output.csv", "test_na_new_output.csv"]:
        try:
            os.remove(file)
        except:
            pass

if __name__ == "__main__":
    test_na_behavior()
