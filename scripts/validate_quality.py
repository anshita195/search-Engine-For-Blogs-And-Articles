#!/usr/bin/env python3
"""
Quality Validation Script
Sample and validate the quality of classified personal blogs
"""

import json
import random
import sys
from pathlib import Path
import pandas as pd

def validate_search_index_quality():
    """Validate the quality of the search index through sampling."""
    print("🔍 VALIDATING SEARCH INDEX QUALITY")
    print("=" * 50)
    
    # Load search index
    search_index_file = Path("data/search_index.json")
    if not search_index_file.exists():
        print("❌ search_index.json not found!")
        return
    
    with open(search_index_file, 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    print(f"📊 Total blogs in index: {len(search_index)}")
    
    # Sample 50 blogs for validation (or 100 if you have time)
    sample_size = min(50, len(search_index))
    sample_blogs = random.sample(search_index, sample_size)
    
    print(f"🎯 Sampling {sample_size} blogs for validation")
    
    # Create validation results
    validation_results = []
    
    for i, blog in enumerate(sample_blogs, 1):
        print(f"\n--- Blog {i}/{sample_size} ---")
        print(f"Title: {blog.get('title', 'N/A')}")
        print(f"URL: {blog.get('url', 'N/A')}")
        print(f"Domain: {blog.get('domain', 'N/A')}")
        print(f"Confidence: {blog.get('confidence', 'N/A'):.3f}")
        print(f"Content preview: {blog.get('content', '')[:200]}...")
        
        # Ask for validation
        while True:
            response = input("\nIs this a PERSONAL blog? (y/n/s for skip): ").lower().strip()
            if response in ['y', 'n', 's']:
                break
            print("Please enter y, n, or s")
        
        if response == 's':
            continue
            
        validation_results.append({
            'url': blog.get('url'),
            'title': blog.get('title'),
            'domain': blog.get('domain'),
            'confidence': blog.get('confidence'),
            'is_personal': response == 'y',
            'classifier_correct': (response == 'y') == blog.get('is_personal', False)
        })
    
    # Calculate metrics
    if validation_results:
        total_validated = len(validation_results)
        correct_predictions = sum(1 for r in validation_results if r['classifier_correct'])
        actual_personal = sum(1 for r in validation_results if r['is_personal'])
        predicted_personal = sum(1 for r in validation_results if r['classifier_correct'] and r['is_personal'])
        
        precision = predicted_personal / actual_personal if actual_personal > 0 else 0
        accuracy = correct_predictions / total_validated
        
        print(f"\n📈 VALIDATION RESULTS")
        print(f"=" * 30)
        print(f"Total validated: {total_validated}")
        print(f"Actually personal: {actual_personal}")
        print(f"Classifier correct: {correct_predictions}")
        print(f"Precision: {precision:.1%}")
        print(f"Accuracy: {accuracy:.1%}")
        
        # Save detailed results
        results_file = Path("data/validation_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_validated': total_validated,
                    'actual_personal': actual_personal,
                    'correct_predictions': correct_predictions,
                    'precision': precision,
                    'accuracy': accuracy
                },
                'detailed_results': validation_results
            }, f, indent=2)
        
        print(f"✅ Detailed results saved to: {results_file}")
        
        # Show examples of misclassifications
        misclassified = [r for r in validation_results if not r['classifier_correct']]
        if misclassified:
            print(f"\n⚠️  MISCLASSIFIED EXAMPLES ({len(misclassified)}):")
            for r in misclassified[:5]:  # Show first 5
                status = "Personal but classified as corporate" if r['is_personal'] else "Corporate but classified as personal"
                print(f"- {r['title']} ({r['domain']}) - {status}")
    
    return validation_results

def generate_quality_report():
    """Generate a comprehensive quality report."""
    print("\n📋 GENERATING QUALITY REPORT")
    print("=" * 40)
    
    # Load search index
    with open("data/search_index.json", 'r', encoding='utf-8') as f:
        search_index = json.load(f)
    
    # Basic statistics
    total_blogs = len(search_index)
    avg_confidence = sum(b.get('confidence', 0) for b in search_index) / total_blogs
    
    # Domain distribution
    domains = {}
    for blog in search_index:
        domain = blog.get('domain', 'unknown')
        domains[domain] = domains.get(domain, 0) + 1
    
    top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Content length distribution
    content_lengths = [len(b.get('content', '')) for b in search_index]
    avg_content_length = sum(content_lengths) / len(content_lengths)
    
    print(f"📊 BASIC STATISTICS:")
    print(f"Total blogs: {total_blogs}")
    print(f"Average confidence: {avg_confidence:.3f}")
    print(f"Average content length: {avg_content_length:.0f} characters")
    
    print(f"\n🏆 TOP DOMAINS:")
    for domain, count in top_domains:
        print(f"  {domain}: {count} blogs")
    
    # Save report
    report = {
        'total_blogs': total_blogs,
        'avg_confidence': avg_confidence,
        'avg_content_length': avg_content_length,
        'domain_distribution': dict(top_domains),
        'content_length_stats': {
            'min': min(content_lengths),
            'max': max(content_lengths),
            'avg': avg_content_length
        }
    }
    
    with open("data/quality_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Quality report saved to: data/quality_report.json")

if __name__ == "__main__":
    import sys
    
    # Check for dry-run flag
    if "--dry-run" in sys.argv:
        print("🧪 DRY RUN: Quality validation would run here")
        print("✅ Quality validation script is ready")
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        generate_quality_report()
    else:
        validate_search_index_quality() 