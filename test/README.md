# Test Scripts

This folder contains all test scripts for the Translator3000 project.

## Test Categories

### Performance & Benchmarking
- `test_benchmark.py` - General performance benchmarking
- `test_delay_comparison.py` - Delay optimization testing
- `test_speed.py` - Translation speed testing
- `test_multithreading.py` - Multithreading performance tests

### Translation Services
- `test_googletrans4.py` - Google Translate 4.x testing
- `test_libretranslate.py` - LibreTranslate service testing
- `test_localhost_detection.py` - Local LibreTranslate detection testing
- `test_sync_wrapper.py` - Async wrapper testing

### File Format Support
- `test_csv_detection.py` - CSV file detection and parsing
- `test_csv_edge_cases.py` - CSV edge case handling
- `test_html_translation.py` - HTML content translation
- `test_xml_cdata.py` - XML CDATA handling
- `test_real_xml.py` - Real XML file testing

### Configuration & Features
- `test_config_loading.py` - Configuration file loading
- `test_config_status.py` - Configuration status checking
- `test_glossary.py` - Glossary functionality
- `test_naming.py` - File naming conventions
- `test_company_name.py` - Company name handling

### Setup & Environment
- `test_setup.py` - Environment setup testing

## Running Tests

To run any test script:

```bash
# From the project root
python test/test_script_name.py

# Or from the test folder
cd test
python test_script_name.py
```

## Adding New Tests

When creating new test scripts:
1. Name them with the `test_` prefix
2. Place them in this `test/` folder
3. Update this README if adding a new category
4. Include clear documentation in the script itself
