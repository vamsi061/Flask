import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time

# Global driver instance
_driver = None

def get_driver():
    """Get or create a ChromeDriver instance"""
    global _driver
    if _driver is None:
        print("Launching undetected ChromeDriver...")
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        try:
            _driver = uc.Chrome(options=options)
            _driver.implicitly_wait(5)  # Reduced from 10 to 5 seconds
        except Exception as e:
            print(f"ChromeDriver initialization error: {e}")
            return None
    return _driver

def close_driver():
    """Close the global driver instance"""
    global _driver
    if _driver:
        try:
            _driver.quit()
        except:
            pass
        _driver = None
        print("ChromeDriver session ended.")

def scrape_website(website):
    driver = get_driver()
    if not driver:
        return ""
    
    try:
        print(f"Navigating to {website} ...")
        driver.get(website)
        # Reduced wait time
        time.sleep(1)  # Reduced from implicit wait of 10 seconds
        html = driver.page_source
        return html
    except Exception as e:
        print(f"ChromeDriver error: {e}")
        # If there's an error, try to reset the driver
        close_driver()
        return ""

def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    return str(body_content) if body_content else ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    cleaned = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in cleaned.splitlines() if line.strip())

def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
    ]