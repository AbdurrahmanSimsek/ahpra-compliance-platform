import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from app import db
from app.models import Website, Page

class WebsiteCrawler:
    def __init__(self, website_id):
        self.website = Website.query.get(website_id)
        if not self.website:
            raise ValueError(f"Website with ID {website_id} not found")
        
        self.base_url = self.website.url
        self.visited_urls = set()
        self.queue = [self.base_url]
        self.pages = []
    
    def is_valid_url(self, url):
        """Check if URL belongs to the same domain and is a valid page"""
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        
        # Check if same domain
        if parsed_base.netloc != parsed_url.netloc:
            return False
        
        # Ignore URLs with fragments only
        if not parsed_url.path or parsed_url.path == '/':
            if parsed_base.path == parsed_url.path and parsed_url.fragment:
                return False
        
        # Ignore common file extensions that aren't HTML
        ignored_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', 
                             '.xls', '.xlsx', '.zip', '.rar', '.css', '.js')
        if any(url.lower().endswith(ext) for ext in ignored_extensions):
            return False
        
        return True
    
    def extract_links(self, url, html_content):
        """Extract all links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(url, href)
            
            if self.is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                links.append(absolute_url)
        
        return links
    
    def extract_content(self, html_content):
        """Extract title and text content from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else ""
        
        # Extract text content, ignoring scripts and styles
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator="\n", strip=True)
        
        return title, text
    
    def crawl(self, max_pages=None):
        """Crawl the website and store pages"""
        try:
            self.website.crawl_status = 'in_progress'
            db.session.commit()
            
            while self.queue and (max_pages is None or len(self.pages) < max_pages):
                url = self.queue.pop(0)
                
                if url in self.visited_urls:
                    continue
                
                self.visited_urls.add(url)
                
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code != 200:
                        continue
                    
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'text/html' not in content_type:
                        continue
                    
                    html_content = response.text
                    title, text_content = self.extract_content(html_content)
                    
                    # Create Page object
                    page = Page(
                        website=self.website,
                        url=url,
                        title=title,
                        html_content=html_content,
                        text_content=text_content
                    )
                    
                    db.session.add(page)
                    self.pages.append(page)
                    
                    # Extract and add new links to the queue
                    new_links = self.extract_links(url, html_content)
                    self.queue.extend(new_links)
                    
                except Exception as e:
                    print(f"Error crawling {url}: {str(e)}")
                    continue
            
            self.website.crawl_status = 'completed'
            self.website.last_crawled = db.func.now()
            db.session.commit()
            
            return self.pages
            
        except Exception as e:
            self.website.crawl_status = 'failed'
            db.session.commit()
            raise e
