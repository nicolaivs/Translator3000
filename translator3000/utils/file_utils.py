"""
File discovery and processing utilities for Translator3000.

This module contains helper functions for discovering files in directories,
handling file processing modes, and managing input/output paths.
"""

from typing import Dict, List, Any
from pathlib import Path
import os


def discover_files_and_folders(source_dir: Path) -> Dict[str, Any]:
    """
    Discover all CSV and XML files in source directory, including subdirectories.
    
    Args:
        source_dir: Source directory to scan
    
    Returns:
        Dictionary with structure: {
            'root_files': [list of files in root source dir],
            'folders': {
                'folder_name': [list of files in that folder],
                ...
            }
        }
    """
    discovered = {
        'root_files': [],
        'folders': {}
    }
    
    # Find files in root source directory
    for file_path in source_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.xml']:
            discovered['root_files'].append(file_path)
    
    # Find subdirectories and their files
    for item in source_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            folder_files = []
            # Look for CSV/XML files in subdirectory
            for file_path in item.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.xml']:
                    folder_files.append(file_path)
            
            if folder_files:  # Only include folders that have CSV/XML files
                discovered['folders'][item.name] = folder_files
    
    return discovered


def print_discovered_files(discovered: Dict[str, List[Path]], source_dir: Path) -> int:
    """
    Print discovered files and return total count.
    
    Args:
        discovered: Dictionary from discover_files_and_folders()
        source_dir: Source directory for relative path calculation
        
    Returns:
        Total number of files found
    """
    total_files = 0
    
    # Print root files
    if discovered['root_files']:
        print("[ROOT] Files in source root:")
        for file_path in discovered['root_files']:
            file_type = "CSV" if file_path.suffix.lower() == ".csv" else "XML"
            print(f"  • {file_path.name} ({file_type})")
            total_files += 1
        print()
    
    # Print folder contents
    if discovered['folders']:
        print("[SUBDIRS] Files in subdirectories:")
        for folder_name, files in discovered['folders'].items():
            print(f"  [FOLDER] {folder_name}/")
            for file_path in files:
                file_type = "CSV" if file_path.suffix.lower() == ".csv" else "XML"
                relative_path = file_path.relative_to(source_dir / folder_name)
                print(f"    • {relative_path} ({file_type})")
                total_files += 1
            print()
    
    return total_files


def ensure_directory_exists(directory: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        return False


def is_supported_file(file_path: Path) -> bool:
    """
    Check if a file is supported for translation.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file has .csv or .xml extension
    """
    return file_path.suffix.lower() in ['.csv', '.xml']


def get_relative_path(file_path: Path, base_dir: Path) -> str:
    """
    Get relative path string from base directory.
    
    Args:
        file_path: Full path to file
        base_dir: Base directory to calculate relative path from
        
    Returns:
        Relative path as string
    """
    try:
        return str(file_path.relative_to(base_dir))
    except ValueError:
        # If file is not under base_dir, return just the filename
        return file_path.name
