#!/usr/bin/env python3
"""
Simple Blog Crawler
Basic crawler with robots.txt compliance and rate limiting.
"""

import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleCrawler:
    def __init__(self, output_dir: str = "data/crawled", rate_limit: float = 1.0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.domain_last_request: Dict[str, float] = {}
        
        # Database
        self.db_path = self.output_dir / "crawl.db"
        self._init_database()
        
        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PersonalBlogBot/1.0'
        })
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawled_pages (
                url TEXT PRIMARY KEY,
                domain TEXT,
                status_code INTEGER,
                title TEXT,
                html_content TEXT,
                links TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _get_robots_parser(self, domain: str) -> RobotFileParser:
        if domain not in self.robots_cache:
            try:
                robots_url = f"https://{domain}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            except:
                self.robots_cache[domain] = None
        return self.robots_cache[domain]
    
    def _can_crawl(self, url: str) -> bool:
        if url in self.visited_urls:
            return False
        
        domain = urlparse(url).netloc
        rp = self._get_robots_parser(domain)
        if rp and not rp.can_fetch('PersonalBlogBot/1.0', url):
            return False
        
        return True
    
    def _respect_rate_limit(self, domain: str):
        last_request = self.domain_last_request.get(domain, 0)
        time_since_last = time.time() - last_request
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.domain_last_request[domain] = time.time()
    
    def crawl_page(self, url: str) -> Dict:
        if not self._can_crawl(url):
            return None
        
        domain = urlparse(url).netloc
        self._respect_rate_limit(domain)
        
        try:
            logger.info(f"Crawling {url}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                absolute_url = urljoin(url, href)
                if urlparse(absolute_url).netloc == domain:
                    links.append(absolute_url.split('#')[0])
            
            result = {
                'url': url,
                'domain': domain,
                'status_code': response.status_code,
                'title': title,
                'html_content': response.text,
                'links': list(set(links)),
                'timestamp': datetime.now().isoformat()
            }
            
            self.visited_urls.add(url)
            self._store_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    def _store_result(self, result: Dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO crawled_pages 
            (url, domain, status_code, title, html_content, links, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['url'],
            result['domain'],
            result['status_code'],
            result['title'],
            result['html_content'],
            json.dumps(result['links']),
            result['timestamp']
        ))
        conn.commit()
        conn.close()
    
    def crawl_seeds(self, seed_urls: List[str], max_pages: int = 50) -> List[Dict]:
        results = []
        to_crawl = seed_urls.copy()
        
        while to_crawl and len(results) < max_pages:
            url = to_crawl.pop(0)
            result = self.crawl_page(url)
            
            if result:
                results.append(result)
                # Add new links to crawl queue
                to_crawl.extend(result['links'][:5])  # Limit new links per page
        
        return results

def main():
    # Load seeds
    with open("data/seeds.json", 'r') as f:
        seeds = json.load(f)
    
    crawler = SimpleCrawler(rate_limit=2.0)
    results = crawler.crawl_seeds(seeds[:3], max_pages=10)
    
    print(f"Crawled {len(results)} pages")
    for result in results:
        print(f"- {result['url']}: {result['title']}")

if __name__ == "__main__":
    main() 