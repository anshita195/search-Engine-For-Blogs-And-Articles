#!/usr/bin/env python3
"""
Hierarchical Classifier for Personal vs Corporate Content
Combines Domain Filter (Stage 1) + TF-IDF (Stage 2) + Embeddings (Stage 3) + Structural Heuristics (Stage 4)
"""

import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from classifier.domain_filter import DomainFilter
from classifier.tfidf_classifier import TFIDFClassifier
from classifier.embedding_classifier import EmbeddingClassifier
from classifier.structural_heuristics import StructuralHeuristics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HierarchicalClassifier:
    def __init__(self, 
                 domain_threshold: float = 5.0,
                 tfidf_threshold: float = 0.6,
                 embedding_threshold: float = 0.7,
                 structural_threshold: float = 0.5):
        """
        Initialize the hierarchical classifier.
        
        Args:
            domain_threshold: Confidence threshold for domain filter
            tfidf_threshold: Confidence threshold for TF-IDF classifier
            embedding_threshold: Confidence threshold for embedding classifier
            structural_threshold: Confidence threshold for structural heuristics
        """
        self.domain_threshold = domain_threshold
        self.tfidf_threshold = tfidf_threshold
        self.embedding_threshold = embedding_threshold
        self.structural_threshold = structural_threshold
        
        # Initialize all classifiers
        logger.info("Initializing hierarchical classifier components...")
        
        # Stage 1: Domain Filter
        self.domain_filter = DomainFilter()
        logger.info("✅ Domain filter initialized")
        
        # Stage 2: TF-IDF Classifier
        try:
            self.tfidf_classifier = TFIDFClassifier()
            self.tfidf_classifier.load_model("models/tfidf_classifier.pkl")
            logger.info("✅ TF-IDF classifier loaded")
        except Exception as e:
            logger.warning(f"⚠️ TF-IDF classifier not available: {e}")
            self.tfidf_classifier = None
        
        # Stage 3: Embedding Classifier
        try:
            self.embedding_classifier = EmbeddingClassifier(threshold=embedding_threshold)
            self.embedding_classifier.load_embeddings("models/prototype_embeddings.pkl")
            logger.info("✅ Embedding classifier loaded")
        except Exception as e:
            logger.warning(f"⚠️ Embedding classifier not available: {e}")
            self.embedding_classifier = None
        
        # Stage 4: Structural Heuristics
        self.structural_heuristics = StructuralHeuristics()
        logger.info("✅ Structural heuristics initialized")
        
        logger.info("🎯 Hierarchical classifier ready!")
    
    def classify_page(self, url: str, title: str = "", meta_description: str = "", 
                     content: str = "", html_content: str = "") -> Dict:
        """
        Classify a web page using the hierarchical pipeline.
        
        Args:
            url: Page URL
            title: Page title
            meta_description: Meta description
            content: Clean text content
            html_content: Raw HTML content (for structural analysis)
        
        Returns:
            Classification result with all stage details
        """
        logger.info(f"🔍 Classifying: {url}")
        
        # Stage 1: Domain Filter
        logger.info("  📊 Stage 1: Domain Filter")
        domain_result = self.domain_filter.filter_page(url, content, html_content)
        
        # Convert FilterResult to dict format
        domain_dict = {
            'prediction': domain_result.is_personal,
            'confidence': domain_result.confidence,
            'score': domain_result.score,
            'reasons': domain_result.reasons,
            'stage': domain_result.stage,
            'url': url,
            'domain': self.domain_filter._canonicalize_domain(url)
        }
        
        if domain_result.confidence >= self.domain_threshold:
            logger.info(f"    ✅ High confidence domain classification: {domain_result.is_personal}")
            return self._create_final_result(
                prediction=domain_result.is_personal,
                confidence=domain_result.confidence,
                stage="domain_filter",
                stage_details={
                    "domain_filter": domain_dict,
                    "tfidf": None,
                    "embedding": None,
                    "structural": None
                }
            )
        
        # Stage 2: TF-IDF Classifier
        if self.tfidf_classifier and content:
            logger.info("  📊 Stage 2: TF-IDF Classifier")
            tfidf_result = self.tfidf_classifier.classify_text(content)
            
            if tfidf_result['confidence'] >= self.tfidf_threshold:
                logger.info(f"    ✅ High confidence TF-IDF classification: {tfidf_result['prediction']}")
                return self._create_final_result(
                    prediction=tfidf_result['prediction'],
                    confidence=tfidf_result['confidence'],
                    stage="tfidf",
                    stage_details={
                        "domain_filter": domain_dict,
                        "tfidf": tfidf_result,
                        "embedding": None,
                        "structural": None
                    }
                )
        else:
            tfidf_result = None
        
        # Stage 3: Embedding Classifier
        if self.embedding_classifier and content:
            logger.info("  📊 Stage 3: Embedding Classifier")
            embedding_result = self.embedding_classifier.classify_page(
                url=url, title=title, meta_description=meta_description, content=content
            )
            
            if embedding_result['confidence'] >= self.embedding_threshold:
                logger.info(f"    ✅ High confidence embedding classification: {embedding_result['is_personal']}")
                return self._create_final_result(
                    prediction=embedding_result['is_personal'],
                    confidence=embedding_result['confidence'],
                    stage="embedding",
                    stage_details={
                        "domain_filter": domain_dict,
                        "tfidf": tfidf_result,
                        "embedding": embedding_result,
                        "structural": None
                    }
                )
        else:
            embedding_result = None
        
        # Stage 4: Structural Heuristics
        logger.info("  📊 Stage 4: Structural Heuristics")
        if html_content:
            structural_result = self.structural_heuristics.analyze_html_structure(html_content, url)
        else:
            structural_result = {
                'prediction': None,
                'confidence': 0.0,
                'total_score': 0.0,
                'section_scores': {},
                'indicators_found': []
            }
        
        if structural_result['confidence'] >= self.structural_threshold:
            logger.info(f"    ✅ High confidence structural classification: {structural_result['prediction']}")
            return self._create_final_result(
                prediction=structural_result['prediction'],
                confidence=structural_result['confidence'],
                stage="structural",
                stage_details={
                    "domain_filter": domain_dict,
                    "tfidf": tfidf_result,
                    "embedding": embedding_result,
                    "structural": structural_result
                }
            )
        
        # If all stages are uncertain, combine their predictions
        logger.info("  📊 Combining all stage predictions")
        final_prediction, final_confidence = self._combine_predictions(
            domain_dict, tfidf_result, embedding_result, structural_result
        )
        
        return self._create_final_result(
            prediction=final_prediction,
            confidence=final_confidence,
            stage="combined",
            stage_details={
                "domain_filter": domain_dict,
                "tfidf": tfidf_result,
                "embedding": embedding_result,
                "structural": structural_result
            }
        )
    
    def _combine_predictions(self, domain_result, tfidf_result, embedding_result, structural_result):
        """Combine predictions from all stages using weighted voting."""
        predictions = []
        confidences = []
        weights = []
        
        # Domain filter (weight: 0.3)
        if domain_result and domain_result['prediction'] is not None:
            predictions.append(domain_result['prediction'])
            confidences.append(domain_result['confidence'])
            weights.append(0.3)
        
        # TF-IDF (weight: 0.25)
        if tfidf_result and tfidf_result['prediction'] is not None:
            predictions.append(tfidf_result['prediction'])
            confidences.append(tfidf_result['confidence'])
            weights.append(0.25)
        
        # Embedding (weight: 0.3)
        if embedding_result and embedding_result['is_personal'] is not None:
            predictions.append(embedding_result['is_personal'])
            confidences.append(embedding_result['confidence'])
            weights.append(0.3)
        
        # Structural (weight: 0.15)
        if structural_result and structural_result['prediction'] is not None:
            predictions.append(structural_result['prediction'])
            confidences.append(structural_result['confidence'])
            weights.append(0.15)
        
        if not predictions:
            return None, 0.0
        
        # Calculate weighted average
        weighted_sum = sum(p * w for p, w in zip(predictions, weights))
        total_weight = sum(weights)
        
        if total_weight == 0:
            return None, 0.0
        
        final_prediction = 1 if weighted_sum / total_weight > 0.5 else 0
        final_confidence = sum(c * w for c, w in zip(confidences, weights)) / total_weight
        
        return final_prediction, final_confidence
    
    def _create_final_result(self, prediction, confidence, stage, stage_details):
        """Create the final classification result."""
        return {
            "url": stage_details.get("domain_filter", {}).get("url", ""),
            "is_personal": prediction,
            "confidence": confidence,
            "stage_used": stage,
            "stage_details": stage_details,
            "domain": stage_details.get("domain_filter", {}).get("domain", ""),
            "title": stage_details.get("embedding", {}).get("title", "") if stage_details.get("embedding") else "",
            "author": stage_details.get("embedding", {}).get("author", "") if stage_details.get("embedding") else ""
        }

def main():
    """Test the hierarchical classifier."""
    classifier = HierarchicalClassifier()
    
    # Test with a sample URL
    test_url = "https://jvns.ca/blog/2020/10/28/a-few-things-i-ve-learned-about-email-marketing/"
    
    # Mock content for testing
    test_content = "I've been learning about email marketing for the past few years..."
    test_html = f"""
    <html>
    <head><title>Email Marketing Lessons</title></head>
    <body>
        <header><nav><a href="/about">About Me</a></nav></header>
        <main>{test_content}</main>
        <footer>Powered by WordPress</footer>
    </body>
    </html>
    """
    
    result = classifier.classify_page(
        url=test_url,
        title="Email Marketing Lessons",
        meta_description="Personal lessons learned",
        content=test_content,
        html_content=test_html
    )
    
    print("Hierarchical Classification Result:")
    print(f"URL: {result['url']}")
    print(f"Prediction: {result['is_personal']} (1=Personal, 0=Corporate)")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Stage Used: {result['stage_used']}")
    print(f"Domain: {result['domain']}")

if __name__ == "__main__":
    main() 