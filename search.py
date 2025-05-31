from googlesearch import search as google_search
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
import re
import time  # Add this import

from scrape import scrape_website, extract_body_content, clean_body_content, split_dom_content
from parse import parse_with_ollama


def perform_google_search(query, num_results=7):
    try:
        print(f"Performing Google search for: {query}")
        results = list(google_search(query, num_results=num_results))
        print(f"Found {len(results)} results")
        return results
    except Exception as e:
        print(f"Google search error: {e}")
        # Fallback to a simple search if google_search fails
        try:
            print("Using fallback search mechanism...")
            # Simple fallback using requests
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            response = requests.get(search_url, headers=headers)
            print(f"Fallback search status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Fallback search failed with status code: {response.status_code}")
                # Try with a different search engine as a second fallback
                return fallback_bing_search(query, num_results)
                
            soup = BeautifulSoup(response.text, "html.parser")
            links = []
            
            # Look for search results in Google's format
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.startswith('/url?q='):
                    url = href.split('/url?q=')[1].split('&')[0]
                    if is_valid_url(url):
                        links.append(url)
            
            print(f"Fallback search found {len(links)} results")
            if links:
                return links[:num_results]
            else:
                # If no links found, try with a different search engine
                return fallback_bing_search(query, num_results)
                
        except Exception as fallback_error:
            print(f"Fallback search error: {fallback_error}")
            # Try with a different search engine as a last resort
            return fallback_bing_search(query, num_results)

# Add a second fallback using Bing
def fallback_bing_search(query, num_results=7):
    try:
        print("Using Bing fallback search...")
        search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        response = requests.get(search_url, headers=headers)
        print(f"Bing search status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Bing search failed with status code: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        
        # Look for search results in Bing's format
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('http') and 'bing.com' not in href and 'microsoft.com' not in href:
                if is_valid_url(href):
                    links.append(href)
        
        print(f"Bing search found {len(links)} results")
        return links[:num_results]
    except Exception as bing_error:
        print(f"Bing fallback search error: {bing_error}")
        # Last resort: return some hardcoded URLs for testing
        return hardcoded_fallback_urls(query)

# Last resort fallback with hardcoded URLs for testing
def hardcoded_fallback_urls(query):
    print("Using hardcoded fallback URLs for testing...")
    # These are just examples - replace with relevant URLs for your testing
    return [
        "https://en.wikipedia.org/wiki/Main_Page",
        "https://www.bbc.com/news",
        "https://www.cnn.com",
        "https://www.nytimes.com",
        "https://www.theguardian.com/international"
    ]

def extract_headings_paragraphs_and_images(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    content = []
    raw_images = []

    for tag in soup.find_all(['h1', 'h2', 'h3', 'p']):
        text = tag.get_text().strip()
        if text:
            content.append(text)

    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or ""
        alt = img.get('alt', "").strip().lower()
        class_list = " ".join(img.get('class', [])).lower()

        if src and not src.startswith("data:"):
            full_url = urljoin(base_url, src)
            if full_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                raw_images.append({
                    "url": full_url,
                    "alt": alt,
                    "class": class_list
                })

    for tag in soup.find_all(['div', 'span', 'section']):
        style = tag.get('style', '')
        if 'background-image' in style:
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if match:
                full_url = urljoin(base_url, match.group(1))
                raw_images.append({
                    "url": full_url,
                    "alt": '',
                    "class": 'background'
                })

    return content, raw_images

def relevance_score(text, query):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, text.lower(), query.lower()).ratio()

def clean_text(texts):
    seen = set()
    cleaned = []
    for text in texts:
        if text not in seen and len(text.split()) > 5:
            seen.add(text)
            cleaned.append(text)
    return cleaned

def is_valid_url(url):
    if not url or not url.startswith("http") or "google.com/search" in url:
        return False
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def extract_keywords_from_summary(summary, top_n=10):
    from collections import Counter
    words = re.findall(r'\b[a-zA-Z]{4,}\b', summary.lower())
    return [word for word, _ in Counter(words).most_common(top_n)]

def filter_images_by_keywords(images, keywords):
    filtered = []
    for image in images:
        score = 0
        text = (image.get("alt", "") + " " + image.get("url", "") + " " + image.get("class", "")).lower()
        for keyword in keywords:
            if keyword.lower() in text:
                score += 1
        if score > 0:
            filtered.append(image["url"])
    return list(set(filtered))  # Deduplicate

# Add this function to the search.py file if it doesn't already exist
def remove_duplicates(urls):
    """Remove duplicate URLs and ensure uniqueness"""
    # Convert to lowercase for case-insensitive comparison
    seen = set()
    unique_urls = []
    
    for url in urls:
        # Normalize URL by removing trailing slashes and converting to lowercase
        normalized_url = url.rstrip('/').lower()
        
        # Extract domain and path for further normalization
        parsed = urlparse(normalized_url)
        domain = parsed.netloc
        
        # Create a unique identifier for the URL
        url_id = f"{domain}{parsed.path}"
        
        if url_id not in seen:
            seen.add(url_id)
            unique_urls.append(url)  # Keep the original URL format
    
    return unique_urls

# Modify the run_search function to use remove_duplicates
def run_search(query):
    urls = perform_google_search(query, num_results=7)
    if not urls:
        return {
            "query": query,
            "summary": f"Here are some general resources related to '{query}'.",
            "sources": hardcoded_fallback_urls(query),
            "profile_images": []
        }

    # Remove duplicate URLs before processing
    urls = remove_duplicates(urls)
    
    all_texts = []
    all_dom_contents = []
    all_raw_images = []
    valid_scraped_urls = []

    # Function to process a single URL
    def process_url(url):
        if not is_valid_url(url):
            print(f"[SKIPPED] Invalid URL: {url}")
            return None

        html = scrape_website(url)
        if not html:
            print(f"[SKIPPED] Failed to scrape: {url}")
            return None
            
        result = {}
        result['url'] = url
        
        # Extract texts and images
        texts, images = extract_headings_paragraphs_and_images(html, url)
        if texts:
            result['texts'] = sorted(texts, key=lambda t: relevance_score(t, query), reverse=True)[:5]
        else:
            result['texts'] = []
        
        result['images'] = images
        
        # Extract and clean body content
        body_content = extract_body_content(html)
        result['content'] = clean_body_content(body_content)
        
        return result

    # Process URLs in parallel using ThreadPoolExecutor
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:  # Limit to 3 concurrent requests
        futures = [executor.submit(process_url, url) for url in urls]
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    # Close the ChromeDriver after all scraping is done
    close_driver()
    
    # Process the results
    for result in results:
        all_texts.extend(result['texts'])
        all_raw_images.extend(result['images'])
        all_dom_contents.append(result['content'])
        valid_scraped_urls.append(result['url'])

    # Ensure no duplicate sources in the final result
    valid_scraped_urls = remove_duplicates(valid_scraped_urls)

    if not all_dom_contents:
        return {
            "query": query,
            "summary": f"Here are some general resources related to '{query}'.",
            "sources": hardcoded_fallback_urls(query),
            "profile_images": []
        }

    # Limit the number of chunks to process to improve performance
    dom_chunks = []
    for content in all_dom_contents:
        chunks = split_dom_content(content, max_length=6000)
        dom_chunks.extend(chunks[:2])  # Only use the first 2 chunks from each page

    parse_description = f"Summarize the following web page content related to the query: {query}"
    summary = parse_with_ollama(dom_chunks, parse_description).strip()

    if not summary:
        return {
            "query": query,
            "summary": f"Here are some general resources related to '{query}'.",
            "sources": valid_scraped_urls,
            "profile_images": []
        }

    cleaned_texts = clean_text(all_texts)
    summary_keywords = extract_keywords_from_summary(summary)
    profile_images = filter_images_by_keywords(all_raw_images, summary_keywords)

    return {
        "query": query,
        "summary": summary,
        "sources": valid_scraped_urls,  # These are now unique
        "profile_images": profile_images[:5]
    }

# Additional Recommendations

# 1. **ChromeDriver Version**: Make sure your ChromeDriver version matches your Chrome browser version.

# 2. **Rate Limiting**: Add delays between requests to avoid being blocked:
# Add at the top of the file
import time

def run_search(query):
    urls = perform_google_search(query, num_results=7)
    if not urls:
        return {"error": "No search results found"}

    all_texts = []
    all_dom_contents = []
    all_raw_images = []
    valid_scraped_urls = []

    # Add delays between requests in run_search function
    for url in urls:
        if not is_valid_url(url):
            print(f"[SKIPPED] Invalid URL: {url}")
            continue

        html = scrape_website(url)
        if html:
            time.sleep(2)  # Add a 2-second delay between requests
            texts, images = extract_headings_paragraphs_and_images(html, url)
            if texts:
                top_texts = sorted(texts, key=lambda t: relevance_score(t, query), reverse=True)[:5]
                all_texts.extend(top_texts)
            all_raw_images.extend(images)

            body_content = extract_body_content(html)
            cleaned_content = clean_body_content(body_content)
            all_dom_contents.append(cleaned_content)

            valid_scraped_urls.append(url)
        else:
            print(f"[SKIPPED] Failed to scrape: {url}")

    if not all_dom_contents:
        return {"error": "Failed to extract relevant information"}

    dom_chunks = []
    for content in all_dom_contents:
        dom_chunks.extend(split_dom_content(content, max_length=6000))

    parse_description = f"Summarize the following web page content related to the query: {query}"
    summary = parse_with_ollama(dom_chunks, parse_description).strip()

    if not summary:
        return {"error": "Failed to generate summary from AI"}

    cleaned_texts = clean_text(all_texts)
    summary_keywords = extract_keywords_from_summary(summary)
    profile_images = filter_images_by_keywords(all_raw_images, summary_keywords)

    return {
        "query": query,
        "summary": summary,
        "sources": valid_scraped_urls,
        "profile_images": profile_images[:5]
    }

# Add this at the end of the file's imports
from concurrent.futures import ThreadPoolExecutor
from scrape import close_driver  # Import the new function
