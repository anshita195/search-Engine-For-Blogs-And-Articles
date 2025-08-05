#!/usr/bin/env python3
"""
Full-Scale Domain Harvest Sprint
Extract ALL unique domains from index, harvest blogrolls in parallel,
then process with sharpened filters and classification.
"""

import json
import sys
import time
import re
from pathlib import Path
import logging
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe counter
class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

# Modern blogroll patterns
MODERN_PATTERNS = [
    'favorites', 'reading', 'recommended', 'links', 'friends',
    'blogs i read', 'sites i like', 'inspiration', 'people i follow',
    'recommended reading', 'blog friends', 'my friends', 'other blogs',
    'blog links', 'sites worth visiting', 'blogs i love', 'favorites'
]

def get_all_unique_domains():
    """Extract ALL unique domains from search index."""
    print("🔍 Extracting ALL unique domains from search index...")
    search_index_file = Path("data/search_index.json")
    if not search_index_file.exists():
        print("❌ Search index not found!")
        return []
    
    with open(search_index_file, 'r') as f:
        data = json.load(f)
    
    domains = set()
    for blog in data:
        try:
            domain = urlparse(blog['url']).netloc
            if domain:
                domains.add(domain)
        except:
            continue
    
    domains = list(domains)
    print(f"📊 Found {len(domains)} unique domains")
    return domains

def harvest_domain_blogroll(domain, counter):
    """Harvest blogroll from a single domain (thread-safe)."""
    current = counter.increment()
    print(f"🌐 [{current}] Harvesting domain: {domain}")
    
    try:
        # Step 1: Check homepage
        url = f"https://{domain}"
        response = requests.get(url, timeout=10, headers={'User-Agent': 'PersonalBlogBot/1.0'})
        
        if response.status_code != 200:
            print(f"   ❌ [{current}] Failed to access {url}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        domain_links = []
        
        # Look for modern patterns in link text
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().lower().strip()
            href = link.get('href')
            
            # Check if link text matches modern patterns
            if any(pattern in link_text for pattern in MODERN_PATTERNS):
                if href.startswith('http'):
                    domain_links.append(href)
                elif href.startswith('/'):
                    domain_links.append(f"https://{domain}{href}")
        
        # Check "About" page
        about_links = soup.find_all('a', href=True, string=re.compile(r'about', re.IGNORECASE))
        for link in about_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    about_url = f"https://{domain}{href}"
                elif href.startswith('http'):
                    about_url = href
                else:
                    continue
                
                try:
                    about_response = requests.get(about_url, timeout=10, headers={'User-Agent': 'PersonalBlogBot/1.0'})
                    if about_response.status_code == 200:
                        about_soup = BeautifulSoup(about_response.text, 'html.parser')
                        about_page_links = about_soup.find_all('a', href=True)
                        
                        for about_link in about_page_links:
                            about_href = about_link.get('href')
                            about_text = about_link.get_text().lower().strip()
                            
                            # Look for blog-like links in about page
                            if (about_href.startswith('http') and 
                                any(word in about_text for word in ['blog', 'site', 'personal', 'writing', 'author'])):
                                domain_links.append(about_href)
                except:
                    continue
        
        # Check "Favorites" or "Reading" pages
        favorites_links = soup.find_all('a', href=True, string=re.compile(r'favorites?|reading', re.IGNORECASE))
        for link in favorites_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    fav_url = f"https://{domain}{href}"
                elif href.startswith('http'):
                    fav_url = href
                else:
                    continue
                
                try:
                    fav_response = requests.get(fav_url, timeout=10, headers={'User-Agent': 'PersonalBlogBot/1.0'})
                    if fav_response.status_code == 200:
                        fav_soup = BeautifulSoup(fav_response.text, 'html.parser')
                        fav_page_links = fav_soup.find_all('a', href=True)
                        
                        for fav_link in fav_page_links:
                            fav_href = fav_link.get('href')
                            if fav_href.startswith('http'):
                                domain_links.append(fav_href)
                except:
                    continue
        
        # Filter out social media and obvious non-blogs
        filtered_links = []
        for link in domain_links:
            try:
                link_domain = urlparse(link).netloc
                if (not any(skip in link_domain for skip in [
                    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 
                    'youtube.com', 'github.com', 'amazon.com', 'google.com', 
                    'wikipedia.org', 'reddit.com', 'stackoverflow.com'
                ]) and link_domain != domain):
                    filtered_links.append(link)
            except:
                continue
        
        # Remove duplicates
        unique_links = list(set(filtered_links))
        print(f"   📊 [{current}] Found {len(unique_links)} blogroll links")
        return unique_links
        
    except Exception as e:
        print(f"   ❌ [{current}] Error harvesting {domain}: {e}")
        return []

def full_scale_harvest():
    """Run full-scale domain harvesting with parallel processing."""
    print("🚀 FULL-SCALE DOMAIN HARVEST SPRINT")
    print("=" * 50)
    
    # Step 1: Get all unique domains
    all_domains = get_all_unique_domains()
    
    if not all_domains:
        print("❌ No domains found!")
        return
    
    print(f"🎯 Target: Harvest blogrolls from {len(all_domains)} domains")
    
    # Step 2: Parallel harvesting
    all_blogroll_links = []
    successful_domains = []
    counter = Counter()
    
    # Use ThreadPoolExecutor for parallel processing
    max_workers = 10  # Adjust based on your system
    print(f"⚡ Using {max_workers} parallel workers")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all domain harvesting tasks
        future_to_domain = {
            executor.submit(harvest_domain_blogroll, domain, counter): domain 
            for domain in all_domains
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                blogroll_links = future.result()
                if blogroll_links:
                    successful_domains.append(domain)
                    all_blogroll_links.extend(blogroll_links)
            except Exception as e:
                print(f"❌ Error processing {domain}: {e}")
    
    # Step 3: Dedupe results
    unique_blogroll_links = list(set(all_blogroll_links))
    
    print(f"\n🎯 FULL-SCALE HARVEST RESULTS:")
    print(f"Domains processed: {len(all_domains)}")
    print(f"Domains with blogrolls: {len(successful_domains)}")
    print(f"Total blogroll links found: {len(all_blogroll_links)}")
    print(f"Unique blogroll links: {len(unique_blogroll_links)}")
    
    # Save results
    results = {
        'harvested_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'domains_processed': len(all_domains),
        'domains_with_blogrolls': len(successful_domains),
        'total_blogroll_links': len(all_blogroll_links),
        'unique_blogroll_links': len(unique_blogroll_links),
        'successful_domains': successful_domains,
        'blogroll_links': unique_blogroll_links
    }
    
    output_file = Path("data/full_scale_harvest_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {output_file}")
    print(f"\n🚀 Next step: Process these {len(unique_blogroll_links)} URLs with classification")
    print(f"   Command: python scripts/process_full_harvest.py")
    
    return unique_blogroll_links

if __name__ == "__main__":
    full_scale_harvest() 