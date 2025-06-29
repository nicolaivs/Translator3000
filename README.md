# Translator3000 - Multi-Language CSV & XML Translation Script

A powerful Python script for translating CSV file columns and XML text content between multiple languages using the free Google Translate API. Supports both single-file and batch processing modes.

## Features

- 🌐 **Multi-Language Support**: Translate between 10 supported languages
- 🔄 **Dynamic Language Selection**: Choose source and target languages at runtime
- 📊 **CSV Processing**: Reads and processes CSV files with pandas
- 🏷️ **XML Processing**: Translates XML text content while preserving structure and attributes
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

## Configuration

The script includes a powerful configuration system via the `translator3000.config` file:

### Initial Setup

1. **Copy the sample config**: `copy translator3000.config.sample translator3000.config`
2. **Edit your settings**: Add API keys and customize performance settings
3. **Secure by default**: The main config file is git-ignored to protect sensitive settings

### Performance Settings (Optimized)

- **API Delay**: 5ms between requests (optimized for best performance)
- **Multithreading**: 4 workers for CSV/XML processing  
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Error Handling**: Graceful fallback to original text on translation failure

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

### Logging

The script creates a `translation.log` file with detailed information about:
- Translation progress
- Error messages
- Performance metrics

## Performance Tips

- **Batch size**: Process large files in smaller chunks if needed
- **Rate limiting**: Increase delay between requests if you encounter throttling
- **Caching**: Consider implementing translation caching for repeated text
- **Parallel processing**: For very large datasets, consider implementing parallel translation

## License

This project is open source. The `googletrans` library is subject to Google's Terms of Service.

## Contributing

Feel free to submit issues and enhancement requests!

### Local LibreTranslate Setup (Optional - High Performance)

For **8-15x faster translation** and complete privacy, you can run LibreTranslate locally using Docker:

```bash
# Quick setup - run LibreTranslate on localhost:5000
docker run -p 5000:5000 libretranslate/libretranslate
```

**Benefits:**
- 🚀 **8-15x faster** than cloud services
- 🔒 **Complete privacy** - data never leaves your machine  
- 💰 **No rate limits** - translate as much as you want
- 🌐 **Works offline** - no internet required

Translator3000 **automatically detects** and prioritizes self hosted instances. When self hosted is available, it becomes the primary translation service!

📖 **Detailed setup guide**: See [LOCALHOST_SETUP.md](LOCALHOST_SETUP.md) for complete Docker configuration options.
