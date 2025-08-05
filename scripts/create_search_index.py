#!/usr/bin/env python3
"""
Create Search Index from Classified Content
Builds a searchable index from crawled and classified pages
"""

import json
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from classifier.hierarchical_classifier import HierarchicalClassifier
from extractor.content_extractor import ContentExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_search_index():
    """Create a search index from classified content."""
    
    # Load the full dataset of 41 blogs
    dataset_path = Path("data/prototype_dataset.json")
    if not dataset_path.exists():
        print("❌ Dataset file not found: data/prototype_dataset.json")
        return
    
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    # Extract URLs from the dataset
    sample_urls = [item['url'] for item in dataset]
    
    print(f"📊 Loaded {len(sample_urls)} URLs from dataset")
    
    print("🚀 Creating Search Index")
    print("=" * 50)
    
    # Initialize components
    classifier = HierarchicalClassifier()
    extractor = ContentExtractor()
    
    search_index = []
    
    for i, item in enumerate(dataset, 1):
        url = item['url']
        print(f"\n📥 Processing {i}/{len(dataset)}: {url}")
        
        try:
            # Use content from dataset instead of live extraction
            title = item.get('title', '')
            content = item.get('content', '')
            meta_description = item.get('meta_description', '')
            author = item.get('author', '')
            
            if not content:
                print("⚠️  No content in dataset, skipping")
                continue
            
            # Classify using dataset content
            result = classifier.classify_page(
                url=url,
                title=title,
                meta_description=meta_description,
                content=content,
                html_content=f"<html><body>{content}</body></html>"
            )
            
            # Only include personal blogs in the search index
            if result['is_personal']:
                print(f"✅ Personal blog detected (confidence: {result['confidence']:.3f})")
                
                # Create search document
                search_doc = {
                    'url': url,
                    'title': title,
                    'description': meta_description,
                    'content': content,
                    'author': author,
                    'domain': result['domain'],
                    'is_personal': True,
                    'confidence': result['confidence'],
                    'stage_used': result['stage_used'],
                    'extracted_at': '',
                    'content_length': len(content)
                }
                
                search_index.append(search_doc)
            else:
                print(f"❌ Corporate site detected (confidence: {result['confidence']:.3f})")
                
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            continue
    
    # Save search index (convert numpy types to native Python types)
    def convert_numpy_types(obj):
        if hasattr(obj, 'item'):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(v) for v in obj]
        return obj
    
    search_index_serializable = convert_numpy_types(search_index)
    
    output_file = Path("data/search_index.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(search_index_serializable, f, indent=2)
    
    print(f"\n📊 Search Index Summary:")
    print(f"Total documents: {len(search_index)}")
    print(f"Personal blogs: {len(search_index)}")
    print(f"Corporate sites: {len(sample_urls) - len(search_index)}")
    print(f"Index saved to: {output_file}")
    
    # Show sample documents
    print(f"\n📋 Sample Documents:")
    for i, doc in enumerate(search_index[:3]):
        print(f"\n{i+1}. {doc['title']}")
        print(f"   URL: {doc['url']}")
        print(f"   Domain: {doc['domain']}")
        print(f"   Confidence: {doc['confidence']:.3f}")
        print(f"   Content length: {doc['content_length']} chars")
    
    return search_index

if __name__ == "__main__":
    create_search_index() 