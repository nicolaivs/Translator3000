#!/usr/bin/env python3
"""
Demo script to show CSV translation in action.
This runs the translation automatically on the sample file.
"""

import sys
import os
# Add parent directory to path so we can import translator3000
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from translator3000 import CSVTranslator

def demo_translation():
    """Demo the CSV translation functionality."""
    print("CSV Translation Demo")
    print("=" * 30)
    
    # Check if sample file exists
    input_file = "sample_products.csv"
    if not os.path.exists(input_file):
        print(f"❌ Sample file '{input_file}' not found!")
        return
    
    print(f"📁 Using sample file: {input_file}")
    print("🔄 Translating 'name' and 'description' columns from English to Dutch...")
    print()
    
    # Create translator
    translator = CSVTranslator(delay_between_requests=0.2)
      # Translate the sample file (comma-delimited)
    print("Demo 1: Comma-delimited CSV")
    success1 = translator.translate_csv(
        input_file="sample_products.csv",
        output_file="sample_products_demo_translated.csv",
        columns_to_translate=["name", "description"],
        delimiter=","
    )
    
    # Translate the semicolon-delimited sample file
    print("\nDemo 2: Semicolon-delimited CSV")
    success2 = translator.translate_csv(
        input_file="sample_products_semicolon.csv",
        output_file="sample_products_semicolon_translated.csv",
        columns_to_translate=["name", "description"],
        delimiter=";"
    )
    
    if success1 and success2:
        print("\n🎉 Demo translation completed!")
        print("📁 Check the files:")
        print("   - sample_products_demo_translated.csv (comma-delimited)")
        print("   - sample_products_semicolon_translated.csv (semicolon-delimited)")
        print("\nOriginal vs Translated columns:")
        
        # Show a comparison
        import pandas as pd
        df = pd.read_csv("sample_products_demo_translated.csv")
        for idx, row in df.head(2).iterrows():
            print(f"\nProduct {idx + 1}:")
            print(f"  Original name: {row['name']}")
            print(f"  Dutch name:    {row['name_dutch']}")
            print(f"  Original desc: {row['description'][:50]}...")
            print(f"  Dutch desc:    {row['description_dutch'][:50]}...")
    else:
        print("❌ Demo translation failed")

if __name__ == "__main__":
    demo_translation()
