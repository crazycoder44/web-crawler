"""HTML parsing module for extracting book information."""
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin
from .models import Book
import logging
import re

logger = logging.getLogger("books_crawler")

BASE_URL = "https://books.toscrape.com/"

def extract_categories(html: str) -> List[Tuple[str, str]]:
    """Extract all book categories and their URLs."""
    soup = BeautifulSoup(html, 'lxml')
    categories = []
    
    # Categories are in the left sidebar
    category_links = soup.select('.side_categories ul.nav li ul li a')
    for link in category_links:
        url = urljoin(BASE_URL, link.get('href', ''))
        name = ' '.join(link.text.strip().split())
        categories.append((name, url))
    
    return categories

def extract_books_from_list(html: str) -> List[Tuple[str, str]]:
    """Extract book URLs from a category or list page."""
    soup = BeautifulSoup(html, 'lxml')
    books = []
    
    # Find all book articles
    for article in soup.select('article.product_pod'):
        title_link = article.h3.a
        if title_link:
            # Get the book URL
            href = title_link.get('href', '')
            
            # Clean up the path
            href = href.replace('../', '')  # Remove relative path components
            href = re.sub('^catalogue/', '', href)  # Remove catalogue/ if it's at the start 
            href = re.sub('^/catalogue/', '', href)  # Remove /catalogue/ if it's at the start
            
            # Now add /catalogue/ prefix and construct full URL
            href = '/catalogue/' + href
            url = urljoin(BASE_URL, href)
            title = title_link.get('title', '').strip()
            books.append((title, url))
    
    return books

def get_next_page_url(html: str, current_url: str) -> Optional[str]:
    """Extract the URL of the next page if it exists.
    Handles both category pages and main index pagination.
    
    Args:
        html: The HTML content of the current page
        current_url: The URL of the current page
    """
    soup = BeautifulSoup(html, 'lxml')
    next_link = soup.select_one('li.next a')
    if not next_link or not next_link.get('href'):
        return None
        
    next_href = next_link['href']
    
    # Get the directory of the current URL
    current_dir = current_url.rsplit('/', 1)[0] + '/'
    
    # Simply join the current directory with the next page href
    return urljoin(current_dir, next_href)

def parse_rating(rating_element: str) -> int:
    """Convert textual rating to numeric (1-5)."""
    rating_classes = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
    rating_text = rating_element.get('class', [''])[1] if rating_element else ''
    return rating_classes.get(rating_text, 0)

def extract_book_data(html: str, url: str) -> Dict[str, Any]:
    """Extract all book information from a book detail page."""
    import hashlib
    from datetime import datetime

    soup = BeautifulSoup(html, 'lxml')
    main_content = soup.select_one('article.product_page')
    if not main_content:
        raise ValueError(f"Invalid book page structure for {url}")
    
    # Extract product information table data
    table_rows = soup.select('table.table-striped tr')
    table_data = {
        row.th.text.strip().lower().replace(' ', '_'): row.td.text.strip()
        for row in table_rows
    } if table_rows else {}
    
    # Get description
    desc_elem = soup.select_one('#product_description ~ p')
    description = desc_elem.text.strip() if desc_elem else None
    
    # Get category from breadcrumb
    category_elem = soup.select('ul.breadcrumb li')[2] if len(soup.select('ul.breadcrumb li')) > 2 else None
    category = category_elem.text.strip() if category_elem else None
    
    # Extract prices from table cells
    price_incl_text = table_data.get('price_(incl._tax)', '')  # Note: key matches exact table header text
    price_excl_text = table_data.get('price_(excl._tax)', '')
    
    # Convert prices to float, handle £ sign
    try:
        price_incl = float(price_incl_text.replace('£', '').strip())
        if price_incl <= 0:
            raise ValueError("Price including tax must be greater than 0")
    except (ValueError, TypeError):
        raise ValueError(f"Invalid price including tax: {price_incl_text}")
    
    try:
        price_excl = float(price_excl_text.replace('£', '').strip())
        if price_excl <= 0:
            raise ValueError("Price excluding tax must be greater than 0") 
    except (ValueError, TypeError):
        raise ValueError(f"Invalid price excluding tax: {price_excl_text}")
    
    # Get availability number from string like "In stock (19 available)"
    availability_text = table_data.get('availability', '')
    availability_match = re.search(r'\((\d+) available\)', availability_text)
    availability = availability_match.group(1) if availability_match else '0'
    
    # Get rating
    rating_elem = soup.select_one('p.star-rating')
    rating = parse_rating(rating_elem)
    
    # Get image URL
    img_elem = soup.select_one('.item.active img')
    image_url = urljoin(BASE_URL, img_elem['src']) if img_elem else None
    
    # Generate fingerprint
    fingerprint = hashlib.md5(html.encode('utf-8')).hexdigest()
    
    return {
        'title': soup.select_one('.product_page h1').text.strip(),
        'source_url': url,
        'description': description,
        'category': category,
        'price_incl_tax': price_incl,
        'price_excl_tax': price_excl,
        'availability': f"{availability} available",
        'num_reviews': int(table_data.get('number_of_reviews', '0')),
        'image_url': image_url,
        'rating': rating,
        'fingerprint': fingerprint,
        'crawl_timestamp': datetime.utcnow(),
        'http_status': 200  # Since we got this far, we know the request succeeded
    }