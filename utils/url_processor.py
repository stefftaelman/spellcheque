"""
URL processor module for fetching and extracting text from web pages.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def process_url_input(url, timeout=10):
    """
    Fetch content from URL and extract the main text.
    
    Args:
        url (str): The URL to fetch content from
        timeout (int): Request timeout in seconds
        
    Returns:
        tuple: (text_content, None) where text_content is the extracted text
              The second value is None since there's no associated file ID
              
    Raises:
        ValueError: If the URL is invalid or content cannot be fetched
    """
    # Basic URL validation
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError("Invalid URL format. Please enter a complete URL (e.g., https://example.com).")
    
    try:
        # Fetch content from URL
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes
        
        # Parse HTML and extract text content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
            
        # Extract text from main content elements
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td'])
        extracted_text = ' '.join([element.get_text() for element in text_elements])
        
        if not extracted_text.strip():
            raise ValueError("Could not extract meaningful text content from the provided URL.")
            
        return extracted_text, None
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching URL: {str(e)}")