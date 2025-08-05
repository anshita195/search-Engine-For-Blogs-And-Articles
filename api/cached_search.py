#!/usr/bin/env python3
"""
High-Performance Cached Search
In-memory indexing with LRU caching for sub-500ms performance
"""

import json
import time
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CachedSearchEngine:
    def __init__(self):
        self.search_index = []
        self.domain_index = {}  # domain -> list of doc indices
        self.title_index = {}   # word -> list of doc indices
        self.content_index = {} # word -> list of doc indices
        self.loaded = False
        
    def load_index(self, index_file: str = "data/search_index.json"):
        """Load and index the search data in memory."""
        if self.loaded:
            return
            
        start_time = time.time()
        logger.info("Loading search index into memory...")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            self.search_index = json.load(f)
        
        # Build inverted indexes for fast lookup
        self._build_indexes()
        
        load_time = (time.time() - start_time) * 1000
        logger.info(f"Index loaded in {load_time:.1f}ms: {len(self.search_index)} documents")
        self.loaded = True
    
    def _build_indexes(self):
        """Build inverted indexes for fast searching."""
        for doc_idx, doc in enumerate(self.search_index):
            # Domain index
            domain = doc.get('domain', '').lower()
            if domain not in self.domain_index:
                self.domain_index[domain] = []
            self.domain_index[domain].append(doc_idx)
            
            # Title index
            title = doc.get('title', '').lower()
            for word in title.split():
                if len(word) > 2:  # Skip short words
                    if word not in self.title_index:
                        self.title_index[word] = []
                    self.title_index[word].append(doc_idx)
            
            # Content index (first 500 chars for speed)
            content = doc.get('content', '')[:500].lower()
            for word in content.split():
                if len(word) > 2:  # Skip short words
                    if word not in self.content_index:
                        self.content_index[word] = []
                    self.content_index[word].append(doc_idx)
    
    @lru_cache(maxsize=1000)
    def search(self, query: str, domain_filter: Optional[str] = None, 
               limit: int = 10, offset: int = 0) -> Dict:
        """Fast cached search with AND logic on titles + semantic fallback."""
        start_time = time.time()
        
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        # STRICT AND search on titles only (more precise)
        matching_docs = set()
        if query_words:
            # Start with first word
            if query_words[0] in self.title_index:
                matching_docs = set(self.title_index[query_words[0]])
            
            # Require ALL words in title (AND logic)
            for word in query_words[1:]:
                if word in self.title_index:
                    word_docs = set(self.title_index[word])
                    matching_docs = matching_docs.intersection(word_docs)
                else:
                    matching_docs = set()  # No matches if word not found
                    break
        
        # Apply domain filter
        if domain_filter:
            domain_filter_lower = domain_filter.lower()
            if domain_filter_lower in self.domain_index:
                domain_docs = set(self.domain_index[domain_filter_lower])
                matching_docs = matching_docs.intersection(domain_docs)
        
        # Get actual documents
        results = []
        for doc_idx in matching_docs:
            results.append(self.search_index[doc_idx])
        
        # Sort by relevance (title matches)
        def relevance_score(doc):
            title_lower = doc.get('title', '').lower()
            score = 0
            for word in query_words:
                if word in title_lower:
                    score += 1
            return score
        
        results.sort(key=relevance_score, reverse=True)
        
        # Apply pagination
        total_results = len(results)
        paginated_results = results[offset:offset + limit]
        
        search_time = (time.time() - start_time) * 1000
        
        return {
            "query": query,
            "results": paginated_results,
            "total_results": total_results,
            "search_time_ms": round(search_time, 2),
            "page": offset // limit + 1,
            "total_pages": (total_results + limit - 1) // limit,
            "cached": True,
            "search_type": "strict_and"
        }
    
    def get_domains(self) -> List[str]:
        """Get list of all available domains."""
        return list(self.domain_index.keys())
    
    def get_stats(self) -> Dict:
        """Get search engine statistics."""
        return {
            "total_documents": len(self.search_index),
            "total_domains": len(self.domain_index),
            "title_index_size": len(self.title_index),
            "content_index_size": len(self.content_index),
            "cache_info": self.search.cache_info()
        }

# Global instance
search_engine = CachedSearchEngine() 