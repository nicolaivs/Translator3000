"""
Base translation service interface.

This module defines the common interface that all translation services must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseTranslationService(ABC):
    """Abstract base class for all translation services."""
    
    def __init__(self, source_lang: str, target_lang: str):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.name = self.__class__.__name__.lower().replace('translationservice', '')
    
    @abstractmethod
    def translate(self, text: str) -> Optional[str]:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            
        Returns:
            Translated text or None if translation failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this translation service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this translation service."""
        return self.name
