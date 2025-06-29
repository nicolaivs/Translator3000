"""
LibreTranslate translation service implementation.

This module provides the LibreTranslate API service wrapper with self-hosted
server detection and automatic fallback to remote services.
"""

import logging
from typing import Optional
from .base import BaseTranslationService
from ..config import get_config

logger = logging.getLogger(__name__)


def is_libretranslate_selfhost_available() -> bool:
    """Check if LibreTranslate is running on self-hosted server."""
    config = get_config()
    
    if not config.get('libretranslate_selfhost_enabled', True):
        return False
        
    try:
        import requests
        selfhost_url = config.get('libretranslate_selfhost_url', 'http://localhost:5000/translate')
        timeout = config.get('libretranslate_selfhost_timeout', 2)
        
        # Extract base URL for health check
        if '/translate' in selfhost_url:
            base_url = selfhost_url.replace('/translate', '')
        else:
            base_url = selfhost_url
            
        # Simple GET request to check if service is responding
        response = requests.get(base_url, timeout=timeout)
        
        # Check if it responds with expected LibreTranslate content
        if response.status_code == 200:
            # LibreTranslate usually has "LibreTranslate" in the HTML title or content
            content = response.text.lower()
            if 'libretranslate' in content or 'translate' in content:
                logger.info(f"✓ Self-hosted LibreTranslate detected at {selfhost_url}")
                return True
            else:
                logger.debug(f"Service at {base_url} doesn't appear to be LibreTranslate")
                return False
        else:
            logger.debug(f"Self-hosted service at {base_url} responded with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.debug(f"selfhost LibreTranslate check failed: {e}")
        return False


class LibreTranslateService(BaseTranslationService):
    """LibreTranslate API service wrapper."""
    
    def __init__(self, source_lang: str, target_lang: str, api_url: str = None, api_key: str = ""):
        super().__init__(source_lang, target_lang)
        config = get_config()
        
        # Auto-detect best URL if not provided
        if api_url is None:
            if is_libretranslate_selfhost_available():
                self.api_url = config['libretranslate_selfhost_url']
                logger.info("🚀 Using self-hosted LibreTranslate instance for optimal performance")
            else:
                self.api_url = config['libretranslate_url']
                logger.info("Using remote LibreTranslate service")
        else:
            self.api_url = api_url
            
        self.api_key = api_key or config.get('libretranslate_api_key', '')
    
    def is_available(self) -> bool:
        """Check if LibreTranslate service is available."""
        try:
            import requests
            return True
        except ImportError:
            return False
    
    def translate(self, text: str) -> Optional[str]:
        """Translate text using LibreTranslate API."""
        if not text or not text.strip():
            return text
            
        payload = {
            "q": text.strip(),
            "source": self.source_lang,
            "target": self.target_lang
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Add API key if provided
        if self.api_key:
            payload["api_key"] = self.api_key
        
        try:
            import requests
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 429:
                raise Exception("Rate limit exceeded - consider using an API key")
            elif response.status_code == 403:
                raise Exception("Access forbidden - check API key")
            elif response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            if 'translatedText' in result:
                return result['translatedText']
            else:
                raise Exception(f"Unexpected response format: {result}")
                
        except Exception as e:
            if "Rate limit" in str(e) or "429" in str(e):
                logger.warning("LibreTranslate rate limit hit - falling back to next service")
            else:
                logger.warning(f"LibreTranslate API error: {e}")
            return None
