#!/usr/bin/env python3
"""
Semantic Search Module
Uses sentence transformers for semantic similarity search
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
import pickle
import logging

logger = logging.getLogger(__name__)

class SemanticSearch:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Initialize semantic search with sentence transformer model."""
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.documents = None
        self.embeddings_file = Path("data/document_embeddings.pkl")
        
    def load_or_create_embeddings(self, search_index):
        """Load existing embeddings or create new ones."""
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data['embeddings']
                    self.documents = data['documents']
                logger.info(f"Loaded {len(self.documents)} existing embeddings")
                return
            except Exception as e:
                logger.warning(f"Failed to load embeddings: {e}")
        
        # Create new embeddings
        logger.info("Creating new embeddings...")
        self.create_embeddings(search_index)
    
    def create_embeddings(self, search_index):
        """Create embeddings for all documents in search index."""
        documents = []
        for doc in search_index:
            # Combine title and content for better semantic matching
            text = f"{doc.get('title', '')} {doc.get('content', '')[:500]}"
            documents.append({
                'id': len(documents),
                'text': text,
                'doc': doc
            })
        
        # Generate embeddings
        texts = [doc['text'] for doc in documents]
        self.embeddings = self.model.encode(texts, show_progress_bar=True)
        self.documents = documents
        
        # Save embeddings
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'documents': self.documents
            }, f)
        
        logger.info(f"Created and saved embeddings for {len(documents)} documents")
    
    def search(self, query, top_k=10):
        """Perform semantic search."""
        if self.embeddings is None:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            results.append({
                **doc['doc'],
                'semantic_score': float(similarities[idx])
            })
        
        return results
    
    def hybrid_search(self, query, keyword_results, top_k=10):
        """Combine keyword and semantic search results."""
        if self.embeddings is None:
            return keyword_results[:top_k]
        
        # Get semantic results (find different results, not just re-rank)
        semantic_results = self.search(query, top_k=top_k*3)  # Get more candidates
        
        # Create a map of URL to semantic score
        semantic_scores = {r['url']: r['semantic_score'] for r in semantic_results}
        
        # Get URLs from keyword results
        keyword_urls = {r['url'] for r in keyword_results}
        
        # Combine results: keyword results + semantic-only results
        combined_results = []
        
        # Add keyword results with semantic scores
        for result in keyword_results:
            semantic_score = semantic_scores.get(result['url'], 0.0)
            combined_results.append({
                **result,
                'semantic_score': semantic_score,
                'hybrid_score': semantic_score * 0.3
            })
        
        # Add semantic-only results (not in keyword results)
        for result in semantic_results:
            if result['url'] not in keyword_urls:
                combined_results.append({
                    **result,
                    'hybrid_score': result['semantic_score'] * 0.7  # Higher weight for semantic-only
                })
        
        # Sort by hybrid score
        combined_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return combined_results[:top_k] 