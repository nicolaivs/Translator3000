#!/usr/bin/env python3
"""
Comprehensive test to debug why text is not being translated in CSV processor.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from translator3000.processors.csv_processor import CSVProcessor
import logging

# Enable debug logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def test_translation_coverage():
    """Test to identify why text is not being translated."""
    
    print("🧪 Testing translation coverage and debugging issues...")
    
    # Initialize processor
    csv_processor = CSVProcessor('en', 'da')  # English to Danish for testing
    
    # Test cases with varying complexity
    test_cases = [
        # Simple cases
        "Hello world",
        "This is a test",
        
        # HTML cases with different spacing patterns
        "Use micare<strong>Surface maintenance</strong>For best results.",
        "Also try <em>product testing</em> before use.",
        "Text with <span>multiple words</span> and more text.",
        
        # Complex HTML cases
        "<p>This is a paragraph with <strong>bold text</strong> inside.</p>",
        "<div>Content with <em>emphasis</em> and <span>spans</span> everywhere.</div>",
        
        # Edge cases
        "Text<span> with leading space</span>here",
        "Text<span>with trailing space </span>here",
        "Multiple<strong> words </strong>in<em> different </em>tags",
        
        # Mixed content
        "Before <strong data-attr='value'>tagged content</strong> after text."
    ]
    
    print("📄 Testing individual translation cases:")
    print("=" * 100)
    
    for i, original in enumerate(test_cases):
        print(f"\nTest case {i+1}:")
        print(f"Original:   '{original}'")
        
        # Test HTML detection
        is_html = csv_processor.is_html_content(original)
        print(f"HTML detected: {is_html}")
        
        # Test translation
        if is_html:
            translated = csv_processor.translate_html_content(original)
        else:
            translated = csv_processor._translate_plain_text(original)
            
        print(f"Translated: '{translated}'")
        
        # Check if translation actually happened
        if translated == original:
            print("⚠️  WARNING: No translation occurred!")
        else:
            print("✅ Translation successful")
        
        # For HTML content, let's also test the BeautifulSoup method directly
        if is_html:
            try:
                bs_result = csv_processor._translate_html_with_beautifulsoup(original)
                print(f"BeautifulSoup: '{bs_result}'")
                if bs_result == original:
                    print("❌ BeautifulSoup method failed to translate!")
                else:
                    print("✅ BeautifulSoup method worked")
            except Exception as e:
                print(f"❌ BeautifulSoup method error: {e}")

def test_beautifulsoup_debugging():
    """Debug the BeautifulSoup translation method specifically."""
    
    print("\n" + "=" * 100)
    print("🔍 Debugging BeautifulSoup translation method...")
    
    # Initialize processor
    csv_processor = CSVProcessor('en', 'da')
    
    # Test HTML content
    html_content = "Use micare<strong>Surface maintenance</strong>For best results."
    
    print(f"\nDebugging: '{html_content}'")
    
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"Soup structure: {soup}")
        print("Text nodes found:")
        
        for i, text_node in enumerate(soup.find_all(string=True)):
            original_text = text_node.string
            text_content = original_text.strip()
            
            print(f"  Node {i+1}:")
            print(f"    Original: '{original_text}'")
            print(f"    Stripped: '{text_content}'")
            print(f"    Parent: {text_node.parent.name if text_node.parent else 'None'}")
            print(f"    Length: {len(text_content)}")
            print(f"    Should translate: {text_content and len(text_content) > 1}")
            
            if text_content and len(text_content) > 1:
                # Try to translate this node
                try:
                    translated = csv_processor._translate_plain_text(text_content)
                    print(f"    Translated: '{translated}'")
                    
                    if translated != text_content:
                        print("    ✅ Translation worked")
                        
                        # Test whitespace preservation
                        content_start = original_text.find(text_content)
                        leading_space = original_text[:content_start] if content_start > 0 else ''
                        content_end = content_start + len(text_content)
                        trailing_space = original_text[content_end:] if content_end < len(original_text) else ''
                        
                        print(f"    Leading space: '{leading_space}' (len={len(leading_space)})")
                        print(f"    Trailing space: '{trailing_space}' (len={len(trailing_space)})")
                        
                        new_text = leading_space + translated + trailing_space
                        print(f"    Final result: '{new_text}'")
                    else:
                        print("    ❌ Translation failed - same as original")
                        
                except Exception as e:
                    print(f"    ❌ Translation error: {e}")
            else:
                print("    ⏭️  Skipped (too short or empty)")
                
    except Exception as e:
        print(f"❌ BeautifulSoup debugging failed: {e}")

def test_simple_html_cases():
    """Test specific simple HTML cases that should work."""
    
    print("\n" + "=" * 100)
    print("🧪 Testing simple HTML cases...")
    
    csv_processor = CSVProcessor('en', 'da')
    
    simple_cases = [
        "<strong>Surface maintenance</strong>",
        "<em>product testing</em>",
        "<span>multiple words</span>",
        "Before <strong>text</strong> after",
        "Text <em>emphasis</em> more text"
    ]
    
    for case in simple_cases:
        print(f"\nTesting: '{case}'")
        result = csv_processor._translate_html_with_beautifulsoup(case)
        print(f"Result:  '{result}'")
        
        if result == case:
            print("❌ No translation occurred")
        else:
            print("✅ Translation successful")

if __name__ == "__main__":
    test_translation_coverage()
    test_beautifulsoup_debugging()
    test_simple_html_cases()
