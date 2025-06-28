# Glossary Feature

## Overview
The glossary feature allows you to define custom translations for specific terms that should always be translated the same way, regardless of context.

## Files

### `glossary.csv`
Your personal glossary file (not tracked by git). Create this file to define your custom translations.

### `glossary.csv.sample`
Sample glossary file showing the format and example entries.

## Format

The glossary uses a CSV format with semicolon separators and three columns:

```
source;target;keep_case
```

- **source**: The original term to find (case-insensitive matching)
- **target**: The replacement term  
- **keep_case**: True/False - whether to preserve the original case pattern

## Examples

```csv
source;target;keep_case
ajax;AJAX;False
javascript;JavaScript;True
api;API;False
json;JSON;False
```

### Case Handling Examples:

**keep_case = False (use target as-is):**
- "ajax" → "AJAX"
- "Ajax" → "AJAX"  
- "AJAX" → "AJAX"

**keep_case = True (preserve original case):**
- "javascript" → "javascript"
- "Javascript" → "Javascript"
- "JAVASCRIPT" → "JAVASCRIPT"

## Usage

1. Copy `glossary.csv.sample` to `glossary.csv`
2. Add your custom terms
3. Run the translator - glossary terms will be applied before translation

## Notes

- Only whole words are matched (word boundaries)
- Case-insensitive matching for finding terms
- Comments start with `#`
- Empty lines are ignored
- The `glossary.csv` file is ignored by git (user-specific)
