# filename: scrape.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_playwright_instance = None
_browser = None
_context = None

def init_playwright():
    global _playwright_instance, _browser, _context
    if _playwright_instance is None:
        _playwright_instance = sync_playwright().start()
        _browser = _playwright_instance.chromium.launch(headless=True)
        _context = _browser.new_context()
        logger.info("Playwright initialized.")

def close_playwright():
    global _playwright_instance, _browser, _context
    if _context:
        _context.close()
        _context = None
    if _browser:
        _browser.close()
        _browser = None
    if _playwright_instance:
        _playwright_instance.stop()
        _playwright_instance = None
    logger.info("Playwright closed.")

def scrape_website(url, timeout=15000):
    """
    Fetch the full HTML content of a webpage using Playwright.
    :param url: URL to scrape
    :param timeout: max timeout in ms (default 15 seconds)
    :return: HTML content string or None on failure
    """
    try:
        init_playwright()
        page = _context.new_page()
        logger.info(f"Navigating to {url}")
        page.goto(url, timeout=timeout, wait_until="load")
        html = page.content()
        page.close()
        return html
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading {url}")
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
    return None

def extract_body_content(html):
    """
    Extract main body text content from HTML. (Your existing logic here)
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body
    if body:
        return body.get_text(separator='\n').strip()
    else:
        return ""

def clean_body_content(text):
    """
    Clean text by removing excessive whitespace, etc. (Your existing logic)
    """
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def split_dom_content(content, max_length=6000):
    """
    Split long text content into chunks no longer than max_length.
    """
    chunks = []
    start = 0
    while start < len(content):
        end = start + max_length
        chunks.append(content[start:end])
        start = end
    return chunks

# Call this when app shuts down or after batch scraping to release resources
def close_driver():
    close_playwright()
