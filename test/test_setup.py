#!/usr/bin/env python3
"""
Quick test script to verify the CSV translator setup.
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported."""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    # Test translation libraries
    deep_translator_available = False
    googletrans_available = False
    
    try:
        from deep_translator import GoogleTranslator
        print("✅ deep-translator imported successfully")
        deep_translator_available = True
    except ImportError as e:
        print(f"⚠️  deep-translator import failed: {e}")
    
    try:
        from googletrans import Translator
        print("✅ googletrans imported successfully")
        googletrans_available = True
    except ImportError as e:
        print(f"⚠️  googletrans import failed: {e}")
    
    if not deep_translator_available and not googletrans_available:
        print("❌ No translation library available!")
        return False
    
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    return True

def test_translator():
    """Test basic translation functionality."""
    print("\nTesting translator...")
    
    # Try deep-translator first
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='nl')
        result = translator.translate("Hello World")
        print(f"✅ deep-translator test: 'Hello World' -> '{result}'")
        return True
    except Exception as e:
        print(f"⚠️  deep-translator test failed: {e}")
    
    # Try googletrans as fallback
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate("Hello World", src='en', dest='nl')
        print(f"✅ googletrans test: 'Hello World' -> '{result.text}'")
        return True
    except Exception as e:
        print(f"⚠️  googletrans test failed: {e}")
    
    print("❌ All translation tests failed")
    return False

def test_csv_reading():
    """Test CSV file reading."""
    print("\nTesting CSV reading...")
    
    try:
        import pandas as pd
        
        # Check if sample file exists
        csv_file = "sample_products.csv"
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            print(f"✅ CSV reading test: loaded {len(df)} rows, {len(df.columns)} columns")
            print(f"   Columns: {list(df.columns)}")
            return True
        else:
            print(f"⚠️  Sample CSV file '{csv_file}' not found")
            return False
            
    except Exception as e:
        print(f"❌ CSV reading test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("CSV Translator - Setup Verification")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test translator (requires internet)
    if not test_translator():
        all_passed = False
        print("   Note: Translation test requires internet connection")
    
    # Test CSV functionality
    if not test_csv_reading():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nTo run the translator:")
        print("   python csv_translator.py")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\nTry running:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main()
