#!/usr/bin/env python3
"""
Prometheus Metrics for Search Engine
Tracks performance, usage, and health metrics
"""

import time
from typing import Dict, Any
from dataclasses import dataclass
from collections import defaultdict, Counter

@dataclass
class SearchMetrics:
    """Metrics for search operations."""
    total_searches: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    avg_search_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    semantic_fallbacks: int = 0
    basic_only_searches: int = 0
    
    # Query statistics
    popular_queries: Counter = None
    search_times: list = None
    
    def __post_init__(self):
        if self.popular_queries is None:
            self.popular_queries = Counter()
        if self.search_times is None:
            self.search_times = []
    
    def record_search(self, query: str, success: bool, search_time_ms: float, 
                     cache_hit: bool, semantic_used: bool):
        """Record a search operation."""
        self.total_searches += 1
        
        if success:
            self.successful_searches += 1
        else:
            self.failed_searches += 1
        
        # Track search time
        self.search_times.append(search_time_ms)
        if len(self.search_times) > 1000:  # Keep last 1000 searches
            self.search_times.pop(0)
        
        # Update average
        self.avg_search_time_ms = sum(self.search_times) / len(self.search_times)
        
        # Track cache performance
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        # Track search strategy
        if semantic_used:
            self.semantic_fallbacks += 1
        else:
            self.basic_only_searches += 1
        
        # Track popular queries
        self.popular_queries[query.lower()] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics as dictionary."""
        cache_hit_rate = 0.0
        if self.cache_hits + self.cache_misses > 0:
            cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) * 100
        
        success_rate = 0.0
        if self.total_searches > 0:
            success_rate = self.successful_searches / self.total_searches * 100
        
        return {
            "total_searches": self.total_searches,
            "successful_searches": self.successful_searches,
            "failed_searches": self.failed_searches,
            "success_rate_percent": round(success_rate, 2),
            "avg_search_time_ms": round(self.avg_search_time_ms, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "semantic_fallbacks": self.semantic_fallbacks,
            "basic_only_searches": self.basic_only_searches,
            "popular_queries": dict(self.popular_queries.most_common(10)),
            "recent_search_times": self.search_times[-10:] if self.search_times else []
        }

# Global metrics instance
search_metrics = SearchMetrics()

def record_search_operation(query: str, success: bool, search_time_ms: float, 
                          cache_hit: bool, semantic_used: bool):
    """Record a search operation in metrics."""
    search_metrics.record_search(query, success, search_time_ms, cache_hit, semantic_used)

def get_metrics() -> Dict[str, Any]:
    """Get current metrics."""
    return search_metrics.get_stats() 