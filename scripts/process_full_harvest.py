#!/usr/bin/env python3
"""
Process Full-Scale Harvest Results
Apply sharpened filters and classification to harvested URLs.
"""

import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.improved_scaling import process_urls_with_improved_filtering, get_existing_urls

def process_full_harvest():
    """Process URLs from full-scale domain harvesting."""
    print("🚀 PROCESSING FULL-SCALE HARVEST RESULTS")
    print("=" * 50)
    
    # Load harvested URLs
    harvest_file = Path("data/full_scale_harvest_results.json")
    if not harvest_file.exists():
        print("❌ No full-scale harvest results found! Run full_scale_harvest.py first")
        return
    
    with open(harvest_file, 'r') as f:
        harvest_data = json.load(f)
    
    harvested_urls = harvest_data.get('blogroll_links', [])
    print(f"📊 Loaded {len(harvested_urls)} harvested URLs")
    
    if not harvested_urls:
        print("❌ No URLs to process!")
        return
    
    # Get existing URLs for duplicate prevention
    existing_urls = get_existing_urls()
    
    # Process URLs with improved filtering and classification
    auto_added, review_count = process_urls_with_improved_filtering(harvested_urls, existing_urls)
    
    print(f"\n🎯 FULL-SCALE HARVEST PROCESSING RESULTS:")
    print(f"✅ Auto-added: {auto_added} high-confidence blogs")
    print(f"🔍 Review candidates: {review_count} medium-confidence blogs")
    print(f"📊 Total processed: {len(harvested_urls)} URLs")
    
    # Calculate success rate
    if len(harvested_urls) > 0:
        success_rate = (auto_added / len(harvested_urls)) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")
    
    # Show current index size
    search_index_file = Path("data/search_index.json")
    if search_index_file.exists():
        with open(search_index_file, 'r') as f:
            current_data = json.load(f)
        print(f"📊 Current index size: {len(current_data)} blogs")
        
        # Check if we're approaching 1000
        if len(current_data) >= 1000:
            print(f"🎉 TARGET ACHIEVED! Index has {len(current_data)} blogs!")
        else:
            remaining = 1000 - len(current_data)
            print(f"🎯 {remaining} more blogs needed to reach 1000")

if __name__ == "__main__":
    process_full_harvest() 