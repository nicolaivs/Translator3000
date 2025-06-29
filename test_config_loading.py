#!/usr/bin/env python3
"""Test config loading to check for warnings."""

import sys
sys.path.append('.')

from translator3000 import CONFIG

print("Config loaded successfully!")
print(f"localhost_enabled: {CONFIG.get('libretranslate_localhost_enabled')} (type: {type(CONFIG.get('libretranslate_localhost_enabled'))})")
print(f"localhost_port: {CONFIG.get('libretranslate_localhost_port')} (type: {type(CONFIG.get('libretranslate_localhost_port'))})")
print(f"localhost_timeout: {CONFIG.get('libretranslate_localhost_timeout')} (type: {type(CONFIG.get('libretranslate_localhost_timeout'))})")
