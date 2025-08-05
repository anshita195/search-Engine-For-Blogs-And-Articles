#!/usr/bin/env python3
"""
Embedding-based Classifier for Personal vs Corporate Content
Uses Gemma 1B to compute embeddings and classify content
"""

import json
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import logging
from urllib.parse import urlparse
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingClassifier:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", threshold: float = 0.7):
        """
        Initialize the embedding classifier.
        
        Args:
            model_name: Sentence transformer model to use (default: all-MiniLM-L6-v2 for fast embeddings)
            threshold: Similarity threshold for classification
        """
        self.model_name = model_name
        self.threshold = threshold
        
        # Load sentence transformer model
        logger.info(f"Loading sentence transformer model: {model_name}")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        
        logger.info(f"Initialized EmbeddingClassifier with model: {model_name}")
        
        # Store prototype embeddings
        self.personal_embeddings = np.array([])
        self.corporate_embeddings = np.array([])
        self.personal_texts = []
        self.corporate_texts = []
        
        logger.info(f"Initialized EmbeddingClassifier with Gemma model: {model_name}")
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length to avoid token limits (Gemma has 2048 token limit)
        if len(text) > 1500:  # Conservative limit
            text = text[:1500]
        
        return text
    
    def create_text_representation(self, item: Dict) -> str:
        """
        Create a text representation for embedding.
        Combines title, domain, meta_description, and content.
        """
        parts = []
        
        # Add title
        if item.get('title'):
            parts.append(f"Title: {item['title']}")
        
        # Add domain
        if item.get('domain'):
            parts.append(f"Domain: {item['domain']}")
        
        # Add meta description
        if item.get('meta_description'):
            parts.append(f"Description: {item['meta_description']}")
        
        # Add content (first 800 chars for efficiency with Gemma)
        if item.get('content'):
            content = item['content'][:800] if len(item['content']) > 800 else item['content']
            parts.append(f"Content: {content}")
        
        return " | ".join(parts)
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Get embeddings for a list of texts using sentence transformers.
        """
        # Use sentence transformer to get embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def load_prototype_dataset(self, dataset_path: str = "data/prototype_dataset.json"):
        """Load and prepare prototype dataset."""
        logger.info(f"Loading prototype dataset from {dataset_path}")
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        personal_texts = []
        corporate_texts = []
        
        for item in dataset:
            text_repr = self.create_text_representation(item)
            
            if item['is_personal'] == 1:
                personal_texts.append(text_repr)
            else:
                corporate_texts.append(text_repr)
        
        self.personal_texts = personal_texts
        self.corporate_texts = corporate_texts
        
        logger.info(f"Loaded {len(personal_texts)} personal and {len(corporate_texts)} corporate prototypes")
        
        return len(personal_texts), len(corporate_texts)
    
    def compute_prototype_embeddings(self):
        """Compute embeddings for all prototype texts using Gemma."""
        logger.info("Computing prototype embeddings with Gemma...")
        
        if not self.personal_texts and not self.corporate_texts:
            raise ValueError("No prototype texts loaded. Call load_prototype_dataset() first.")
        
        # Compute embeddings for personal texts
        if self.personal_texts:
            logger.info(f"Computing embeddings for {len(self.personal_texts)} personal texts...")
            self.personal_embeddings = self.get_embeddings(self.personal_texts)
            logger.info(f"Computed embeddings for {len(self.personal_texts)} personal texts")
        
        # Compute embeddings for corporate texts
        if self.corporate_texts:
            logger.info(f"Computing embeddings for {len(self.corporate_texts)} corporate texts...")
            self.corporate_embeddings = self.get_embeddings(self.corporate_texts)
            logger.info(f"Computed embeddings for {len(self.corporate_texts)} corporate texts")
    
    def classify_text(self, text: str) -> Tuple[int, float, Dict]:
        """
        Classify a text as personal (1) or corporate (0).
        
        Returns:
            (prediction, confidence, details)
        """
        if not self.personal_embeddings.size or not self.corporate_embeddings.size:
            raise ValueError("No prototype embeddings available. Call compute_prototype_embeddings() first.")
        
        # Clean and prepare text
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return None, 0.0, {"error": "Empty text"}
        
        # Compute embedding for input text
        text_embedding = self.get_embeddings([cleaned_text])
        
        # Compute similarities with personal prototypes
        personal_similarities = cosine_similarity(text_embedding, self.personal_embeddings)[0]
        max_personal_sim = np.max(personal_similarities)
        
        # Compute similarities with corporate prototypes
        corporate_similarities = cosine_similarity(text_embedding, self.corporate_embeddings)[0]
        max_corporate_sim = np.max(corporate_similarities)
        
        # Determine prediction and confidence
        if max_personal_sim > max_corporate_sim:
            prediction = 1  # Personal
            confidence = max_personal_sim
            best_match_type = "personal"
            best_match_sim = max_personal_sim
        else:
            prediction = 0  # Corporate
            confidence = max_corporate_sim
            best_match_type = "corporate"
            best_match_sim = max_corporate_sim
        
        # Apply threshold
        if confidence < self.threshold:
            prediction = None  # Uncertain
        
        details = {
            "personal_max_similarity": float(max_personal_sim),
            "corporate_max_similarity": float(max_corporate_sim),
            "best_match_type": best_match_type,
            "best_match_similarity": float(best_match_sim),
            "threshold": self.threshold,
            "confidence": float(confidence)
        }
        
        return prediction, confidence, details
    
    def classify_page(self, url: str, title: str = "", meta_description: str = "", content: str = "") -> Dict:
        """
        Classify a web page based on its content.
        
        Args:
            url: Page URL
            title: Page title
            meta_description: Meta description
            content: Page content
            
        Returns:
            Classification result dictionary
        """
        # Create text representation
        item = {
            "url": url,
            "title": title,
            "domain": self.extract_domain(url),
            "meta_description": meta_description,
            "content": content
        }
        
        text_repr = self.create_text_representation(item)
        
        # Classify
        prediction, confidence, details = self.classify_text(text_repr)
        
        result = {
            "url": url,
            "is_personal": prediction,
            "confidence": confidence,
            "domain": item["domain"],
            "details": details
        }
        
        return result
    
    def save_embeddings(self, output_path: str = "models/prototype_embeddings.pkl"):
        """Save computed embeddings to disk."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        embeddings_data = {
            "personal_embeddings": self.personal_embeddings,
            "corporate_embeddings": self.corporate_embeddings,
            "personal_texts": self.personal_texts,
            "corporate_texts": self.corporate_texts,
            "model_name": self.model_name,
            "threshold": self.threshold
        }
        
        with open(output_file, 'wb') as f:
            pickle.dump(embeddings_data, f)
        
        logger.info(f"Saved embeddings to {output_file}")
    
    def load_embeddings(self, embeddings_path: str = "models/prototype_embeddings.pkl"):
        """Load pre-computed embeddings from disk."""
        embeddings_file = Path(embeddings_path)
        
        if not embeddings_file.exists():
            raise FileNotFoundError(f"Embeddings file not found: {embeddings_file}")
        
        with open(embeddings_file, 'rb') as f:
            embeddings_data = pickle.load(f)
        
        self.personal_embeddings = embeddings_data["personal_embeddings"]
        self.corporate_embeddings = embeddings_data["corporate_embeddings"]
        self.personal_texts = embeddings_data["personal_texts"]
        self.corporate_texts = embeddings_data["corporate_texts"]
        self.model_name = embeddings_data["model_name"]
        self.threshold = embeddings_data["threshold"]
        
        logger.info(f"Loaded embeddings from {embeddings_file}")
        logger.info(f"Personal: {len(self.personal_texts)}, Corporate: {len(self.corporate_texts)}")
    
    def evaluate_prototype_accuracy(self) -> Dict:
        """Evaluate accuracy on prototype dataset."""
        logger.info("Evaluating prototype accuracy...")
        
        correct = 0
        total = 0
        results = []
        
        # Test personal texts
        for i, text in enumerate(self.personal_texts):
            prediction, confidence, details = self.classify_text(text)
            is_correct = prediction == 1
            correct += int(is_correct)
            total += 1
            
            results.append({
                "text_type": "personal",
                "prediction": prediction,
                "confidence": confidence,
                "correct": is_correct
            })
        
        # Test corporate texts
        for i, text in enumerate(self.corporate_texts):
            prediction, confidence, details = self.classify_text(text)
            is_correct = prediction == 0
            correct += int(is_correct)
            total += 1
            
            results.append({
                "text_type": "corporate",
                "prediction": prediction,
                "confidence": confidence,
                "correct": is_correct
            })
        
        accuracy = correct / total if total > 0 else 0
        
        evaluation = {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "results": results
        }
        
        logger.info(f"Prototype accuracy: {accuracy:.3f} ({correct}/{total})")
        
        return evaluation

def main():
    """Main function to demonstrate the embedding classifier."""
    # Initialize classifier
    classifier = EmbeddingClassifier(threshold=0.7)
    
    # Load prototype dataset
    personal_count, corporate_count = classifier.load_prototype_dataset()
    
    # Compute embeddings
    classifier.compute_prototype_embeddings()
    
    # Save embeddings
    classifier.save_embeddings()
    
    # Evaluate accuracy
    evaluation = classifier.evaluate_prototype_accuracy()
    
    # Test classification on a sample
    test_text = "I've been learning web development for the past year and wanted to share my journey..."
    prediction, confidence, details = classifier.classify_text(test_text)
    
    print(f"\nTest classification:")
    print(f"Text: {test_text[:100]}...")
    print(f"Prediction: {prediction} (Personal: 1, Corporate: 0, Uncertain: None)")
    print(f"Confidence: {confidence:.3f}")
    print(f"Details: {details}")

if __name__ == "__main__":
    main() 