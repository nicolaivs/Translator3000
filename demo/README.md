# Demo & Benchmark Scripts

This folder contains demonstration and benchmark scripts for the Translator3000 project.

## Demo Scripts

### Translation Demos
- `demo_translation.py` - Basic translation demonstration
- `demo_localhost.py` - Local LibreTranslate demonstration

### Benchmarking
- `benchmark_localhost.py` - Localhost vs remote performance comparison

### HTML Processing  
- `html_translation_demo.py` - HTML content translation examples

## Performance Monitoring

All demo scripts include the new real-time performance benchmarking features:
- Warmup time measurement
- Processing time tracking  
- Character counting (actual translated text only)
- Translation speed calculation in characters/second

Example output:
```
📊 Performance Statistics:
⏱️  Warmup time: 0.59 seconds
⏱️  Processing time: 0.54 seconds
⏱️  Total runtime: 10.43 seconds
🔤 Characters translated: 178
⚡ Translation speed: 331.7 characters/second
```

## Running Demos

To run any demo script:

```bash
# From the project root
python demo/demo_script_name.py

# Or from the demo folder
cd demo
python demo_script_name.py
```

## Purpose

These scripts are designed to:
- Demonstrate key features of Translator3000
- Compare performance between different translation services
- Show best practices for using the library
- Provide examples for new users

## Adding New Demos

When creating new demo or benchmark scripts:
1. Name them with `demo_` or `benchmark_` prefix
2. Place them in this `demo/` folder
3. Include clear comments explaining what the demo shows
4. Update this README if needed
