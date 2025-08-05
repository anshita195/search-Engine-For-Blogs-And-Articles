#!/usr/bin/env python3
"""
Fix Search Index Encoding Issues
Read the corrupted search_index.json and rewrite it with proper UTF-8 encoding
"""

import json
import sys
from pathlib import Path

def fix_search_index_encoding():
    """Fix encoding issues in search_index.json"""
    print("🔧 FIXING SEARCH INDEX ENCODING")
    print("=" * 50)
    
    search_index_file = Path("data/search_index.json")
    backup_file = Path("data/search_index_backup.json")
    
    if not search_index_file.exists():
        print("❌ search_index.json not found!")
        return
    
    # Try different encoding approaches
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    data = None
    used_encoding = None
    
    for encoding in encodings_to_try:
        try:
            print(f"🔍 Trying encoding: {encoding}")
            with open(search_index_file, 'r', encoding=encoding) as f:
                content = f.read()
                data = json.loads(content)
                used_encoding = encoding
                print(f"✅ Successfully read with {encoding} encoding")
                break
        except UnicodeDecodeError as e:
            print(f"❌ Failed with {encoding}: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode failed with {encoding}: {e}")
            continue
    
    if data is None:
        print("❌ Could not read the file with any encoding!")
        return
    
    print(f"📊 Loaded {len(data)} documents from search index")
    
    # Clean the data by removing problematic characters
    def clean_text(text):
        if not isinstance(text, str):
            return text
        
        # Replace common encoding artifacts
        replacements = {
            'Ã¢â‚¬â€': '—',  # em dash
            'Ã¢â‚¬â€œ': '–',  # en dash
            'Ã¢â‚¬â„¢': "'",  # right single quote~
            'Ã¢â‚¬Å"': '"',   # right double quote
            'Ã¢â‚¬Å"': '"',   # left double quote
            'Ã¢â‚¬â¢': '•',   # bullet
            'Ã¢â‚¬Â¦': '…',   # ellipsis
            'Ã¢â‚¬Â': '"',    # right double quote
            'Ã¢â‚¬Â': '"',    # left double quote
            'Ã¢â‚¬â¢': '•',   # bullet
            'Ã¢â‚¬Â¦': '…',   # ellipsis
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    # Clean all text fields in the data
    cleaned_data = []
    for item in data:
        cleaned_item = {}
        for key, value in item.items():
            if isinstance(value, str):
                cleaned_item[key] = clean_text(value)
            else:
                cleaned_item[key] = value
        cleaned_data.append(cleaned_item)
    
    # Write back with proper UTF-8 encoding
    output_file = Path("data/search_index_fixed.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Fixed search index saved to: {output_file}")
    print(f"📊 {len(cleaned_data)} documents processed")
    
    # Replace the original file
    if backup_file.exists():
        print("🔄 Replacing original file with fixed version...")
        search_index_file.unlink()  # Remove original
        output_file.rename(search_index_file)  # Rename fixed to original
        print("✅ Original file replaced with fixed version")
    else:
        print(f"💾 Fixed file saved as: {output_file}")
        print("⚠️ Original file preserved as backup")
    
    # Show sample of cleaned data
    print(f"\n📋 Sample cleaned document:")
    if cleaned_data:
        sample = cleaned_data[0]
        print(f"Title: {sample.get('title', 'N/A')[:100]}...")
        print(f"URL: {sample.get('url', 'N/A')}")
        print(f"Domain: {sample.get('domain', 'N/A')}")

if __name__ == "__main__":
    fix_search_index_encoding() 