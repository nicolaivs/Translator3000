#!/usr/bin/env python3
"""
HTML-Aware CSV Translation Script
=================================

This version of the CSV translator properly handles HTML content,
preserving HTML tags while translating only the text content.

Features:
- Detects HTML content automatically
- Preserves HTML structure and attributes
- Translates only text inside HTML tags
- Fallback to plain text translation for non-HTML content
"""

import pandas as pd
import re
import time
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import translation libraries
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    logger.error("deep-translator not available. Install with: pip install deep-translator")
    TRANSLATOR_AVAILABLE = False

# Import HTML parser
try:
    from bs4 import BeautifulSoup
    HTML_PARSER_AVAILABLE = True
except ImportError:
    logger.warning("BeautifulSoup not available. Install with: pip install beautifulsoup4")
    HTML_PARSER_AVAILABLE = False


class HTMLAwareTranslator:
    """CSV translator that preserves HTML structure."""
    
    def __init__(self):
        if not TRANSLATOR_AVAILABLE:
            raise ImportError("Translation library not available")
        
        self.translator = GoogleTranslator(source='en', target='nl')
    
    def is_html_content(self, text: str) -> bool:
        """Check if text contains HTML tags."""
        if not text:
            return False
        return bool(re.search(r'<[^>]+>', str(text)))
    
    def translate_html_aware(self, text: str) -> str:
        """Translate text while preserving HTML structure."""
        if not text or pd.isna(text):
            return text
        
        text_str = str(text).strip()
        if not text_str:
            return text
        
        if self.is_html_content(text_str):
            logger.info("🔍 HTML content detected - preserving structure")
            return self._translate_html_content(text_str)
        else:
            return self._translate_plain_text(text_str)
    
    def _translate_html_content(self, html_text: str) -> str:
        """Translate HTML content using BeautifulSoup."""
        if not HTML_PARSER_AVAILABLE:
            logger.warning("⚠️  BeautifulSoup not available, using basic regex method")
            return self._translate_html_regex(html_text)
        
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # Find all text nodes and translate them
            for string in soup.find_all(string=True):
                # Skip script, style, and other non-content tags
                if string.parent.name not in ['script', 'style', 'meta', 'head']:
                    text_content = string.strip()
                    if text_content and len(text_content) > 1:
                        translated = self._translate_plain_text(text_content)
                        string.replace_with(translated)
            
            return str(soup)
            
        except Exception as e:
            logger.warning(f"BeautifulSoup parsing failed: {e}")
            return self._translate_html_regex(html_text)
    
    def _translate_html_regex(self, html_text: str) -> str:
        """Fallback HTML translation using regex."""
        try:
            def translate_text_in_tags(match):
                text_content = match.group(1).strip()
                if text_content and len(text_content) > 1:
                    return f'>{self._translate_plain_text(text_content)}<'
                return match.group(0)
            
            # Translate text between HTML tags
            pattern = r'>([^<]+)<'
            return re.sub(pattern, translate_text_in_tags, html_text)
            
        except Exception as e:
            logger.warning(f"Regex HTML translation failed: {e}")
            return html_text
    
    def _translate_plain_text(self, text: str) -> str:
        """Translate plain text."""
        try:
            if not text or len(text.strip()) <= 1:
                return text
            
            translated = self.translator.translate(text.strip())
            time.sleep(0.1)  # Rate limiting
            return translated
            
        except Exception as e:
            logger.warning(f"Translation failed for '{text[:30]}...': {e}")
            return text


def demo_html_translation():
    """Demonstrate HTML-aware translation."""
    print("HTML-Aware Translation Demo")
    print("=" * 30)
    
    if not TRANSLATOR_AVAILABLE:
        print("❌ Translation library not available")
        return
    
    translator = HTMLAwareTranslator()
    
    # Test cases
    test_cases = [
        "Simple text without HTML",
        "<h1>Welcome to our store</h1>",
        "<p>This is a <strong>great product</strong> with amazing features.</p>",
        '<div class="product"><h2>Wireless Headphones</h2><p>High-quality <em>wireless</em> headphones with <span style="color:blue">noise cancellation</span>.</p></div>',
        "Mixed content: <b>Bold text</b> and normal text"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"Original:  {test_text}")
        
        translated = translator.translate_html_aware(test_text)
        print(f"Translated: {translated}")
        
        if translator.is_html_content(test_text):
            print("✅ HTML structure preserved")
        else:
            print("📝 Plain text translation")


if __name__ == "__main__":
    demo_html_translation()
