#!/usr/bin/env python3
"""
Fix duplicate URLs in search index
"""

import json
from pathlib import Path

def fix_duplicates():
    """Remove duplicate URLs from search index."""
    print("🔧 FIXING DUPLICATES IN SEARCH INDEX")
    print("=" * 50)
    
    # Load current search index
    search_index_file = Path("data/search_index.json")
    if not search_index_file.exists():
        print("❌ Search index file not found!")
        return
    
    with open(search_index_file, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Original blogs: {len(data)}")
    
    # Remove duplicates
    unique_data = []
    seen_urls = set()
    duplicates_removed = 0
    
    for blog in data:
        if blog['url'] not in seen_urls:
            unique_data.append(blog)
            seen_urls.add(blog['url'])
        else:
            duplicates_removed += 1
            print(f"   🗑️ Removed duplicate: {blog['url']}")
    
    print(f"📊 After deduplication: {len(unique_data)} blogs")
    print(f"🗑️ Duplicates removed: {duplicates_removed}")
    
    # Save deduplicated index
    with open(search_index_file, 'w') as f:
        json.dump(unique_data, f, indent=2)
    
    print(f"✅ Deduplicated index saved to: {search_index_file}")
    
    # Verify no duplicates remain
    urls = [blog['url'] for blog in unique_data]
    unique_urls = set(urls)
    print(f"🔍 Verification - Unique URLs: {len(unique_urls)}")
    print(f"🔍 Verification - Total blogs: {len(unique_data)}")
    
    if len(unique_urls) == len(unique_data):
        print("✅ No duplicates remain!")
    else:
        print("❌ Still have duplicates!")

if __name__ == "__main__":
    fix_duplicates() 