import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Any, Optional
import re
from playwright.sync_api import sync_playwright
import time
from app.utils.text_cleaning import clean_html, clean_text, process_text_for_ai
from app.config import settings

logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def get_base_url(url: str) -> str:
    """
    Get base URL from full URL.
    
    Args:
        url: Full URL
        
    Returns:
        Base URL
    """
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

def is_same_domain(url: str, base_url: str) -> bool:
    """
    Check if URL is from the same domain as base URL.
    
    Args:
        url: URL to check
        base_url: Base URL
        
    Returns:
        True if same domain, False otherwise
    """
    return urlparse(url).netloc == urlparse(base_url).netloc

def extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract links from BeautifulSoup object.
    
    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List of absolute URLs
    """
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # Skip anchor links and JavaScript
        if href.startswith('#') or href.startswith('javascript:'):
            continue
        
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        
        # Skip external links and non-HTTP/HTTPS links
        if not is_same_domain(absolute_url, base_url) or not absolute_url.startswith(('http://', 'https://')):
            continue
        
        # Skip common non-content URLs
        skip_patterns = [
            r'\.pdf$', r'\.jpg$', r'\.jpeg$', r'\.png$', r'\.gif$', 
            r'\.css$', r'\.js$', r'\.xml$', r'\.rss$', 
            r'/tag/', r'/category/', r'/author/', r'/feed/', 
            r'/wp-content/', r'/wp-includes/', r'/wp-admin/'
        ]
        
        if any(re.search(pattern, absolute_url, re.IGNORECASE) for pattern in skip_patterns):
            continue
        
        links.append(absolute_url)
    
    return links

def is_important_page(url: str) -> bool:
    """
    Check if URL likely points to an important page.
    
    Args:
        url: URL to check
        
    Returns:
        True if important page, False otherwise
    """
    important_patterns = [
        r'/about', r'/bio', r'/profile', r'/team', 
        r'/services', r'/speak(ing|er)', r'/events', 
        r'/topics', r'/expertise', r'/keynote',
        r'/portfolio', r'/work', r'/projects', 
        r'/contact', r'/blog'
    ]
    
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in important_patterns)

def fetch_with_playwright(url: str) -> Optional[str]:
    """
    Fetch page content using Playwright (for JavaScript-heavy sites).
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content if successful, None otherwise
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to load
            page.wait_for_timeout(2000)
            
            # Get HTML content
            content = page.content()
            
            # Close browser
            browser.close()
            
            return content
    except Exception as e:
        logger.error(f"Error fetching URL with Playwright: {url}, error: {str(e)}")
        return None

def fetch_url(url: str) -> Optional[str]:
    """
    Fetch URL content, trying multiple methods if necessary.
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content if successful, None otherwise
    """
    # First try with requests (faster)
    content = fetch_with_requests(url)
    
    # If failed or empty content, try with Playwright
    if not content or len(content.strip()) < 100:
        content = fetch_with_playwright(url)
    
    return content

def crawl_website(start_url: str, max_pages: int = 10) -> Dict[str, Any]:
    """
    Crawl website starting from URL and extract content.
    
    Args:
        start_url: Starting URL
        max_pages: Maximum number of pages to crawl
        
    Returns:
        Dictionary with crawled data
    """
    if not is_valid_url(start_url):
        return {'error': 'Invalid URL'}
    
    base_url = get_base_url(start_url)
    visited = set()
    to_visit = [start_url]
    important_pages = []
    extracted_content = {}
    
    while to_visit and len(visited) < max_pages:
        # Get next URL to visit
        current_url = to_visit.pop(0)
        
        # Skip if already visited
        if current_url in visited:
            continue
        
        # Mark as visited
        visited.add(current_url)
        
        # Check if it's an important page
        is_important = is_important_page(current_url)
        if is_important:
            important_pages.append(current_url)
        
        # Fetch content
        html_content = fetch_url(current_url)
        if not html_content:
            continue
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text
        text_content = clean_html(html_content)
        
        # Store content
        page_data = {
            'url': current_url,
            'title': soup.title.string if soup.title else '',
            'text': text_content,
            'is_important': is_important
        }
        
        extracted_content[current_url] = page_data
        
        # Extract links for further crawling
        if len(visited) < max_pages:
            links = extract_links(soup, current_url)
            
            # Prioritize important pages
            for link in links:
                if link not in visited and link not in to_visit:
                    if is_important_page(link):
                        to_visit.insert(0, link)  # Add important pages to the front
                    else:
                        to_visit.append(link)  # Add other pages to the back
    
    # Process the collected content
    combined_text = ""
    
    # First add content from important pages
    for url in important_pages:
        if url in extracted_content:
            page = extracted_content[url]
            combined_text += f"=== {page['title']} ===\n\n"
            combined_text += page['text'] + "\n\n"
    
    # Then add content from other pages
    for url, page in extracted_content.items():
        if url not in important_pages:
            combined_text += f"=== {page['title']} ===\n\n"
            combined_text += page['text'] + "\n\n"
    
    # Process text for AI
    processed_chunks = process_text_for_ai(combined_text)
    
    result = {
        'base_url': base_url,
        'pages_crawled': len(visited),
        'important_pages': important_pages,
        'processed_text': processed_chunks
    }
    
    return result

def fetch_with_requests(url: str) -> Optional[str]:
    """
    Fetch page content using requests.
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content if successful, None otherwise
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Check if content is HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            return None
        
        return response.text
    except Exception as e:
        logger.error(f"Error fetching URL with requests: {url}, error: {str(e)}")
        return None