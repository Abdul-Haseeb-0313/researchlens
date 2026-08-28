#!/usr/bin/env python3
"""
Print directory contents with full paths and file contents,
skipping specified directories and binary files.
Usage:
    python print_dir_contents.py [directory]
"""

import os
import sys

EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'node_modules'}

# Common binary / non-text extensions to skip
BINARY_EXTENSIONS = {
    '.pdf', '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.bmp',
    '.ico', '.zip', '.tar', '.gz', '.7z', '.exe', '.dll',
    '.so', '.dylib', '.db', '.sqlite', '.mp3', '.mp4', '.avi',
    '.mov', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
}

def is_binary(filepath):
    """Return True if file has a binary extension or contains null bytes."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    # Additional check: read first 1024 bytes and look for null byte
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
    except Exception:
        return True
    return False

def print_directory_contents(startpath):
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            filepath = os.path.join(root, file)
            if is_binary(filepath):
                print(f"--- {filepath} ---")
                print("[Skipped binary file]")
                print()
                continue
            print(f"--- {filepath} ---")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    print(f.read())
            except Exception as e:
                print(f"[Error reading file: {e}]")
            print()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    print_directory_contents(path)