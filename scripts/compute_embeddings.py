#!/usr/bin/env python3
"""
Script to compute embeddings for prototype dataset
Step 3: Compute Embeddings using Gemma 1B
"""

import sys
import json
import logging
from pathlib import Path
import time

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from classifier.embedding_classifier import EmbeddingClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_embeddings():
    """Compute and save embeddings for prototype dataset."""
    logger.info("🚀 Starting Embedding Computation for Prototype Dataset with Gemma 1B")
    
    start_time = time.time()
    
    # Initialize classifier
    logger.info("Initializing Gemma embedding classifier...")
    classifier = EmbeddingClassifier(
        model_name="google/gemma-3-1b-it",  # Gemma 3 1B Instruct (better for classification)
        threshold=0.7  # Similarity threshold
    )
    
    # Load prototype dataset
    logger.info("Loading prototype dataset...")
    personal_count, corporate_count = classifier.load_prototype_dataset()
    
    logger.info(f"📊 Dataset loaded: {personal_count} personal, {corporate_count} corporate")
    
    # Compute embeddings
    logger.info("Computing embeddings with Gemma...")
    classifier.compute_prototype_embeddings()
    
    # Save embeddings
    logger.info("Saving embeddings...")
    classifier.save_embeddings("models/prototype_embeddings.pkl")
    
    # Evaluate accuracy
    logger.info("Evaluating accuracy...")
    evaluation = classifier.evaluate_prototype_accuracy()
    
    # Print results
    elapsed_time = time.time() - start_time
    
    logger.info("✅ Embedding computation completed!")
    logger.info(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    logger.info(f"📈 Accuracy: {evaluation['accuracy']:.3f} ({evaluation['correct']}/{evaluation['total']})")
    
    # Test classification
    logger.info("\n🧪 Testing classification...")
    
    test_cases = [
        {
            "text": "I've been learning web development for the past year and wanted to share my journey with others who might be on a similar path.",
            "expected": "personal"
        },
        {
            "text": "Our company provides comprehensive web development services including custom solutions, e-commerce platforms, and mobile applications.",
            "expected": "corporate"
        },
        {
            "text": "This comprehensive guide covers everything you need to know about becoming a successful web developer in today's competitive market.",
            "expected": "corporate"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        prediction, confidence, details = classifier.classify_text(test_case["text"])
        
        prediction_label = "personal" if prediction == 1 else "corporate" if prediction == 0 else "uncertain"
        is_correct = prediction_label == test_case["expected"] if prediction is not None else False
        
        logger.info(f"Test {i}:")
        logger.info(f"  Text: {test_case['text'][:80]}...")
        logger.info(f"  Prediction: {prediction_label} (confidence: {confidence:.3f})")
        logger.info(f"  Expected: {test_case['expected']}")
        logger.info(f"  Correct: {'✅' if is_correct else '❌'}")
        logger.info("")
    
    return True

def main():
    """Main function."""
    try:
        success = compute_embeddings()
        if success:
            logger.info("🎉 Embedding computation completed successfully!")
            return 0
        else:
            logger.error("❌ Embedding computation failed!")
            return 1
    except Exception as e:
        logger.error(f"❌ Error during embedding computation: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 