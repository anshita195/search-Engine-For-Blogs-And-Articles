#!/usr/bin/env python3
"""
Personal Blog Search Engine API
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import json
from pathlib import Path
import sys
import time

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

app = FastAPI(title="Personal Blog Search Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Search engines
from api.cached_search import search_engine
from api.metrics import record_search_operation, get_metrics
SEMANTIC_SEARCH = None

def load_search_index():
    """Load search index from file."""
    global SEMANTIC_SEARCH
    try:
        # Load cached search engine
        search_engine.load_index()
        print(f"📚 Loaded {len(search_engine.search_index)} documents into memory")
        
        # Initialize semantic search
        try:
            from api.semantic_search import SemanticSearch
            SEMANTIC_SEARCH = SemanticSearch()
            SEMANTIC_SEARCH.load_or_create_embeddings(search_engine.search_index)
            print("🧠 Semantic search initialized")
        except Exception as e:
            print(f"⚠️ Semantic search not available: {e}")
            SEMANTIC_SEARCH = None
    except Exception as e:
        print(f"❌ Failed to load search index: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the search interface."""
    ui_file = Path("ui/index.html")
    if ui_file.exists():
        with open(ui_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
        <body>
            <h1>Personal Blog Search Engine</h1>
            <p>API is running! Search interface not found.</p>
            <p>Try: <a href="/api/search?q=programming">/api/search?q=programming</a></p>
        </body>
        </html>
        """)

@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    use_semantic: bool = Query(False, description="Use semantic search"),
    limit: int = Query(10, description="Number of results to return"),
    page: int = Query(1, description="Page number"),
    domain: str = Query(None, description="Filter by domain")
):
    """Search for personal blogs with optional semantic search and pagination."""
    if not search_engine.loaded:
        load_search_index()
    
    # Calculate offset for pagination
    offset = (page - 1) * limit
    
    # Use cached search engine for fast results
    result = search_engine.search(q, domain_filter=domain, limit=limit, offset=offset)
    
    # Apply semantic search as fallback when basic search returns too few results
    if SEMANTIC_SEARCH and (len(result["results"]) < limit * 0.8):  # Less than 80% of requested results
        try:
            print(f"🔍 Basic search found {len(result['results'])} results, using semantic fallback...")
            
            # Use semantic search to find additional results
            semantic_results = SEMANTIC_SEARCH.search(q, top_k=limit*2)
            
            # Combine results, prioritizing basic search results
            basic_urls = {r['url'] for r in result["results"]}
            combined_results = []
            
            # Add basic search results first (higher priority)
            combined_results.extend(result["results"])
            
            # Add semantic-only results
            for sem_result in semantic_results:
                if sem_result['url'] not in basic_urls:
                    combined_results.append(sem_result)
            
            result["results"] = combined_results[:limit]
            result["semantic_used"] = True
            result["search_strategy"] = "basic_with_semantic_fallback"
        except Exception as e:
            print(f"⚠️ Semantic search failed: {e}")
            result["semantic_used"] = False
            result["search_strategy"] = "basic_only"
    else:
        result["semantic_used"] = False
        result["search_strategy"] = "basic_only"
    
    # Record metrics
    record_search_operation(
        query=q,
        success=True,
        search_time_ms=result["search_time_ms"],
        cache_hit=result.get("cached", False),
        semantic_used=result.get("semantic_used", False)
    )
    
    return result

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    if not search_engine.loaded:
        load_search_index()
    
    stats = search_engine.get_stats()
    return {
        "status": "healthy",
        "search_index_size": stats["total_documents"],
        "total_domains": stats["total_domains"],
        "cache_hits": stats["cache_info"].hits,
        "cache_misses": stats["cache_info"].misses
    }

@app.get("/api/domains")
async def get_domains():
    """Get list of available domains for filtering."""
    if not search_engine.loaded:
        load_search_index()
    
    domains = search_engine.get_domains()
    return {
        "domains": sorted(domains),
        "total_domains": len(domains)
    }

@app.get("/api/metrics")
async def get_metrics_endpoint():
    """Get search engine metrics and performance statistics."""
    return get_metrics()

if __name__ == "__main__":
    import uvicorn
    load_search_index()
    uvicorn.run(app, host="0.0.0.0", port=8001) 