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

# Mock search index
SEARCH_INDEX = []
SEMANTIC_SEARCH = None

def load_search_index():
    """Load search index from file."""
    global SEARCH_INDEX, SEMANTIC_SEARCH
    try:
        index_file = Path("data/search_index.json")
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                SEARCH_INDEX = json.load(f)
                print(f"📚 Loaded {len(SEARCH_INDEX)} documents")
                
                # Initialize semantic search
                try:
                    from api.semantic_search import SemanticSearch
                    SEMANTIC_SEARCH = SemanticSearch()
                    SEMANTIC_SEARCH.load_or_create_embeddings(SEARCH_INDEX)
                    print("🧠 Semantic search initialized")
                except Exception as e:
                    print(f"⚠️ Semantic search not available: {e}")
                    SEMANTIC_SEARCH = None
        else:
            print("⚠️ No search index found")
            SEARCH_INDEX = []
    except Exception as e:
        print(f"❌ Failed to load search index: {e}")
        SEARCH_INDEX = []

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
    limit: int = Query(10, description="Number of results to return")
):
    """Search for personal blogs with optional semantic search."""
    if not SEARCH_INDEX:
        load_search_index()
    
    start_time = time.time()
    
    # Keyword search
    query_lower = q.lower()
    keyword_results = []
    
    for doc in SEARCH_INDEX:
        if (query_lower in doc.get('title', '').lower() or 
            query_lower in doc.get('content', '').lower()):
            keyword_results.append(doc)
    
    # Apply semantic search if requested and available
    if use_semantic and SEMANTIC_SEARCH:
        try:
            results = SEMANTIC_SEARCH.hybrid_search(q, keyword_results, top_k=limit)
        except Exception as e:
            print(f"⚠️ Semantic search failed: {e}")
            results = keyword_results[:limit]
    else:
        results = keyword_results[:limit]
    
    search_time = time.time() - start_time
    
    return {
        "query": q,
        "results": results,
        "total_results": len(keyword_results),
        "search_time_ms": round(search_time * 1000, 2),
        "semantic_used": use_semantic and SEMANTIC_SEARCH is not None
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "search_index_size": len(SEARCH_INDEX)
    }

if __name__ == "__main__":
    import uvicorn
    load_search_index()
    uvicorn.run(app, host="0.0.0.0", port=8001) 