#!/usr/bin/env python3
"""
Domain Filter Module - Enhanced taxonomy implementation
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    is_personal: bool
    confidence: float
    score: float
    reasons: List[str]
    stage: str

class DomainFilter:
    def __init__(self, taxonomy_path: str = "enhanced_taxonomy.json"):
        self.taxonomy_path = Path(taxonomy_path)
        self.taxonomy = self._load_taxonomy()
        self._compile_patterns()
        
    def _load_taxonomy(self) -> Dict:
        with open(self.taxonomy_path, 'r') as f:
            return json.load(f)
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance"""
        self.compiled_patterns = {'positive': {}, 'negative': {}}
        
        for category, config in self.taxonomy['content_indicators']['positive_regex'].items():
            self.compiled_patterns['positive'][category] = {
                'patterns': [re.compile(p, re.IGNORECASE) for p in config['patterns']],
                'weight': config['weight']
            }
        
        for category, config in self.taxonomy['content_indicators']['negative_regex'].items():
            self.compiled_patterns['negative'][category] = {
                'patterns': [re.compile(p, re.IGNORECASE) for p in config['patterns']],
                'weight': config['weight']
            }
    
    def _canonicalize_domain(self, url: str) -> str:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain[4:] if domain.startswith('www.') else domain
    
    def _check_domain_patterns(self, domain: str) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        
        # High confidence positive
        for pattern in self.taxonomy['domain_patterns']['high_confidence_positive']['patterns']:
            if pattern in domain:
                weight = self.taxonomy['domain_patterns']['high_confidence_positive']['weight']
                score += weight
                reasons.append(f"High confidence positive: {pattern}")
                break
        
        # High confidence negative
        for pattern in self.taxonomy['domain_patterns']['high_confidence_negative']['patterns']:
            if pattern in domain:
                weight = self.taxonomy['domain_patterns']['high_confidence_negative']['weight']
                score += weight
                reasons.append(f"High confidence negative: {pattern}")
                break
        
        # Medium confidence (only if no high confidence match)
        if score == 0:
            for pattern in self.taxonomy['domain_patterns']['medium_confidence_positive']['patterns']:
                if pattern in domain:
                    weight = self.taxonomy['domain_patterns']['medium_confidence_positive']['weight']
                    score += weight
                    reasons.append(f"Medium confidence positive: {pattern}")
                    break
        
        return score, reasons
    
    def _check_content_patterns(self, text: str) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        
        # Positive patterns
        for category, config in self.compiled_patterns['positive'].items():
            for pattern in config['patterns']:
                matches = pattern.findall(text)
                if matches:
                    score += config['weight'] * len(matches)
                    reasons.append(f"Positive ({category}): {len(matches)} matches")
        
        # Negative patterns
        for category, config in self.compiled_patterns['negative'].items():
            for pattern in config['patterns']:
                matches = pattern.findall(text)
                if matches:
                    score += config['weight'] * len(matches)
                    reasons.append(f"Negative ({category}): {len(matches)} matches")
        
        return score, reasons
    
    def _check_structural_indicators(self, html_content: str, url: str) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []
        
        # RSS feeds
        if re.search(r'<link[^>]*type=["\']application/rss\+xml["\'][^>]*>', html_content, re.IGNORECASE):
            score += 2
            reasons.append("RSS feed detected")
        
        # Author metadata
        if re.search(r'<meta[^>]*property=["\']og:article:author["\'][^>]*>', html_content, re.IGNORECASE):
            score += 1
            reasons.append("Author metadata detected")
        
        # Dated URL patterns
        parsed_url = urlparse(url)
        if re.search(r'^/20[0-2]\d/', parsed_url.path):
            score += 1
            reasons.append("Dated URL pattern")
        
        return score, reasons
    
    def filter_page(self, url: str, text_content: str = "", html_content: str = "") -> FilterResult:
        domain = self._canonicalize_domain(url)
        total_score = 0.0
        all_reasons = []
        
        # Stage 1: Domain filtering
        domain_score, domain_reasons = self._check_domain_patterns(domain)
        total_score += domain_score
        all_reasons.extend(domain_reasons)
        
        # High confidence domain decisions
        if domain_score >= 5:
            return FilterResult(True, 0.9, total_score, all_reasons, 'domain')
        elif domain_score <= -5:
            return FilterResult(False, 0.9, total_score, all_reasons, 'domain')
        
        # Stage 2: Content filtering
        if text_content:
            content_score, content_reasons = self._check_content_patterns(text_content)
            total_score += content_score
            all_reasons.extend(content_reasons)
        
        # Stage 3: Structural analysis
        if html_content:
            structural_score, structural_reasons = self._check_structural_indicators(html_content, url)
            total_score += structural_score
            all_reasons.extend(structural_reasons)
        
        # Determine final classification
        confidence = min(abs(total_score) / 10.0, 0.9)
        
        if total_score >= 3:
            return FilterResult(True, confidence, total_score, all_reasons, 'content')
        elif total_score <= -3:
            return FilterResult(False, confidence, total_score, all_reasons, 'content')
        else:
            return FilterResult(False, 0.3, total_score, all_reasons, 'uncertain')

def main():
    filter = DomainFilter()
    
    test_cases = [
        ("https://jvns.ca/blog/", "This is my personal blog about programming", "<html>...</html>"),
        ("https://forbes.com/tech", "Our company provides solutions", "<html>...</html>"),
    ]
    
    for url, text, html in test_cases:
        result = filter.filter_page(url, text, html)
        print(f"\nURL: {url}")
        print(f"Result: {'PERSONAL' if result.is_personal else 'CORPORATE'}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Score: {result.score:.2f}")

if __name__ == "__main__":
    main() 