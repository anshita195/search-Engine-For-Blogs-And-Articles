#!/usr/bin/env python3
"""
IMPROVED Search Engine Scaling with Bulletproof Duplicate Prevention
- Lower confidence threshold (0.75)
- Better URL pre-filtering
- RSS/Atom feed discovery
- NO DUPLICATES EVER
"""

import json
import sys
import time
import re
from pathlib import Path
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import feedparser

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from classifier.hierarchical_classifier import HierarchicalClassifier
from crawler.simple_crawler import SimpleCrawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IMPROVED Configuration
CONFIDENCE_THRESHOLD = 0.85  # RAISED BACK TO HIGHER CONFIDENCE
REVIEW_THRESHOLD = 0.75      # RAISED REVIEW THRESHOLD
MAX_FEED_ITEMS = 50

# URL pre-filtering patterns
BLOG_URL_PATTERNS = [
    r'/blog/', r'/post/', r'/article/', r'/writing/', r'/journal/',
    r'/diary/', r'/story/', r'/memoir/', r'/202[0-9]/', r'/201[0-9]/'
]

CORPORATE_URL_PATTERNS = [
    r'/press/', r'/news/', r'/careers/', r'/product/', r'/services/',
    r'/about-us/', r'/company/', r'/team/', r'/contact/', r'/privacy/',
    r'/terms/', r'/advertise/', r'/sponsor/', r'/pricing/', r'/enterprise/',
    r'/documentation/', r'/api/', r'/developers/', r'/support/', r'/help/',
    r'/tutorial/', r'/guide/', r'/docs/', r'/reference/', r'/manual/'
]

def get_existing_urls():
    """Get all existing URLs from search index to prevent duplicates."""
    search_index_file = Path("data/search_index.json")
    if not search_index_file.exists():
        return set()
    
    with open(search_index_file, 'r') as f:
        data = json.load(f)
    
    # Extract all URLs and normalize them
    existing_urls = set()
    for blog in data:
        url = blog['url']
        # Normalize URL (remove query params, fragments, etc.)
        normalized_url = normalize_url(url)
        existing_urls.add(normalized_url)
    
    print(f"🔍 Loaded {len(existing_urls)} existing URLs for duplicate prevention")
    return existing_urls

def normalize_url(url):
    """Normalize URL to prevent duplicates with different formats."""
    try:
        parsed = urlparse(url)
        # Remove query parameters and fragments
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        # Remove trailing slash
        if normalized.endswith('/') and len(normalized) > 1:
            normalized = normalized.rstrip('/')
        return normalized.lower()
    except:
        return url.lower()

def is_url_already_indexed(url, existing_urls):
    """Check if URL is already in the index (with normalization)."""
    normalized_url = normalize_url(url)
    return normalized_url in existing_urls

def pre_filter_url(url):
    """Pre-filter URLs before content extraction to improve efficiency."""
    url_lower = url.lower()
    
    # Check for corporate patterns first (faster rejection)
    for pattern in CORPORATE_URL_PATTERNS:
        if re.search(pattern, url_lower):
            return False, f"Corporate pattern: {pattern}"
    
    # Check for blog patterns
    for pattern in BLOG_URL_PATTERNS:
        if re.search(pattern, url_lower):
            return True, f"Blog pattern: {pattern}"
    
    return True, "No clear pattern"

def discover_rss_feeds(domain):
    """Discover RSS/Atom feeds for a domain."""
    feeds = []
    
    try:
        # Try homepage first
        url = f"https://{domain}"
        response = requests.get(url, timeout=10, headers={'User-Agent': 'PersonalBlogBot/1.0'})
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for RSS feed links
            rss_links = soup.find_all('link', type=['application/rss+xml', 'application/atom+xml'])
            for link in rss_links:
                href = link.get('href')
                if href:
                    if href.startswith('/'):
                        href = f"https://{domain}{href}"
                    feeds.append(href)
            
            # Also try common feed URLs
            common_feeds = [
                f"https://{domain}/feed",
                f"https://{domain}/rss",
                f"https://{domain}/atom",
                f"https://{domain}/blog/feed",
                f"https://{domain}/posts/feed",
                f"https://{domain}/rss.xml",
                f"https://{domain}/atom.xml"
            ]
            
            for feed_url in common_feeds:
                feeds.append(feed_url)
    
    except Exception as e:
        print(f"   ❌ Error discovering feeds for {domain}: {e}")
    
    return list(set(feeds))  # Remove duplicates

def parse_rss_feed(feed_url):
    """Parse RSS/Atom feed and extract blog post URLs."""
    try:
        feed = feedparser.parse(feed_url)
        urls = []
        
        for entry in feed.entries[:MAX_FEED_ITEMS]:  # Limit to avoid overwhelming
            if hasattr(entry, 'link'):
                urls.append(entry.link)
        
        return urls
    except Exception as e:
        print(f"   ❌ Error parsing feed {feed_url}: {e}")
        return []

def get_existing_personal_blogs():
    """Get existing personal blogs to crawl for new content."""
    search_index_file = Path("data/search_index.json")
    if not search_index_file.exists():
        return []
    
    with open(search_index_file, 'r') as f:
        data = json.load(f)
    
    # Extract unique domains
    domains = set()
    for blog in data:
        try:
            domain = urlparse(blog['url']).netloc
            if domain:
                domains.add(domain)
        except:
            continue
    
    domains = list(domains)
    print(f"📊 Found {len(domains)} existing domains to crawl")
    return domains

def process_urls_with_improved_filtering(new_urls, existing_urls):
    """Process URLs with improved filtering and duplicate prevention."""
    print(f"\n🔍 PROCESSING {len(new_urls)} URLs WITH IMPROVED FILTERING")
    print("=" * 60)
    
    classifier = HierarchicalClassifier()
    crawler = SimpleCrawler()
    
    auto_added = 0
    review_candidates = []
    rejected = 0
    pre_filtered = 0
    duplicates_skipped = 0
    
    for i, url in enumerate(new_urls, 1):
        print(f"\n🌐 Processing URL {i}/{len(new_urls)}: {url}")
        
        # STEP 1: Check if already indexed (DUPLICATE PREVENTION)
        if is_url_already_indexed(url, existing_urls):
            print(f"   ⏭️ SKIPPED: Already indexed")
            duplicates_skipped += 1
            continue
        
        # STEP 2: Pre-filter URL
        should_process, reason = pre_filter_url(url)
        if not should_process:
            print(f"   🚫 PRE-FILTERED: {reason}")
            pre_filtered += 1
            continue
        
        # STEP 3: Extract content
        try:
            result = crawler.crawl_page(url)
            if not result or not result.get('html_content'):
                print(f"   ❌ No content extracted")
                rejected += 1
                continue
            
            content = result['html_content']
            title = result.get('title', '')
            
        except Exception as e:
            print(f"   ❌ Error extracting content: {e}")
            rejected += 1
            continue
        
        # STEP 4: Classify content
        try:
            result = classifier.classify_page(url, title, "", "", content)
            confidence = result['confidence']
            classification = 'personal-blog' if result['is_personal'] else 'corporate'
            print(f"   📊 Classification: {classification} (confidence: {confidence:.3f})")
            
        except Exception as e:
            print(f"   ❌ Error classifying: {e}")
            rejected += 1
            continue
        
        # STEP 5: Process based on confidence
        if classification == 'personal-blog':
            if confidence >= CONFIDENCE_THRESHOLD:
                # Auto-add high confidence personal blogs
                try:
                    add_to_search_index(url, title, content, confidence)
                    auto_added += 1
                    print(f"   ✅ AUTO-ADDED: High confidence personal blog")
                    
                    # Update existing URLs set to prevent future duplicates
                    existing_urls.add(normalize_url(url))
                    
                except Exception as e:
                    print(f"   ❌ Error adding to index: {e}")
                    rejected += 1
            
            elif confidence >= REVIEW_THRESHOLD:
                # Add to review queue
                review_candidates.append({
                    'url': url,
                    'title': title,
                    'confidence': confidence,
                    'classification': classification
                })
                print(f"   🔍 REVIEW CANDIDATE: Medium confidence")
            
            else:
                print(f"   ❌ REJECTED: Low confidence ({confidence:.3f})")
                rejected += 1
        
        else:
            print(f"   ❌ REJECTED: Not a personal blog")
            rejected += 1
        
        # Be polite
        time.sleep(0.5)
    
    # Save review candidates
    if review_candidates:
        review_file = Path("data/review_candidates.json")
        with open(review_file, 'w') as f:
            json.dump(review_candidates, f, indent=2)
        print(f"\n📁 Review candidates saved to: {review_file}")
    
    print(f"\n📊 IMPROVED PROCESSING SUMMARY:")
    print(f"Pre-filtered out: {pre_filtered}")
    print(f"Duplicates skipped: {duplicates_skipped}")
    print(f"Auto-added blogs: {auto_added}")
    print(f"Review candidates: {len(review_candidates)}")
    print(f"Rejected blogs: {rejected}")
    
    # Calculate success rate
    total_processed = len(new_urls) - duplicates_skipped - pre_filtered
    if total_processed > 0:
        success_rate = (auto_added / total_processed) * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    return auto_added, len(review_candidates)

def add_to_search_index(url, title, content, confidence):
    """Add a blog to the search index."""
    search_index_file = Path("data/search_index.json")
    
    # Load existing data
    if search_index_file.exists():
        with open(search_index_file, 'r') as f:
            data = json.load(f)
    else:
        data = []
    
    # Add new blog
    blog_entry = {
        'url': url,
        'title': title,
        'content': content,
        'confidence': confidence,
        'added_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    data.append(blog_entry)
    
    # Save updated index
    with open(search_index_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"   📝 Added to search index: {len(data)} total blogs")

def enhanced_crawl_domain(domain):
    """Enhanced crawling with RSS feed discovery."""
    print(f"🔍 Enhanced crawling domain: {domain}")
    
    all_urls = []
    
    # Discover RSS feeds
    print(f"   🔍 Discovering RSS feeds for {domain}")
    feeds = discover_rss_feeds(domain)
    
    for feed_url in feeds:
        print(f"      📡 Found RSS feed: {feed_url}")
    
    # Parse RSS feeds
    for feed_url in feeds:
        print(f"   📥 Parsing RSS feed: {feed_url}")
        try:
            urls = parse_rss_feed(feed_url)
            print(f"      📊 Found {len(urls)} blog posts in RSS feed")
            all_urls.extend(urls)
        except Exception as e:
            print(f"      ❌ Error parsing feed: {e}")
    
    # Remove duplicates
    unique_urls = list(set(all_urls))
    print(f"   📊 Total unique URLs found: {len(unique_urls)}")
    
    return unique_urls

def improved_scaling():
    """Run improved scaling with better filtering and duplicate prevention."""
    print("🚀 IMPROVED Search Engine Scaling")
    print("=" * 50)
    print(f"📊 Confidence threshold: {CONFIDENCE_THRESHOLD} (raised from 0.75)")
    print(f"📊 Review threshold: {REVIEW_THRESHOLD} (raised from 0.60)")
    print("=" * 50)
    
    # Load existing URLs for duplicate prevention
    existing_urls = get_existing_urls()
    
    # Get existing domains to crawl
    domains = get_existing_personal_blogs()
    
    if not domains:
        print("❌ No existing domains found!")
        return
    
    all_new_urls = []
    
    # Enhanced crawling of existing domains
    for i, domain in enumerate(domains, 1):
        print(f"\n🌐 Processing domain {i}/{len(domains)}: {domain}")
        
        try:
            urls = enhanced_crawl_domain(domain)
            all_new_urls.extend(urls)
            
            # Be polite
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error processing domain {domain}: {e}")
            continue
    
    # Remove duplicates across all domains
    unique_new_urls = list(set(all_new_urls))
    print(f"\n📊 Total unique new URLs discovered: {len(unique_new_urls)}")
    
    if not unique_new_urls:
        print("❌ No new URLs discovered!")
        return
    
    # Process URLs with improved filtering
    auto_added, review_count = process_urls_with_improved_filtering(unique_new_urls, existing_urls)
    
    print(f"\n🎯 IMPROVED RESULTS:")
    print(f"✅ Auto-added: {auto_added} high-confidence blogs")
    print(f"🔍 Review candidates: {review_count} medium-confidence blogs")
    print(f"📊 Total processed: {len(unique_new_urls)} URLs")
    
    if review_count > 0:
        print(f"\n📋 Review these candidates manually:")
        review_file = Path("data/review_candidates.json")
        if review_file.exists():
            with open(review_file, 'r') as f:
                candidates = json.load(f)
            
            for i, candidate in enumerate(candidates[:5], 1):  # Show first 5
                print(f"{i}. {candidate['title']} - {urlparse(candidate['url']).netloc} (confidence: {candidate['confidence']:.3f})")
                print(f"   URL: {candidate['url']}")

if __name__ == "__main__":
    improved_scaling() 