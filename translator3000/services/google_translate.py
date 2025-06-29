"""
Google Translate service implementations.

This module provides both deep-translator (GoogleTranslator) and googletrans
implementations with version compatibility handling.
"""

import asyncio
import logging
from typing import Optional

from .base import BaseTranslationService

logger = logging.getLogger(__name__)


class DeepTranslatorService(BaseTranslationService):
    """Google Translate service via deep-translator library."""
    
    def __init__(self, source_lang: str, target_lang: str):
        super().__init__(source_lang, target_lang)
        
        if not self.is_available():
            raise ImportError("DeepTranslator requires the 'deep-translator' library")
        
        from deep_translator import GoogleTranslator
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    def is_available(self) -> bool:
        """Check if deep-translator library is available."""
        try:
            from deep_translator import GoogleTranslator
            return True
        except ImportError:
            return False
    
    def translate(self, text: str) -> Optional[str]:
        """Translate text using deep-translator GoogleTranslator."""
        if not text or not text.strip():
            return text
        
        try:
            result = self.translator.translate(text.strip())
            return result
        except Exception as e:
            logger.warning(f"DeepTranslator error: {e}")
            return None


class GoogleTransService(BaseTranslationService):
    """Google Translate service via googletrans library with version compatibility."""
    
    def __init__(self, source_lang: str, target_lang: str):
        super().__init__(source_lang, target_lang)
        
        if not self.is_available():
            raise ImportError("GoogleTransService requires the 'googletrans' library")
        
        # Import and set up the appropriate translator based on version
        from googletrans import Translator, __version__
        
        # Check if this is googletrans 4.x (async) or 3.x (sync)
        version_parts = __version__.split('.')
        major_version = int(version_parts[0])
        
        if major_version >= 4:
            # For 4.x, create a wrapper for async functionality
            self.translator = self._GoogleTranslator4xWrapper()
        else:
            # For 3.x, use directly
            self.translator = Translator()
        
        self.is_4x = major_version >= 4
    
    def is_available(self) -> bool:
        """Check if googletrans library is available."""
        try:
            from googletrans import Translator
            return True
        except ImportError:
            return False
    
    def translate(self, text: str) -> Optional[str]:
        """Translate text using googletrans library."""
        if not text or not text.strip():
            return text
        
        try:
            if self.is_4x:
                # Use wrapper for 4.x
                result = self.translator.translate(text.strip(), src=self.source_lang, dest=self.target_lang)
            else:
                # Use directly for 3.x
                result = self.translator.translate(text.strip(), src=self.source_lang, dest=self.target_lang)
            
            return result.text if hasattr(result, 'text') else str(result)
        except Exception as e:
            logger.warning(f"GoogleTrans error: {e}")
            return None
    
    class _GoogleTranslator4xWrapper:
        """Synchronous wrapper for googletrans 4.x async API."""
        
        def __init__(self):
            from googletrans import Translator
            self.translator = Translator()
        
        def translate(self, text: str, src: str, dest: str):
            """Synchronous translation method that wraps the async API."""
            try:
                # Create a new event loop if none exists
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        raise RuntimeError("Event loop is closed")
                except RuntimeError:
                    # No event loop exists, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run the async translation
                result = loop.run_until_complete(
                    self.translator.translate(text, src=src, dest=dest)
                )
                return result
            except Exception as e:
                # If async fails, try the synchronous method (fallback)
                try:
                    return self.translator.translate(text, src=src, dest=dest)
                except:
                    raise e
