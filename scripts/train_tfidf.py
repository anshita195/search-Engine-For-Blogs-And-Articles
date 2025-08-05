#!/usr/bin/env python3
"""
Script to train the TF-IDF classifier (Phase D)
Uses crawled data and rule-based filtering to create training data.
"""

import sys
import logging
from pathlib import Path
import json
import sqlite3
from typing import List, Dict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from classifier.tfidf_classifier import TFIDFClassifier
from classifier.domain_filter import DomainFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_crawled_data(db_path: str = "data/crawled/crawl.db") -> List[Dict]:
    """Load crawled data from SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT url, title, content, html_content, crawled_at 
            FROM crawled_pages 
            WHERE content IS NOT NULL AND content != ''
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'url': row[0],
                'title': row[1],
                'content': row[2],
                'html': row[3],
                'crawled_at': row[4]
            })
        
        logger.info(f"Loaded {len(data)} crawled pages")
        return data
        
    except Exception as e:
        logger.error(f"Error loading crawled data: {e}")
        return []

def create_training_data(crawled_data: List[Dict], min_confidence: float = 0.7) -> List[Dict]:
    """Create training data using rule-based filtering."""
    logger.info("Creating training data from crawled pages...")
    
    domain_filter = DomainFilter()
    training_data = []
    
    for item in crawled_data:
        url = item.get('url', '')
        content = item.get('content', '')
        html = item.get('html', '')
        
        if not content or not url:
            continue
        
        # Use rule-based filter to get initial labels
        filter_result = domain_filter.filter_page(url, content, html)
        
        # Only include high-confidence samples for training
        if filter_result.confidence >= min_confidence:
            training_data.append({
                'text': content,
                'is_personal': filter_result.is_personal,
                'url': url,
                'confidence': filter_result.confidence,
                'stage': filter_result.stage
            })
    
    logger.info(f"Created {len(training_data)} training samples (confidence >= {min_confidence})")
    
    # Log distribution
    personal_count = sum(1 for item in training_data if item['is_personal'])
    logger.info(f"Personal blogs: {personal_count}, Corporate/SEO: {len(training_data) - personal_count}")
    
    return training_data

def save_training_data(training_data: List[Dict], output_path: str = "data/training_data.json"):
    """Save training data to JSON file."""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved training data to {output_file}")
        
    except Exception as e:
        logger.error(f"Error saving training data: {e}")

def main():
    """Main training script."""
    logger.info("🚀 Starting TF-IDF classifier training (Phase D)")
    
    # Load crawled data
    crawled_data = load_crawled_data()
    if not crawled_data:
        logger.error("No crawled data found. Run the crawler first.")
        return False
    
    # Create training data
    training_data = create_training_data(crawled_data, min_confidence=0.7)
    if len(training_data) < 10:
        logger.error("Insufficient training data. Need at least 10 samples.")
        return False
    
    # Save training data for inspection
    save_training_data(training_data)
    
    # Train TF-IDF classifier
    classifier = TFIDFClassifier()
    
    if classifier.train(training_data):
        logger.info("✅ TF-IDF classifier trained successfully!")
        
        # Test on a few samples
        logger.info("🧪 Testing classifier...")
        test_samples = training_data[:5]
        
        for sample in test_samples:
            text = sample['text'][:200] + "..." if len(sample['text']) > 200 else sample['text']
            is_personal, confidence = classifier.predict(sample['text'])
            actual = sample['is_personal']
            
            status = "✅" if is_personal == actual else "❌"
            logger.info(f"{status} Predicted: {is_personal} (conf: {confidence:.3f}), Actual: {actual}")
            logger.info(f"   Text: {text}")
        
        return True
    else:
        logger.error("❌ Failed to train TF-IDF classifier")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 