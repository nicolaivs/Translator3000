#!/usr/bin/env python3
"""
Script to fix import paths in all test and demo scripts.
"""

import os
import glob

# Path fix code to add at the top of scripts
PATH_FIX = """import sys
import os
# Add parent directory to path so we can import translator3000
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

"""

def fix_script(file_path):
    """Fix a single script file."""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already fixed
    if "sys.path.insert" in content:
        print(f"  Already fixed, skipping.")
        return
    
    lines = content.split('\n')
    
    # Find the docstring end and the first import
    import_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('from translator3000 import') or line.strip().startswith('import translator3000'):
            import_line_idx = i
            break
    
    if import_line_idx is None:
        print(f"  No translator3000 import found, skipping.")
        return
    
    # Insert the path fix before the translator3000 import
    path_fix_lines = PATH_FIX.strip().split('\n')
    
    # Insert the path fix
    lines = lines[:import_line_idx] + path_fix_lines + [''] + lines[import_line_idx:]
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"  Fixed!")

def main():
    """Fix all test and demo scripts."""
    
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Find all test scripts
    test_scripts = glob.glob(os.path.join(project_root, 'test', '*.py'))
    demo_scripts = glob.glob(os.path.join(project_root, 'demo', '*.py'))
    
    all_scripts = test_scripts + demo_scripts
    
    print(f"Found {len(all_scripts)} scripts to fix:")
    
    for script in all_scripts:
        # Skip README and __init__ files
        if 'README' in script or '__init__' in script:
            continue
        fix_script(script)
    
    print(f"\nDone! Fixed imports for {len(all_scripts)} scripts.")

if __name__ == "__main__":
    main()
