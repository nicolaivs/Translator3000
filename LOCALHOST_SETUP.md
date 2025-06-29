# LibreTranslate Localhost Setup Guide

This guide explains how to set up and use a local LibreTranslate instance with Translator3000 for optimal performance and privacy.

## Why Use Local LibreTranslate?

### Performance Benefits
- **Speed**: Local instances can be 8-15x faster than remote services
- **No Rate Limits**: Your own instance, no API throttling
- **Offline Operation**: Works without internet connection

### Privacy Benefits
- **Data Privacy**: Your text never leaves your machine
- **GDPR Compliance**: Perfect for sensitive business data
- **No API Keys**: No need for external service accounts

## Quick Setup with Docker

### 1. Install Docker
Download and install Docker Desktop for your operating system.

### 2. Run LibreTranslate Container
```bash
# Basic setup (CPU-only, faster startup)
docker run -p 5000:5000 libretranslate/libretranslate

# With GPU support (if you have NVIDIA GPU)
docker run --gpus all -p 5000:5000 libretranslate/libretranslate

# With persistent API key and custom port
docker run -p 5000:5000 -e LT_API_KEYS=true libretranslate/libretranslate
```

### 3. Verify Installation
Open your browser and go to: http://localhost:5000

You should see the LibreTranslate web interface.

## Translator3000 Configuration

Translator3000 automatically detects and prioritizes local LibreTranslate instances.

### Automatic Detection
When enabled (default), Translator3000 will:
1. Check if localhost:5000 is responding
2. Verify it's actually LibreTranslate
3. Automatically prioritize it over other services
4. Fall back to other services if local instance fails

### Configuration Options

In `translator3000.config`:

```ini
# Enable/disable localhost auto-detection
libretranslate_localhost_enabled=true

# Port to check for local instance (default: 5000)
libretranslate_localhost_port=5000

# Timeout for localhost detection (seconds)
libretranslate_localhost_timeout=2

# Local LibreTranslate endpoint
libretranslate_localhost_url=http://localhost:5000/translate

# Remote LibreTranslate endpoint (fallback)
libretranslate_url=https://libretranslate.com/translate
```

## Service Priority Logic

### With Local LibreTranslate Available:
1. **libretranslate** (localhost:5000) - Fastest
2. **deep_translator** - Cloud fallback
3. **googletrans** - Additional fallback

### Without Local LibreTranslate:
1. **deep_translator** - Fastest cloud service
2. **googletrans** - Fallback
3. **libretranslate** (remote) - Privacy-focused fallback

## Performance Comparison

| Service | Speed (trans/sec) | Privacy | Rate Limits |
|---------|------------------|---------|-------------|
| **Local LibreTranslate** | 8-15 | ★★★★★ | None |
| **deep_translator** | ~4.6 | ★★☆☆☆ | Moderate |
| **googletrans** | ~4.0 | ★★☆☆☆ | Moderate |
| **Remote LibreTranslate** | ~1.0 | ★★★★☆ | High |

## Troubleshooting

### Local Instance Not Detected
1. Verify Docker container is running: `docker ps`
2. Check if port 5000 is accessible: Open http://localhost:5000 in browser
3. Check Translator3000 logs for detection messages
4. Verify `libretranslate_localhost_enabled=true` in config

### Translation Errors
- Local instance may need time to load models on first use
- Some language pairs may not be available locally
- Check Docker container logs: `docker logs <container_id>`

### Performance Issues
- Local instance needs adequate RAM (4GB+ recommended)
- CPU-only instances are slower than GPU-accelerated
- Consider using smaller models for faster response times

## Language Support

Local LibreTranslate supports many language pairs. Check your instance's capabilities:
```bash
curl http://localhost:5000/languages
```

## Advanced Configuration

### Custom Docker Setup
```bash
# Run with specific models and configuration
docker run -p 5000:5000 \
  -e LT_LOAD_ONLY=en,nl,de,fr \
  -e LT_THREADS=4 \
  libretranslate/libretranslate
```

### Production Deployment
For production use, consider:
- Running with docker-compose
- Adding reverse proxy (nginx)
- Setting up SSL certificates
- Monitoring and logging

## Security Notes

- Local instances don't require API keys by default
- Consider enabling API keys for production use
- Use firewall rules to restrict access if needed
- Keep Docker images updated for security patches
