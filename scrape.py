# filename: scrape.py

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import re
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetch HTML content using Playwright (async version)
async def fetch_html_with_playwright(url: str, timeout=15000) -> str:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = await browser.new_context()
            page = await context.new_page()
            logger.info(f"Navigating to {url}")
            await page.goto(url, timeout=timeout, wait_until="load")
            content = await page.content()
            await browser.close()
            return content
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading {url}")
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
    return ""

# Sync wrapper to call from Flask or other sync code
def scrape_website(url, timeout=15000):
    return asyncio.run(fetch_html_with_playwright(url, timeout))

def extract_body_content(html):
    """
    Extract main body text content from HTML.
    """
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body
    if body:
        return body.get_text(separator='\n').strip()
    else:
        return ""

def clean_body_content(text):
    """
    Clean text by removing excessive whitespace.
    """
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
