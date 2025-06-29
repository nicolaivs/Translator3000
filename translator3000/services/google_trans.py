"""
Google Translate service implementations.

This module provides both deep-translator and googletrans service wrappers.
"""

import logging
from typing import Optional
from .base import BaseTranslationService

logger = logging.getLogger(__name__)


class DeepTranslatorService(BaseTranslationService):
    """Deep Translator Google Translate service wrapper."""
    
    def __init__(self, source_lang: str, target_lang: str):
        super().__init__(source_lang, target_lang)
        self.translator = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the deep translator."""
        try:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)
        except ImportError:
            logger.warning("deep-translator library not available")
    
    def is_available(self) -> bool:
        """Check if deep-translator service is available."""
        return self.translator is not None
    
    def translate(self, text: str) -> Optional[str]:
        """Translate text using deep-translator."""
        if not self.translator or not text or not text.strip():
            return text if text else None
        
        try:
            return self.translator.translate(text.strip())
        except Exception as e:
            logger.warning(f"deep-translator error: {e}")
            return None


class GoogleTransService(BaseTranslationService):
    """Original googletrans service wrapper."""
    
    def __init__(self, source_lang: str, target_lang: str):
        super().__init__(source_lang, target_lang)
        self.translator = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the googletrans translator."""
        try:
            # Try to import the available googletrans version
            try:
                # Try googletrans 4.x first (async version)
                from googletrans import Translator
                import asyncio
                
                class SyncWrapper:
                    """Synchronous wrapper for async googletrans 4.x"""
                    def __init__(self):
                        self.translator = Translator()
                    
                    def translate(self, text, src='auto', dest='en'):
                        """Synchronous translate method"""
                        try:
                            # Try to get existing event loop
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # If loop is running, create a new one in a thread
                                import concurrent.futures
                                import threading
                                
                                def run_in_thread():
                                    new_loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(new_loop)
                                    try:
                                        return new_loop.run_until_complete(
                                            self.translator.translate(text, src=src, dest=dest)
                                        )
                                    finally:
                                        new_loop.close()
                                
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(run_in_thread)
                                    return future.result()
                            else:
                                # No running loop, safe to use run_until_complete
                                return loop.run_until_complete(
                                    self.translator.translate(text, src=src, dest=dest)
                                )
                        except RuntimeError:
                            # No event loop, create one
                            return asyncio.run(self.translator.translate(text, src=src, dest=dest))
                
                self.translator = SyncWrapper()
                logger.debug("Initialized googletrans 4.x with sync wrapper")
                
            except (ImportError, AttributeError):
                # Fall back to googletrans 3.x (synchronous version)
                from googletrans import Translator
                self.translator = Translator()
                logger.debug("Initialized googletrans 3.x (synchronous)")
                
        except ImportError:
            logger.warning("googletrans library not available")
    
    def is_available(self) -> bool:
        """Check if googletrans service is available."""
        return self.translator is not None
    
    def translate(self, text: str) -> Optional[str]:
        """Translate text using googletrans."""
        if not self.translator or not text or not text.strip():
            return text if text else None
        
        try:
            result = self.translator.translate(text.strip(), src=self.source_lang, dest=self.target_lang)
            return result.text
        except Exception as e:
            logger.warning(f"googletrans error: {e}")
            return None
