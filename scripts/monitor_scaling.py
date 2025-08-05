#!/usr/bin/env python3
"""
Monitor Scaling Progress
Real-time monitoring of blog scaling progress
"""

import json
import time
from pathlib import Path

def get_current_stats():
    """Get current scaling statistics."""
    search_index_path = Path("data/search_index.json")
    if not search_index_path.exists():
        return {"count": 0, "progress": 0}
    
    with open(search_index_path, 'r') as f:
        search_index = json.load(f)
    
    count = len(search_index)
    progress = (count / 1000) * 100
    
    return {
        "count": count,
        "progress": progress,
        "target": 1000,
        "remaining": 1000 - count
    }

def monitor_progress():
    """Monitor scaling progress in real-time."""
    print("📊 PERSONAL BLOG SCALING MONITOR")
    print("=" * 50)
    print("Target: 1000 personal blogs")
    print("Monitoring every 30 seconds...")
    print()
    
    last_count = 0
    
    while True:
        stats = get_current_stats()
        current_count = stats["count"]
        
        # Show progress bar
        progress_bar_length = 40
        filled_length = int((current_count / 1000) * progress_bar_length)
        bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
        
        # Calculate rate of change
        if last_count > 0:
            rate = current_count - last_count
            rate_text = f"(+{rate} this check)" if rate > 0 else "(no change)"
        else:
            rate_text = ""
        
        # Clear screen and show updated stats
        print(f"\033[2J\033[H")  # Clear screen
        print("📊 PERSONAL BLOG SCALING MONITOR")
        print("=" * 50)
        print(f"🎯 Target: 1000 personal blogs")
        print(f"📈 Current: {current_count} blogs")
        print(f"📊 Progress: {stats['progress']:.1f}%")
        print(f"⏳ Remaining: {stats['remaining']} blogs")
        print()
        print(f"[{bar}] {current_count}/1000 {rate_text}")
        print()
        
        if current_count >= 1000:
            print("🎉 TARGET REACHED! 1000 PERSONAL BLOGS!")
            print("🚀 Your search engine is now production-ready!")
            break
        
        last_count = current_count
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    try:
        monitor_progress()
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
        stats = get_current_stats()
        print(f"📊 Final count: {stats['count']} personal blogs") 