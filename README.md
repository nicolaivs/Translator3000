# Translator3000 - Multi-Language CSV & XML Translation Script

A powerful Python script for translating CSV file columns and XML text content between multiple languages using the free Google Translate API. Supports both single-file and batch processing modes.

## Features

- 🌐 **Multi-Language Support**: Translate between 10 supported languages
- 🔄 **Dynamic Language Selection**: Choose source and target languages at runtime
- 📊 **CSV Processing**: Reads and processes CSV files with pandas
- 🏷️ **Advanced XML Processing**: Robust HTML-aware XML translation with BeautifulSoup
  - 🔧 **BeautifulSoup Integration**: Industry-standard HTML parsing for maximum compatibility
  - 🛡️ **CDATA Preservation**: Maintains all CDATA sections with HTML content intact
  - 🏗️ **Structure Preservation**: 100% XML structure, attributes, and formatting retained
  - 🚫 **Ignore Attribute Support**: Respects `ignore="true"` at both XML and HTML levels
  - 🎯 **Smart Content Detection**: Automatically identifies and handles nested HTML within XML
  - 🔒 **No HTML Escaping**: HTML content stays as raw HTML, never escaped or corrupted
- 🚀 **Selective Batch Processing**: Choose to process root files only, specific folders only, or everything
- 📁 **Recursive Folder Support**: Scans subdirectories and creates matching target structure
- 🔄 **Batch Translation**: Translates multiple columns efficiently
- 📝 **Preserves Data**: Keeps original columns/structure and adds translated versions
- 🛡️ **Error Handling**: Graceful handling of translation failures
- 📊 **Progress Tracking**: Real-time progress updates and logging
- ⚡ **Performance Optimized**: 5ms API delay (25% faster than previous default) + multithreading
- 📈 **Performance Benchmarking**: Timing warmup, processing time, and translation speed (character/s)
- 🔧 **Auto-Detection**: Automatically detects CSV delimiters and text columns
- 📁 **Organized Workflow**: Automatic source/target folder management
- ⚙️ **Configurable**: User-tunable performance settings via config file
- 🔄 **Multi-Service Support**: deep-translator, googletrans, and LibreTranslate with automatic fallback
- 🏠 **Self Hosted Priority**: Automatically detects and prioritizes self hosted LibreTranslate instances (8-15x faster)
- 🧩 **Modular Architecture**: Clean, maintainable code structure for faster development (NEW in v3.0)

## Supported Languages

- **Danish** (da)
- **Dutch (Netherlands)** (nl)
- **Dutch (Flemish)** (nl-be)
- **English** (en)
- **French** (fr)
- **German** (de)
- **Italian** (it)
- **Norwegian (Bokmål)** (no)
- **Spanish** (es)
- **Swedish** (sv)

## Project Structure

```
Translator3000/
├── source/           # Place your CSV/XML files and folders here
│   ├── folder1/      # Subdirectories are supported
│   │   ├── data1.csv
│   │   └── content1.xml
│   ├── data.csv      # Files in root are also processed
│   └── README.md
├── target/           # Translated files are saved here (mirrors source structure)
│   ├── folder1/      # Matching subdirectories created automatically
│   │   ├── data1_translated.csv
│   │   └── content1_translated.xml
│   └── data_translated.csv
├── test/             # Test scripts for development and validation
│   ├── README.md     # Test documentation
│   ├── test_*.py     # Various test scripts
│   └── ...
├── demo/             # Demo and benchmark scripts
│   ├── README.md     # Demo documentation
│   ├── demo_*.py     # Demonstration scripts
│   └── benchmark_*.py # Performance benchmarking
├── translator3000.py # Main translation script
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Installation

1. **Clone or download this project**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   **Translation Service Options:**
- **deep-translator** (recommended): Fast, reliable Google Translate wrapper
  - Requires: `deep-translator` library
  - Performance: ~4.6 translations/sec (fastest)
- **googletrans**: Original Google Translate library
  - Requires: `googletrans` library
  - Performance: ~4.0 translations/sec (good)
- **LibreTranslate** (privacy-focused): Free, open-source, privacy-friendly
  - Requires: `requests` library
  - API: Uses public LibreTranslate API (or self-hosted)
  - Performance: ~1.0 translations/sec (slower, but private)
  - Privacy: No data logging, EU-based

The script automatically detects available libraries and uses them in order of performance: deep-translator → googletrans → LibreTranslate. Install any combination - the script will work with whatever is available!

3. **Test your setup** (recommended):
   ```bash
   python test_setup.py
   ```

## Usage

### Quick Start

1. **Place your CSV/XML files** in the `source/` folder (subdirectories are supported!)
2. **Run the script**:
   ```bash
   python translator3000.py
   ```
3. **Select your languages** (source language of your data, target language for translation)
4. **Choose processing mode**:
   - **Single file mode**: Select one specific file to translate
   - **Batch mode**: Choose which files to process automatically:
     - **Root directory only**: Process only files in the main source folder
     - **Specific folder only**: Process only files in one selected subfolder  
     - **All files and folders**: Process everything (original batch behavior)
5. **Follow the prompts** to select columns for CSV files:
   - **Single file mode**: Select columns by number (e.g., `2,3` for columns 2 and 3)
   - **Batch mode**: Automatic column detection based on content analysis
6. **Find your translated files** in the `target/` folder with matching directory structure

### Custom Source Directory

You can specify a custom source directory in the `translator3000.config` file:

```ini
# Directory Settings
# ------------------
# Custom source directory for translation files (optional)
# If specified, this directory will be used instead of the default "source" folder
source_directory=C:/my_data/translation_files

# Custom target directory for translated files (optional)
# If specified, this directory will be used instead of the default "target" folder
target_directory=C:/my_data/translated_output

# Source directory specifically for test scripts (optional)
source_directory_test=source
```

Leave the directory settings empty to use the default folders in the project root:
- `source_directory`: The default `source/` folder for input files
- `target_directory`: The default `target/` folder for translated files
- `source_directory_test`: Used by test and demo scripts (can be set separately)

### Performance Output

The script provides detailed performance metrics after each translation:

```
📊 Performance Statistics:
⏱️  Warmup time: 0.59 seconds
⏱️  Processing time: 0.54 seconds
⏱️  Total runtime: 10.43 seconds
🔤 Characters translated: 178
⚡ Translation speed: 331.7 characters/second
```

**What this means:**
- **Warmup time**: Time to initialize translation services
- **Processing time**: Actual translation work time
- **Total runtime**: End-to-end execution time  
- **Characters translated**: Only the actual text sent to translation API (not file size)
- **Translation speed**: Real performance in characters per second

### Interactive Mode (Detailed)

1. Run the script:
   ```bash
   python translator3000.py
   ```

2. The script will:
   - Ask you to choose source language (Danish or English, default: English)
   - Ask you to choose target language from 10 supported options
   - Automatically show CSV and XML files in the `source/` folder
   - Let you choose which file to translate
   - **For CSV files**: Show available columns with numbers and ask which columns you want to translate (by number, e.g., `1,3` or `2` for individual columns)
   - **For XML files**: Automatically translate all text content while preserving structure and attributes
   - Save the translated file to the `target/` folder

### Programmatic Usage

For automated processing, modify the main function in `translator3000.py`:

```python
# Example: Translate English to Dutch
translator = CSVTranslator(
    source_lang='en',      # English
    target_lang='nl',      # Dutch
    delay_between_requests=0.1
)
success = translator.translate_csv(
    input_file=str(SOURCE_DIR / "products.csv"),
    output_file=str(TARGET_DIR / "products_translated.csv"),
    columns_to_translate=["name", "description"]
)

# Example: Translate Danish to Swedish
translator = CSVTranslator(
    source_lang='da',      # Danish
    target_lang='sv',      # Swedish
    delay_between_requests=0.1
)
```

## Language Codes

| Language | Code |
|----------|------|
| Danish | `da` |
| Dutch (Netherlands) | `nl` |
| Dutch (Flemish) | `nl-be` |
| English | `en` |
| French | `fr` |
| German | `de` |
| Italian | `it` |
| Norwegian (Bokmål) | `no` |
| Spanish | `es` |
| Swedish | `sv` |

## Example

### Input CSV (`sample_products.csv`):
```csv
product_id,name,description,price,category
1,Wireless Bluetooth Headphones,High-quality wireless headphones with noise cancellation,99.99,Electronics
2,Organic Cotton T-Shirt,Comfortable organic cotton t-shirt available in multiple colors,24.99,Clothing
```

### Output CSV (after translation):
```csv
product_id,name,description,price,category,name_dutch,description_dutch
1,Wireless Bluetooth Headphones,High-quality wireless headphones with noise cancellation,99.99,Electronics,Draadloze Bluetooth-hoofdtelefoons,Hoogwaardige draadloze hoofdtelefoons met ruisonderdrukking
2,Organic Cotton T-Shirt,Comfortable organic cotton t-shirt available in multiple colors,24.99,Clothing,Biologisch katoenen T-shirt,Comfortabel biologisch katoenen t-shirt verkrijgbaar in meerdere kleuren
```

## XML Processing with BeautifulSoup

Translator3000 features a **state-of-the-art XML processor** powered by BeautifulSoup for maximum HTML compatibility and robust structure preservation.

### Key XML Processing Features

🔧 **BeautifulSoup Integration**
- Industry-standard HTML parsing library for maximum compatibility
- Handles malformed HTML gracefully where regex-based approaches fail
- Professional-grade DOM manipulation and text node traversal

🛡️ **CDATA Preservation** 
- Automatically detects and preserves all CDATA sections
- HTML content within CDATA remains as raw HTML (never escaped)
- Original CDATA wrapping is maintained for elements that had it

🏗️ **100% Structure Preservation**
- All XML attributes, namespaces, and formatting retained
- Element hierarchy and nesting completely preserved
- Whitespace and indentation maintained where possible

🚫 **Ignore Attribute Support**
- Respects `ignore="true"` at both XML and HTML levels
- Nested HTML elements with ignore attributes are also skipped
- Granular control over what gets translated

🎯 **Smart Content Detection**
- Automatically identifies HTML content within XML elements
- Detects elements that originally had CDATA wrapping
- Handles escaped HTML entities (`&lt;`, `&gt;`) intelligently

### Example XML Processing

**Input XML** (`products.xml`):
```xml
<?xml version="1.0" encoding="utf-8"?>
<Products>
    <Product>
        <Title>Wireless Headphones</Title>
        <Description><![CDATA[<p>High-quality <strong>wireless headphones</strong> with <em>noise cancellation</em>.</p>]]></Description>
        <Content ignore="true"><![CDATA[<div class="promo">Special offer!</div>]]></Content>
    </Product>
</Products>
```

**Output XML** (Danish translation):
```xml
<?xml version="1.0" encoding="utf-8"?>
<Products>
    <Product>
        <Title>Trådløse hovedtelefoner</Title>
        <Description><![CDATA[<p>Høj kvalitet <strong>trådløse hovedtelefoner</strong> med <em>støjreduktion</em>.</p>]]></Description>
        <Content ignore="true"><![CDATA[<div class="promo">Special offer!</div>]]></Content>
    </Product>
</Products>
```

**Note**: The `Content` element with `ignore="true"` remains untranslated, while the HTML within CDATA is perfectly preserved with translated text content.

### Technical Implementation

- **BeautifulSoup Parsing**: Robust HTML parsing within XML elements
- **Raw XML Analysis**: Detects original CDATA sections by analyzing raw XML
- **Text Node Traversal**: Translates only actual text content, preserving all HTML structure
- **Intelligent Wrapping**: Automatically wraps HTML content in CDATA when needed
- **Fallback Mechanisms**: Multiple parsing strategies for maximum reliability

## Configuration

The script includes a powerful configuration system via the `translator3000.config` file:

### Initial Setup

1. **Copy the sample config**: `copy translator3000.config.sample translator3000.config`
2. **Edit your settings**: Add API keys and customize performance settings
3. **Secure by default**: The main config file is git-ignored to protect sensitive settings

### Performance Settings (Optimized)

- **API Delay**: 5ms between requests (optimized for best performance)
- **Multithreading**: 6 workers for CSV/XML processing  
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Error Handling**: Graceful fallback to original text on translation failure
- **Custom Directory**: Optional source_directory setting for custom input location

### Translation Services

- **Service Priority**: deep-translator → googletrans → LibreTranslate (performance-ordered)
- **Automatic Fallback**: If one service fails, automatically tries the next
- **LibreTranslate Config**: Supports custom API endpoints and API keys for privacy-focused users
- **Performance First**: Fastest services prioritized, privacy options available as fallback

### Performance Improvements

The script has been optimized for speed:
- **25% faster** than previous versions (5ms vs 50ms delay)
- **Up to 25x speedup** with multithreading for large files
- **Smart thresholds**: Automatically enables multithreading for 3+ items
- **Benchmark tested**: 4.6 translations/sec vs 3.8 with old settings

See `PERFORMANCE.md` for detailed benchmark results and tuning guidance.

### Customization Options

Edit `translator3000.config` to adjust:
- `translation_services`: Service priority order (deep_translator,googletrans,libretranslate)
- `libretranslate_url`: LibreTranslate API endpoint (default: public API)
- `libretranslate_api_key`: Optional API key for higher rate limits
- `delay`: API request delay (5ms recommended)
- `csv_max_workers`: Number of threads for CSV processing (4 recommended)
- `xml_max_workers`: Number of threads for XML processing (4 recommended)
- `multithreading_threshold`: Minimum items to enable multithreading (2 recommended)

For detailed configuration options, see `CONFIG.md`.
- Customize column naming conventions
- Add additional error handling

## About the Translation Service

This script uses the **googletrans** library, which provides:

- ✅ **Free to use** - No API key required
- ✅ **Reliable** - Based on Google Translate
- ✅ **Multiple languages** - Supports 100+ languages
- ⚠️ **Rate limits** - Google may throttle excessive requests
- ⚠️ **Terms of service** - Check Google's ToS for commercial usage

### Alternative Translation Services

For production use or high-volume translation, consider:

1. **Google Cloud Translation API** (paid, higher limits)
2. **Azure Translator** (paid, enterprise features)
3. **DeepL API** (paid, high quality)
4. **LibreTranslate** (open source, self-hosted)

## File Structure

```
Translation/
├── translator3000.py          # Main translation script
├── requirements.txt           # Python dependencies
├── sample_products.csv        # Example CSV file
├── README.md                  # This file
├── .github/
│   └── copilot-instructions.md # Copilot customization
└── translation.log            # Generated log file (after running)
```

## Troubleshooting

### Common Issues

1. **Import errors**: Install dependencies with `pip install -r requirements.txt`
2. **`No module named 'cgi'` error**: This is a known issue with `googletrans` library on newer Python versions. The script automatically uses `deep-translator` library instead, which is more reliable.
3. **Translation fails**: Check internet connection and try increasing delay between requests
4. **Large files**: For files with thousands of rows, consider processing in smaller batches
5. **Encoding issues**: Ensure your CSV file is saved in UTF-8 encoding
6. **Numbers get .0 added**: ✅ **FIXED** - Previously, CSV files with empty cells could cause numeric columns to get `.0` added (e.g., `7131525` became `7131525.0`). This has been resolved by improving how the processor handles missing values.

### Glossary Behavior

The glossary supports case-sensitive term replacement:
- **`keep_case=True`**: Always uses the target term exactly as specified (e.g., "KIT;KIT;True" will always replace any case variation with "KIT")
- **`keep_case=False`**: Adapts the target case to match the original text pattern

Example:
```csv
# glossary.csv
source;target;keep_case
KIT;KIT;True
ajax;AJAX;False
```

With this glossary:
- "kit", "Kit", "KIT" all become "KIT" (keep_case=True)
- "Ajax" becomes "AJAX", "ajax" becomes "ajax" (keep_case=False adapts to original case)
