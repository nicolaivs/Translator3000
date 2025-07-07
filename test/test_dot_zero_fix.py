#!/usr/bin/env python3
"""
Test the fix for the .0 issue
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd

def test_dot_zero_fix():
    """Test that the .0 issue is fixed."""
    print("=== Testing .0 Fix ===")
    
    # Create test CSV exactly like user's issue
    test_csv_content = """col1;col2;col3
7131526;7131525;30000
1234567;;50000
9999999;8888888;"""
    
    with open("test_fix.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    print("Original CSV:")
    print(test_csv_content)
    
    # Test the OLD way (without keep_default_na=False)
    print("\n=== OLD WAY (problematic) ===")
    df_old = pd.read_csv("test_fix.csv", encoding='utf-8', delimiter=';')
    print("DataFrame dtypes:", df_old.dtypes.to_dict())
    
    result_old = df_old.copy()
    result_old['col1_translated'] = df_old['col1'].astype(str) + "_translated"
    result_old.to_csv("test_old_output.csv", index=False, encoding='utf-8', sep=';')
    
    with open("test_old_output.csv", "r") as f:
        old_output = f.read()
    print("Old output (with .0 problem):")
    print(old_output)
    
    # Test the NEW way (with keep_default_na=False)
    print("=== NEW WAY (fixed) ===")
    df_new = pd.read_csv("test_fix.csv", encoding='utf-8', delimiter=';', keep_default_na=False)
    print("DataFrame dtypes:", df_new.dtypes.to_dict())
    
    result_new = df_new.copy()
    result_new['col1_translated'] = df_new['col1'].astype(str) + "_translated"
    result_new.to_csv("test_new_output.csv", index=False, encoding='utf-8', sep=';')
    
    with open("test_new_output.csv", "r") as f:
        new_output = f.read()
    print("New output (fixed):")
    print(new_output)
    
    # Clean up
    for file in ["test_fix.csv", "test_old_output.csv", "test_new_output.csv"]:
        try:
            os.remove(file)
        except:
            pass

if __name__ == "__main__":
    test_dot_zero_fix()
