import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from datetime import datetime
from config import CRAWL_DELAY, REQUEST_TIMEOUT, USER_AGENT


class WebCrawler:
    """Crawls web pages and extracts content"""
    
    def __init__(self, max_pages=50, delay=CRAWL_DELAY):
        self.max_pages = max_pages
        self.delay = delay
        self.visited = set()
        
    def is_valid_url(self, url):
        """Check if URL is valid and should be crawled"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and bool(parsed.scheme)
        except:
            return False
    
    def get_page_content(self, url):
        """Fetch and parse a web page"""
        try:
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_text(self, html, url):
        """Extract text content and metadata from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get title
        title = soup.title.string if soup.title else ""
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Extract metadata
        metadata = self.extract_metadata(soup, url)
        
        return title, text, metadata
    
    def extract_metadata(self, soup, url):
        """Extract metadata from the page"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'content_type': 'text/html',
            'crawl_date': datetime.now().isoformat(),
            'content_length': 0
        }
        
        # Try to extract publication date
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}\s+\w+\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, soup.get_text())
            if dates:
                metadata['publication_date'] = dates[0]
                break
        
        # Extract content type from meta tags
        meta_ctype = soup.find('meta', attrs={'http-equiv': 'content-type'})
        if meta_ctype:
            metadata['content_type'] = meta_ctype.get('content', 'text/html').split(';')[0]
        
        # Content length
        metadata['content_length'] = len(soup.get_text())
        
        return metadata
    
    def extract_links(self, html, base_url):
        """Extract all links from a page"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            url = urljoin(base_url, link['href'])
            if self.is_valid_url(url):
                links.append(url)
        
        return links
    
    def crawl(self, seed_urls):
        """Crawl starting from seed URLs"""
        to_visit = list(seed_urls)
        crawled_data = []
        
        print(f"Starting crawl with {len(seed_urls)} seed URLs...")
        
        while to_visit and len(self.visited) < self.max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited:
                continue
            
            print(f"Crawling [{len(self.visited) + 1}/{self.max_pages}]: {url}")
            
            html = self.get_page_content(url)
            if not html:
                continue
            
            self.visited.add(url)
            
            # Extract content
            title, text, metadata = self.extract_text(html, url)
            
            # Extract links for further crawling
            links = self.extract_links(html, url)
            to_visit.extend(links)
            
            # Store crawled data with metadata
            crawled_data.append({
                'url': url,
                'title': title,
                'content': text,
                'metadata': metadata
            })
            
            # Be polite - don't hammer servers
            time.sleep(self.delay)
        
        print(f"Crawling complete! Indexed {len(crawled_data)} pages.")
        return crawled_data
