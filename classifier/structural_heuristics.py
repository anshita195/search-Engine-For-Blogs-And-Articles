#!/usr/bin/env python3
"""
Structural Heuristics for Personal vs Corporate Classification
Phase F: Inspect headers/footers for "About me" links, social media icons, etc.
"""

import re
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class StructuralHeuristics:
    def __init__(self):
        """Initialize structural heuristics analyzer."""
        
        # Personal indicators (positive scores)
        self.personal_patterns = {
            # About me sections
            r'about\s*me': 0.3,
            r'about\s*the\s*author': 0.3,
            r'who\s*i\s*am': 0.2,
            r'my\s*story': 0.2,
            
            # Personal pronouns
            r'\bi\s*am\b': 0.1,
            r'\bmy\s*experience\b': 0.2,
            r'\bi\s*want\b': 0.1,
            r'\bi\s*think\b': 0.1,
            
            # Social media links
            r'twitter\.com': 0.2,
            r'github\.com': 0.2,
            r'linkedin\.com': 0.1,
            r'instagram\.com': 0.1,
            
            # Personal domains
            r'\.dev\b': 0.3,
            r'\.me\b': 0.2,
            r'\.blog\b': 0.2,
            
            # RSS feeds
            r'/feed': 0.2,
            r'/rss': 0.2,
            r'\.xml': 0.1,
            
            # Personal blog indicators
            r'powered\s*by\s*wordpress': 0.1,
            r'built\s*with\s*hugo': 0.1,
            r'jekyll': 0.1,
        }
        
        # Corporate indicators (negative scores)
        self.corporate_patterns = {
            # Business terms
            r'contact\s*us': -0.2,
            r'privacy\s*policy': -0.2,
            r'terms\s*of\s*service': -0.2,
            r'cookie\s*policy': -0.2,
            
            # Marketing terms
            r'subscribe\s*now': -0.2,
            r'get\s*started': -0.2,
            r'free\s*trial': -0.3,
            r'limited\s*time': -0.3,
            
            # Corporate domains
            r'\.com\b': -0.1,
            r'\.org\b': -0.1,
            r'\.net\b': -0.1,
            
            # Ad networks
            r'googleadservices': -0.3,
            r'doubleclick': -0.3,
            r'facebook\.com/tr': -0.3,
            
            # SEO indicators
            r'seo\s*optimized': -0.2,
            r'search\s*engine': -0.1,
            r'keyword': -0.1,
        }
        
        # Compile patterns for efficiency
        self.personal_regex = {re.compile(pattern, re.IGNORECASE): score 
                              for pattern, score in self.personal_patterns.items()}
        self.corporate_regex = {re.compile(pattern, re.IGNORECASE): score 
                               for pattern, score in self.corporate_patterns.items()}
    
    def analyze_html_structure(self, html_content: str, url: str) -> Dict:
        """
        Analyze HTML structure for personal vs corporate indicators.
        
        Args:
            html_content: Raw HTML content
            url: Page URL
            
        Returns:
            Dictionary with structural analysis results
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Analyze different sections
            header_score = self._analyze_section(soup.find('header'), 'header')
            footer_score = self._analyze_section(soup.find('footer'), 'footer')
            nav_score = self._analyze_section(soup.find('nav'), 'navigation')
            main_score = self._analyze_section(soup.find('main'), 'main content')
            
            # Analyze full text
            text_score = self._analyze_text_patterns(text_content)
            
            # Analyze links
            link_score = self._analyze_links(soup)
            
            # Analyze meta tags
            meta_score = self._analyze_meta_tags(soup)
            
            # Calculate total score
            total_score = (header_score + footer_score + nav_score + 
                          main_score + text_score + link_score + meta_score)
            
            # Determine confidence based on score magnitude
            confidence = min(abs(total_score) / 2.0, 1.0)
            
            # Determine prediction
            if total_score > 0.5:
                prediction = 1  # Personal
            elif total_score < -0.5:
                prediction = 0  # Corporate
            else:
                prediction = None  # Uncertain
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'total_score': total_score,
                'section_scores': {
                    'header': header_score,
                    'footer': footer_score,
                    'navigation': nav_score,
                    'main_content': main_score,
                    'text_patterns': text_score,
                    'links': link_score,
                    'meta_tags': meta_score
                },
                'indicators_found': self._get_indicators_found(text_content, soup)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing HTML structure: {e}")
            return {
                'prediction': None,
                'confidence': 0.0,
                'total_score': 0.0,
                'section_scores': {},
                'indicators_found': [],
                'error': str(e)
            }
    
    def _analyze_section(self, section, section_name: str) -> float:
        """Analyze a specific HTML section."""
        if not section:
            return 0.0
        
        text = section.get_text(separator=' ', strip=True)
        return self._analyze_text_patterns(text)
    
    def _analyze_text_patterns(self, text: str) -> float:
        """Analyze text for personal/corporate patterns."""
        score = 0.0
        
        # Check personal patterns
        for pattern, pattern_score in self.personal_regex.items():
            if pattern.search(text):
                score += pattern_score
        
        # Check corporate patterns
        for pattern, pattern_score in self.corporate_regex.items():
            if pattern.search(text):
                score += pattern_score
        
        return score
    
    def _analyze_links(self, soup: BeautifulSoup) -> float:
        """Analyze links for personal/corporate indicators."""
        score = 0.0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            link_text = link.get_text().lower()
            
            # Personal indicators
            if any(pattern.search(href) for pattern in [re.compile(r'twitter\.com'), re.compile(r'github\.com')]):
                score += 0.2
            if 'about' in link_text or 'me' in link_text:
                score += 0.1
            
            # Corporate indicators
            if any(pattern.search(href) for pattern in [re.compile(r'contact'), re.compile(r'privacy')]):
                score -= 0.1
            if 'subscribe' in link_text or 'newsletter' in link_text:
                score -= 0.2
        
        return score
    
    def _analyze_meta_tags(self, soup: BeautifulSoup) -> float:
        """Analyze meta tags for personal/corporate indicators."""
        score = 0.0
        
        for meta in soup.find_all('meta'):
            content = meta.get('content', '').lower()
            name = meta.get('name', '').lower()
            
            # Personal indicators
            if 'author' in name and content:
                score += 0.2
            if 'personal' in content or 'blog' in content:
                score += 0.1
            
            # Corporate indicators
            if 'business' in content or 'corporate' in content:
                score -= 0.2
            if 'seo' in name or 'keywords' in name:
                score -= 0.1
        
        return score
    
    def _get_indicators_found(self, text: str, soup: BeautifulSoup) -> List[Dict]:
        """Get list of indicators found in the content."""
        indicators = []
        
        # Check personal patterns
        for pattern, score in self.personal_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                indicators.append({
                    'type': 'personal',
                    'pattern': pattern,
                    'score': score,
                    'description': f'Found personal indicator: {pattern}'
                })
        
        # Check corporate patterns
        for pattern, score in self.corporate_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                indicators.append({
                    'type': 'corporate',
                    'pattern': pattern,
                    'score': score,
                    'description': f'Found corporate indicator: {pattern}'
                })
        
        return indicators

def main():
    """Test the structural heuristics."""
    heuristics = StructuralHeuristics()
    
    # Test with sample HTML
    test_html = """
    <html>
    <head>
        <title>My Personal Blog</title>
        <meta name="author" content="John Doe">
    </head>
    <body>
        <header>
            <nav>
                <a href="/about-me">About Me</a>
                <a href="https://twitter.com/johndoe">Twitter</a>
            </nav>
        </header>
        <main>
            <h1>My Experience with Web Development</h1>
            <p>I have been learning web development for the past year...</p>
        </main>
        <footer>
            <p>Powered by WordPress</p>
        </footer>
    </body>
    </html>
    """
    
    result = heuristics.analyze_html_structure(test_html, "https://example.com")
    print("Structural Analysis Result:")
    print(f"Prediction: {result['prediction']} (1=Personal, 0=Corporate, None=Uncertain)")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Total Score: {result['total_score']:.3f}")
    print(f"Section Scores: {result['section_scores']}")
    print(f"Indicators Found: {len(result['indicators_found'])}")

if __name__ == "__main__":
    main() 