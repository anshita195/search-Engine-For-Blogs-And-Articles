#!/usr/bin/env python3
"""
Personal Blog Search Engine API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import json
from pathlib import Path
import sys

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

def load_search_index():
    """Load search index from file."""
    global SEARCH_INDEX
    try:
        index_file = Path("data/search_index.json")
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                SEARCH_INDEX = json.load(f)
            print(f"📚 Loaded {len(SEARCH_INDEX)} documents")
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
async def search(q: str):
    """Search for personal blogs."""
    if not SEARCH_INDEX:
        load_search_index()
    
    query_lower = q.lower()
    matching_results = []
    
    for doc in SEARCH_INDEX:
        if (query_lower in doc.get('title', '').lower() or 
            query_lower in doc.get('content', '').lower()):
            matching_results.append(doc)
    
    return {
        "query": q,
        "results": matching_results[:10],  # Limit to 10 results
        "total_results": len(matching_results)
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