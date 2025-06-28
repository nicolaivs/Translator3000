# LibreTranslate Integration Guide

## Overview

Translator3000 supports LibreTranslate as a privacy-focused fallback translation service, with performance-optimized services taking priority.

## Translation Services Priority

1. **deep-translator** (primary)
   - Fastest: ~4.6 translations/sec
   - Google Translate wrapper
   - Most reliable for speed
   
2. **googletrans** (secondary)
   - Good speed: ~4.0 translations/sec
   - Original Google Translate library
   - Solid fallback option
   
3. **LibreTranslate** (privacy fallback)
   - Privacy-focused: ~1.0 translations/sec
   - Free and open-source
   - No data logging
   - EU-based servers
   - Self-hosted option available

## Why LibreTranslate as Fallback?

LibreTranslate offers excellent privacy benefits but is significantly slower than other services:

**Performance Comparison:**
- deep-translator: 4.6 translations/sec
- googletrans: 4.0 translations/sec  
- LibreTranslate: 1.0 translations/sec

**Use LibreTranslate when:**
- Privacy is your top concern
- You have a self-hosted instance (no rate limits)
- Other services are temporarily unavailable
- You prefer open-source solutions

## LibreTranslate Configuration

### Basic Setup (Performance-Optimized)
```ini
# Use fastest services first, privacy-focused as fallback
translation_services=deep_translator,googletrans,libretranslate

# LibreTranslate endpoint (used as fallback)
libretranslate_url=https://libretranslate.com/translate

# No API key needed for basic usage
libretranslate_api_key=
```

### Privacy-First Setup
```ini
# Use LibreTranslate as primary for maximum privacy
translation_services=libretranslate,deep_translator,googletrans

# Get higher rate limits with an API key
libretranslate_api_key=your_api_key_here
```

Get an API key from: https://libretranslate.com/

### Self-Hosted Instance
```ini
# Use your own LibreTranslate server
libretranslate_url=http://localhost:5000/translate
libretranslate_api_key=
```

## Performance Notes

- **LibreTranslate**: ~1-2 translations/sec (public API)
- **deep-translator**: ~4-5 translations/sec
- **Automatic fallback**: If LibreTranslate fails, instantly tries deep-translator

## Rate Limiting

The public LibreTranslate API has rate limits:
- **Without API key**: Limited requests per minute
- **With API key**: Higher limits based on plan
- **Self-hosted**: No limits (your own server)

## Privacy Benefits

LibreTranslate advantages:
- No data logging or tracking
- Open-source and transparent
- EU-based for GDPR compliance
- Can be self-hosted for complete privacy

## Troubleshooting

### LibreTranslate Timeouts
If you see "All translation services failed" messages:
1. Check your internet connection
2. Try with an API key for higher limits
3. The script will automatically fallback to deep-translator
4. Consider self-hosting for unlimited usage

### Service Configuration
To use only specific services:
```ini
# Only LibreTranslate
translation_services=libretranslate

# Only deep-translator
translation_services=deep_translator

# Skip LibreTranslate, use others
translation_services=deep_translator,googletrans
```

## Installation

Install LibreTranslate support:
```bash
pip install requests
```

The script automatically detects available libraries and configures services accordingly.
