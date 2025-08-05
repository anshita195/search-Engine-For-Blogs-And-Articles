#!/usr/bin/env python3
"""
Compare Basic vs Semantic Search
"""

import requests
import time
import json

def compare_searches(query):
    """Compare basic vs semantic search for a query."""
    print(f"\n🔍 Testing: '{query}'")
    print("=" * 50)
    
    # Test basic search
    start_time = time.time()
    basic_response = requests.get("http://localhost:8001/api/search", params={"q": query})
    basic_time = (time.time() - start_time) * 1000
    
    if basic_response.status_code == 200:
        basic_data = basic_response.json()
        print(f"✅ Basic search: {basic_data['search_time_ms']}ms, {len(basic_data['results'])} results")
        
        # Show first 3 results
        for i, result in enumerate(basic_data['results'][:3]):
            print(f"  {i+1}. {result['title'][:60]}... ({result['domain']})")
    else:
        print(f"❌ Basic search failed: {basic_response.status_code}")
        return
    
    # Test semantic search
    start_time = time.time()
    semantic_response = requests.get("http://localhost:8001/api/search", 
                                   params={"q": query, "use_semantic": "true"})
    semantic_time = (time.time() - start_time) * 1000
    
    if semantic_response.status_code == 200:
        semantic_data = semantic_response.json()
        print(f"🧠 Semantic search: {semantic_data['search_time_ms']}ms, {len(semantic_data['results'])} results")
        
        # Show first 3 results
        for i, result in enumerate(semantic_data['results'][:3]):
            print(f"  {i+1}. {result['title'][:60]}... ({result['domain']})")
        
        # Compare results
        basic_urls = {r['url'] for r in basic_data['results']}
        semantic_urls = {r['url'] for r in semantic_data['results']}
        
        overlap = len(basic_urls.intersection(semantic_urls))
        print(f"\n📊 Comparison:")
        print(f"  Basic results: {len(basic_urls)}")
        print(f"  Semantic results: {len(semantic_urls)}")
        print(f"  Overlap: {overlap}")
        
        if len(basic_urls) > 0:
            print(f"  Overlap percentage: {overlap/len(basic_urls)*100:.1f}%")
        else:
            print(f"  Overlap percentage: N/A (no basic results)")
            
        print(f"  Performance difference: {semantic_time - basic_time:.1f}ms")
        
        if len(basic_urls) == 0 and len(semantic_urls) == 0:
            print("🤔 No results found for either search.")
        elif overlap == len(basic_urls) and overlap == len(semantic_urls) and len(basic_urls) > 0:
            print("⚠️  WARNING: Results are identical! Semantic search may not be working properly.")
        elif overlap < len(basic_urls) * 0.5:
            print("✅ Semantic search is providing different results!")
        else:
            print("🤔 Semantic search has some overlap but not identical.")
    else:
        print(f"❌ Semantic search failed: {semantic_response.status_code}")

if __name__ == "__main__":
    test_queries = [
        "programming",
        "python",
        "machine learning", 
        "career advice",
        "personal experience"
    ]
    
    for query in test_queries:
        compare_searches(query) 