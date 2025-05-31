import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Global driver instance
_driver = None

def get_driver():
    """Get or create a ChromeDriver instance"""
    global _driver
    if _driver is None:
        print("Launching undetected ChromeDriver...")
        options = uc.ChromeOptions()

        # 👉 Uncomment the next line to debug (non-headless)
        options.add_argument('--headless')  # Comment out to see browser window

        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        )

        try:
            _driver = uc.Chrome(options=options)
            _driver.implicitly_wait(5)
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
    """Scrape full HTML content from the target website using a headless browser"""
    driver = get_driver()
    if not driver:
        return ""

    try:
        print(f"Navigating to {website} ...")
        driver.get(website)

        # Wait up to 10 seconds for the <body> tag to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        html = driver.page_source
        if not html or len(html.strip()) < 500:
            print("⚠️ Warning: Possibly blocked or empty response.")
            print("First 500 characters of page:\n", html[:500])
            driver.save_screenshot("render_debug.png")  # Helpful in Render
        return html

    except Exception as e:
        print(f"❌ ChromeDriver error: {e}")
        close_driver()
        return ""

def extract_body_content(html_content):
    """Extract the <body> content from the full HTML"""
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    return str(body_content) if body_content else ""

def clean_body_content(body_content):
    """Remove scripts/styles and clean up body text"""
    soup = BeautifulSoup(body_content, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    cleaned = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in cleaned.splitlines() if line.strip())

def split_dom_content(dom_content, max_length=6000):
    """Split long content into chunks (for LLMs, etc.)"""
    return [
        dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
    ]
