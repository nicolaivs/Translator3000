#!/usr/bin/env python3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    print("Testing modular Translator3000...")
    
    # Test import
    from translator3000 import CSVTranslator
    print("✓ Modular CSVTranslator imported successfully")
    
    # Test initialization
    translator = CSVTranslator('en', 'da')  # English to Danish
    print("✓ Translator initialized successfully")
    
    # Test text translation
    result = translator.translate_text("Hello world")
    print(f"✓ Translation test: 'Hello world' → '{result}'")
    
    print("\n🎉 Modular architecture working perfectly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
