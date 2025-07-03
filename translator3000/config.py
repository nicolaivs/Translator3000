"""
Configuration management for Translator3000.

This module handles loading and managing configuration settings from the
translator3000.config file, with sensible defaults and type validation.
"""

import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Define project directories
PROJECT_ROOT = Path(__file__).parent.parent
# SOURCE_DIR will be initialized after loading config
TARGET_DIR = PROJECT_ROOT / "target"
# TEST_SOURCE_DIR will be initialized after loading config

# Ensure target directory exists
TARGET_DIR.mkdir(exist_ok=True)

# Default configuration values
# Performance optimized settings - see PERFORMANCE.md for detailed analysis
DEFAULT_CONFIG = {
    'delay': 5,  # milliseconds between requests (optimal: 4.6 trans/sec vs 3.7 at 50ms)
    'max_retries': 3,
    'retry_base_delay': 20,
    'csv_max_workers': 6,
    'xml_max_workers': 6,
    'multithreading_threshold': 2,
    'progress_interval': 10,
    'source_directory': '',  # Empty string means use default "source" folder
    'source_directory_test': '',  # Empty string means use default source directory
    'translation_services': 'deep_translator,googletrans,libretranslate',
    'libretranslate_selfhost_enabled': True,
    'libretranslate_selfhost_port': 5000,
    'libretranslate_selfhost_timeout': 2,
    'libretranslate_selfhost_url': 'http://localhost:5000/translate',
    'libretranslate_url': 'https://libretranslate.com/translate',
    'libretranslate_api_key': ''
}

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    'da': 'Danish',
    'nl': 'Dutch (Netherlands)',
    'nl-be': 'Dutch (Flemish)',
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'no': 'Norwegian (Bokmål)',
    'es': 'Spanish',
    'sv': 'Swedish'
}


def load_config() -> Dict[str, Any]:
    """Load configuration from translator3000.config file."""
    config = DEFAULT_CONFIG.copy()
    config_file = PROJECT_ROOT / "translator3000.config"
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.split('#')[0].strip()  # Remove inline comments
                        
                        if key in config:
                            try:
                                # Convert to appropriate type (check bool first, since bool is subclass of int)
                                if isinstance(config[key], bool) or value.lower() in ('true', 'false'):
                                    config[key] = value.lower() == 'true'
                                elif isinstance(config[key], int):
                                    config[key] = int(value)
                                elif isinstance(config[key], float):
                                    config[key] = float(value)
                                else:
                                    config[key] = value
                            except ValueError:
                                logger.warning(f"Invalid config value at line {line_num}: {line}")
                        else:
                            # Add new config keys that aren't in DEFAULT_CONFIG yet
                            config[key] = value
            
            logger.info(f"Loaded configuration: delay={config['delay']}ms, max_workers={config['csv_max_workers']}")
        except Exception as e:
            logger.warning(f"Error loading config file: {e}. Using defaults.")
    else:
        logger.info(f"No config file found. Using defaults: delay={config['delay']}ms")
    
    return config


def get_config() -> Dict[str, Any]:
    """Get the current configuration."""
    return _config


# Load configuration on module import
_config = load_config()

# Initialize SOURCE_DIR based on loaded config
if _config['source_directory']:
    # Use custom source directory from config
    custom_path = _config['source_directory']
    # Handle both absolute and relative paths
    if Path(custom_path).is_absolute():
        SOURCE_DIR = Path(custom_path)
    else:
        SOURCE_DIR = PROJECT_ROOT / custom_path
    logger.info(f"Using custom source directory: {SOURCE_DIR}")
else:
    # Use default source directory
    SOURCE_DIR = PROJECT_ROOT / "source"
    logger.info(f"Using default source directory: {SOURCE_DIR}")

# Initialize TEST_SOURCE_DIR based on loaded config
if _config['source_directory_test']:
    # Use custom test source directory from config
    custom_test_path = _config['source_directory_test']
    # Handle both absolute and relative paths
    if Path(custom_test_path).is_absolute():
        TEST_SOURCE_DIR = Path(custom_test_path)
    else:
        TEST_SOURCE_DIR = PROJECT_ROOT / custom_test_path
    logger.info(f"Using custom test source directory: {TEST_SOURCE_DIR}")
else:
    # Use SOURCE_DIR for test files if no specific test directory is provided
    TEST_SOURCE_DIR = SOURCE_DIR
    logger.info(f"Using main source directory for tests: {TEST_SOURCE_DIR}")

# Ensure source directories exist
SOURCE_DIR.mkdir(exist_ok=True)
TEST_SOURCE_DIR.mkdir(exist_ok=True)

# For backward compatibility
CONFIG = _config
