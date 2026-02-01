"""
Web scraping module using Jina AI Reader with fallback to BeautifulSoup.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional
import config

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Custom exception for scraping errors."""
    pass


def fetch_job_text(url: str) -> dict:
    """
    Fetch clean text from job posting URL using Jina AI Reader.
    Fallback to requests + BeautifulSoup if Jina fails.
    
    Args:
        url: Job posting URL
        
    Returns:
        Dictionary with keys:
        - 'text': extracted text (empty string if failed)
        - 'success': bool indicating if fetch was successful
        - 'error': error message if failed (None if successful)
        - 'source': 'jina', 'beautifulsoup', or 'failed'
        
    Note: This function no longer raises ScraperError. Check 'success' field instead.
    """
    # Try Jina AI Reader first
    try:
        logger.info(f"Fetching content from URL using Jina AI Reader: {url}")
        text = _fetch_with_jina(url)
        if text:
            logger.info("Successfully fetched content with Jina AI Reader")
            return {
                'text': text,
                'success': True,
                'error': None,
                'source': 'jina'
            }
    except Exception as e:
        logger.warning(f"Jina AI Reader failed: {str(e)}, trying fallback method")
    
    # Fallback to BeautifulSoup
    try:
        logger.info("Using BeautifulSoup fallback method")
        text = _fetch_with_beautifulsoup(url)
        if text:
            logger.info("Successfully fetched content with BeautifulSoup")
            return {
                'text': text,
                'success': True,
                'error': None,
                'source': 'beautifulsoup'
            }
    except Exception as e:
        logger.error(f"BeautifulSoup fallback also failed: {str(e)}")
    
    # Both methods failed
    error_msg = (
        "Could not scrape this URL. The website may require login, "
        "block automated access, or be temporarily unavailable.\n\n"
        "💡 Tip: Copy and paste the job description text directly, "
        "and I'll extract the details for you!"
    )
    
    return {
        'text': '',
        'success': False,
        'error': error_msg,
        'source': 'failed'
    }


def _fetch_with_jina(url: str) -> Optional[str]:
    """
    Fetch content using Jina AI Reader API.
    
    Args:
        url: URL to fetch
        
    Returns:
        Clean text content or None if failed
    """
    jina_url = f"{config.JINA_READER_URL}{url}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Add API key if available
    if config.JINA_API_KEY:
        headers['Authorization'] = f'Bearer {config.JINA_API_KEY}'
    
    try:
        response = requests.get(
            jina_url,
            headers=headers,
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        text = response.text.strip()
        if len(text) > 100:  # Ensure we got substantial content
            return text
        
        return None
    except Exception as e:
        logger.warning(f"Jina AI Reader request failed: {str(e)}")
        return None


def _fetch_with_beautifulsoup(url: str) -> Optional[str]:
    """
    Fetch content using requests and BeautifulSoup.
    
    Args:
        url: URL to fetch
        
    Returns:
        Clean text content or None if failed
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if len(text) > 100:  # Ensure we got substantial content
            return text
        
        return None
    except Exception as e:
        logger.error(f"BeautifulSoup fetch failed: {str(e)}")
        return None


def test_scraper(url: str) -> None:
    """
    Test the scraper with a given URL.
    
    Args:
        url: URL to test
    """
    try:
        text = fetch_job_text(url)
        print(f"Successfully fetched {len(text)} characters")
        print("\nFirst 500 characters:")
        print(text[:500])
    except ScraperError as e:
        print(f"Scraper Error: {str(e)}")


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    test_url = "https://www.bdjobs.com/jobs/"
    test_scraper(test_url)
