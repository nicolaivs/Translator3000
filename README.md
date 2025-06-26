# CSV Translation Script

A Python script for translating CSV file columns from English to Dutch using the free Google Translate API.

## Features

- 🌐 **Free Translation**: Uses Google Translate API through the `deep-translator` library (no API key required)
- 📊 **CSV Processing**: Reads and processes CSV files with pandas
- 🔄 **Batch Translation**: Translates multiple columns efficiently
- 📝 **Preserves Data**: Keeps original columns and adds translated versions
- 🛡️ **Error Handling**: Graceful handling of translation failures
- 📊 **Progress Tracking**: Real-time progress updates and logging
- ⚡ **Rate Limiting**: Built-in delays to avoid API throttling
- 🔧 **Delimiter Choice**: Support for both comma (,) and semicolon (;) delimited CSV files
- 📁 **Organized Workflow**: Automatic source/target folder management

## Project Structure

```
CSV Translator/
├── source/           # Place your CSV files here for translation
├── target/           # Translated files are saved here
├── csv_translator.py # Main translation script
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Installation

1. **Clone or download this project**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: If you encounter a `No module named 'cgi'` error with `googletrans`, don't worry! The script automatically uses the more reliable `deep-translator` library instead.

3. **Test your setup** (recommended):
   ```bash
   python test_setup.py
   ```

## Usage

### Quick Start

1. **Place your CSV files** in the `source/` folder
2. **Run the script**:
   ```bash
   python csv_translator.py
   ```
3. **Follow the prompts** to select files and columns to translate
4. **Find your translated files** in the `target/` folder

### Interactive Mode (Detailed)

1. Run the script:
   ```bash
   python csv_translator.py
   ```

2. The script will:
   - Automatically show CSV files in the `source/` folder
   - Let you choose which file to translate
   - Show available columns in your CSV
   - Ask which columns you want to translate
   - Save the translated file to the `target/` folder

### Programmatic Usage

For automated processing, modify the main function in `csv_translator.py`:

```python
# Example: Translate specific columns
translator = CSVTranslator(delay_between_requests=0.1)
success = translator.translate_csv(
    input_file="products.csv",
    output_file="products_translated.csv",
    columns_to_translate=["name", "description"]
)
```

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

### Translation Parameters

- **Source Language**: English (`en`)
- **Target Language**: Dutch - Netherlands (`nl`)
- **Rate Limiting**: 0.1 seconds between requests (configurable)
- **Error Handling**: Returns original text if translation fails

### Customization Options

You can modify the `CSVTranslator` class to:
- Change source/target languages
- Adjust rate limiting delays
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
├── csv_translator.py          # Main translation script
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
