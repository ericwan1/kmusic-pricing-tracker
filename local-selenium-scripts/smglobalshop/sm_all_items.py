from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import time
import re
import random
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import numpy as np
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chrome path - configurable via environment variable for Docker
chrome_path = os.getenv(
    'CHROME_BINARY_PATH',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
)

options = Options()
if os.path.exists(chrome_path):
    options.binary_location = chrome_path
else:
    logger.warning(f"Chrome binary not found at {chrome_path}, "
                   "using system default")

options.add_argument("start-maximized")
options.add_argument('--ignore-certificate-errors')
# Run in headless by default, but allow disabling with env var
if os.getenv('NO_HEADLESS', 'false').lower() != 'true':
    options.add_argument('--headless')
    options.add_argument('--headless=new')  # Use new headless mode
    logger.info("Running in headless mode")
else:
    logger.info("Running in visible mode (NO_HEADLESS=true)")
options.add_argument('--no-sandbox')  # Required for Docker
options.add_argument('--disable-dev-shm-usage')  # Required for Docker
# Add realistic user agent to avoid detection
options.add_argument(
    'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)
# Disable automation flags
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
# Set window size to look more realistic
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Remove webdriver property to avoid detection
driver.execute_cdp_cmd(
    'Page.addScriptToEvaluateOnNewDocument',
    {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        '''
    }
)

logger.info("Starting scrape for smglobalshop all items")

# Initialize lists before try block to avoid NameError
name_list = []
link_list = []
cost_list = []
autograph_list = []
vendor_list = []
so_list = []
ds_list = []

try:
    logger.info("Navigating to page...")
    driver.get("https://global.shop.smtown.com/collections/all")

    # Wait a bit for initial page load (more realistic delay)
    logger.info("Waiting for page to load...")
    time.sleep(8)

    # Check if we got an error page
    page_source_check = driver.page_source
    if ("ERR_NAME_NOT_RESOLVED" in page_source_check or
            "This site can't be reached" in page_source_check or
            "DNS_PROBE" in page_source_check):
        raise Exception(
            "Failed to load page: DNS resolution error. "
            "The website may be down or there's a network issue. "
            "Check your network connection. "
            "If this persists, you may be blocked or need to check "
            "your DNS settings."
        )

    # Wait for page to actually load - wait for product cards to appear
    try:
        logger.info("Waiting for product content to appear...")
        # Wait for product cards to be present in the page
        WebDriverWait(driver, 45).until(
            lambda d: "product-card" in d.page_source.lower() and
            "collection-products" in d.page_source.lower()
        )
        logger.info("Page content loaded successfully")
        # Additional wait to let JavaScript finish loading
        time.sleep(3)
    except TimeoutException:
        # Double-check if we have an error page
        current_source = driver.page_source
        if "ERR_NAME_NOT_RESOLVED" in current_source or \
           "DNS_PROBE" in current_source:
            raise Exception(
                "Page failed to load: DNS error detected. "
                "Please check your network connection."
            )
        # Check for blocking/access denied messages
        if ("access denied" in current_source.lower() or
                "blocked" in current_source.lower() or
                ("cloudflare" in current_source.lower() and
                 "checking your browser" in current_source.lower())):
            raise Exception(
                "Possible blocking detected. The site may be blocking "
                "automated access. Try running without headless mode or "
                "check if you can access the site manually in a browser."
            )
        logger.warning(
            "Timeout waiting for product elements, but continuing anyway"
        )

    logger.info("Starting to load all items by scrolling and clicking")

    # First, try to find and count initial product cards
    # Note: # is part of class name, escape it or use attribute selector
    initial_count = len(
        driver.find_elements(By.CSS_SELECTOR, "div[class*='product-card']")
    )
    logger.info(f"Initial product count: {initial_count}")

    count = 1
    max_clicks = 200  # Increased significantly for 1300+ items
    last_product_count = initial_count
    no_change_count = 0

    while count < max_clicks:
        try:
            # Try to find the "Load More" button with multiple selectors
            button = None
            button_found = False

            # Try primary xpath
            try:
                xpath = '//*[@id="usf_container"]/div[2]/div[3]/div/button'
                button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                button_found = True
            except TimeoutException:
                # Try alternative selectors
                try:
                    # Try by text content
                    button = driver.find_element(
                        By.XPATH,
                        "//button[contains(text(), 'Load More') or "
                        "contains(text(), 'LOAD MORE')]"
                    )
                    button_found = True
                except Exception:
                    try:
                        # Try by partial text match using XPath
                        # (CSS doesn't support :contains)
                        xpath_text = (
                            "//button[contains(translate(text(), "
                            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                            "'abcdefghijklmnopqrstuvwxyz'), 'load more')]"
                        )
                        button = driver.find_element(By.XPATH, xpath_text)
                        button_found = True
                    except Exception:
                        pass

            if button_found and button:
                # Scroll to button first (more human-like)
                scroll_script = (
                    "arguments[0].scrollIntoView({behavior: 'smooth', "
                    "block: 'center'});"
                )
                driver.execute_script(scroll_script, button)
                time.sleep(random.uniform(1, 2))  # Random delay

                actions = ActionChains(driver)
                actions.move_to_element(button).pause(
                    random.uniform(0.5, 1.5)
                ).click().perform()
                logger.info(
                    f"LOAD MORE RESULTS button clicked (attempt {count})"
                )
            else:
                # No button found, use scrolling
                logger.info("No button found, scrolling to load more items...")
                # Get current scroll position
                current_scroll = driver.execute_script(
                    "return window.pageYOffset;"
                )
                page_height = driver.execute_script(
                    "return document.body.scrollHeight;"
                )

                # Gradual scroll down (more realistic)
                scroll_step = 500
                for scroll_pos in range(
                    int(current_scroll),
                    int(page_height),
                    scroll_step
                ):
                    driver.execute_script(
                        f"window.scrollTo(0, {scroll_pos});"
                    )
                    time.sleep(random.uniform(0.3, 0.7))

                # Final scroll to bottom
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(random.uniform(2, 4))

                # Check if page height increased (new content loaded)
                new_page_height = driver.execute_script(
                    "return document.body.scrollHeight;"
                )
                if new_page_height > page_height:
                    logger.info(
                        f"Page height increased: {page_height} -> "
                        f"{new_page_height}"
                    )

            # Wait a bit for new items to load
            time.sleep(random.uniform(2, 4))

            # Count current products
            current_product_count = len(
                driver.find_elements(
                    By.CSS_SELECTOR, "div[class*='product-card']"
                )
            )

            if current_product_count > last_product_count:
                diff = current_product_count - last_product_count
                logger.info(
                    f"Products loaded: {last_product_count} -> "
                    f"{current_product_count} (+{diff})"
                )
                last_product_count = current_product_count
                no_change_count = 0
            else:
                no_change_count += 1
                if no_change_count >= 3:
                    logger.info(
                        f"No new products loaded after {no_change_count} "
                        f"attempts. Total products: {current_product_count}"
                    )
                    break

            count += 1
            # Random delay between attempts
            time.sleep(random.uniform(1, 3))

        except Exception as e:
            logger.warning(f"Error during loading attempt {count}: {e}")
            # Try scrolling as fallback
            try:
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(3)
            except Exception:
                pass
            count += 1
            if count > 10:  # Give up after 10 errors
                break

    final_product_count = len(
        driver.find_elements(By.CSS_SELECTOR, "div[class*='product-card']")
    )
    logger.info(
        f"Finished loading items. Total products found: {final_product_count}"
    )

    # Wait a bit for any final rendering
    time.sleep(3)

    # Extract item information
    pg_html = driver.page_source

    # Final check: Make sure we didn't get an error page
    if ("ERR_NAME_NOT_RESOLVED" in pg_html or
            "This site can't be reached" in pg_html or
            "DNS_PROBE" in pg_html):
        raise Exception(
            "Error page detected in HTML. The website failed to load. "
            "This could be due to network issues or the site being down."
        )

    # Check if we have actual product content
    if "product-card" not in pg_html.lower():
        logger.warning(
            "No product-card elements found in page source. "
            "The page may not have loaded correctly."
        )

    soup = BeautifulSoup(pg_html, 'lxml')

    # Debug: Save raw HTML and prettified soup for inspection
    debug_dir = os.path.join(os.path.dirname(__file__), '..', '..')
    raw_html_path = os.path.join(
        debug_dir, 'debug_smglobalshop_raw.html'
    )
    prettified_html_path = os.path.join(
        debug_dir, 'debug_smglobalshop.html'
    )

    with open(raw_html_path, 'w', encoding='utf-8') as f:
        f.write(pg_html)
    logger.info(f"Saved raw page HTML to {raw_html_path}")

    with open(prettified_html_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    logger.info(
        f"Saved prettified HTML to {prettified_html_path} for inspection"
    )

    # Find product cards - selector is "#product-card" (# is part of class)
    all_items = soup.find_all("div", class_="#product-card")

    if len(all_items) == 0:
        logger.warning("No items found with #product-card selector")
        # Try alternative: product-card without the #
        all_items = soup.find_all(
            "div",
            class_=lambda x: x and "product-card" in str(x)
        )
        if len(all_items) > 0:
            logger.info(
                f"Found {len(all_items)} items with "
                "alternative product-card selector"
            )
        else:
            logger.warning("No product cards found at all")

    logger.info(f"Found {len(all_items)} items to process")

    for item_idx, item in enumerate(all_items):
        try:
            # Find the link element (stretched-link)
            link_elem = item.find("a", class_="stretched-link")
            if link_elem is None:
                # Try finding any link
                link_elem = item.find("a")
                if link_elem is None:
                    logger.debug(f"Item {item_idx}: Missing link element")
                    continue

            # Extract URL
            href = link_elem.get('href', '')
            if not href:
                logger.debug(f"Item {item_idx}: Missing href")
                continue

            # Fix URL if needed
            if href.startswith('http'):
                item_link = href
            elif href.startswith('/'):
                item_link = "https://global.shop.smtown.com" + href
            else:
                item_link = "https://global.shop.smtown.com/" + href

            # Extract title from product-card-title
            title_elem = item.find("h3", class_="#product-card-title")
            if title_elem:
                # Get text from span inside, or from h3 directly
                span_elem = title_elem.find("span")
                if span_elem:
                    item_name = span_elem.get_text(strip=True)
                else:
                    item_name = title_elem.get_text(strip=True)
            else:
                # Fallback: try to get from link aria-label or text
                item_name = (
                    link_elem.get('aria-label', '') or
                    link_elem.get_text(strip=True)
                )

            if not item_name:
                logger.debug(f"Item {item_idx}: Missing title")
                continue

            # Extract price from product-card-price
            price_elem = item.find("div", class_="#product-card-price")
            item_cost = None
            if price_elem:
                price_value_elem = price_elem.find(
                    "span", class_="#price-value"
                )
                if price_value_elem:
                    price_text = price_value_elem.get_text(strip=True)
                    # Extract numeric value (e.g., "$6.90" -> "6.90")
                    price_match = re.search(
                        r'[\d,]+\.?\d*', price_text.replace(',', '')
                    )
                    if price_match:
                        item_cost = price_match.group(0)

            if item_cost is None:
                logger.debug(f"Item {item_idx}: Missing price")
                continue

            # Check sold out status - look for badges or unavailable
            so_status = False
            try:
                # Check for sold out badges
                badges_elem = item.find(
                    "div", class_="#product-card-custom-badges"
                )
                if badges_elem:
                    badge_text = badges_elem.get_text(strip=True).lower()
                    if "sold out" in badge_text or "unavailable" in badge_text:
                        so_status = True
            except Exception as e:
                logger.debug(
                    f"Item {item_idx}: Error checking sold out status: {e}"
                )

            name_list.append(item_name)
            link_list.append(item_link)
            cost_list.append(item_cost)
            autograph_list.append(False)
            vendor_list.append("smglobalshop")
            so_list.append(so_status)
            ds_list.append(datetime.now().strftime('%Y-%m-%d'))

        except Exception as e:
            logger.warning(f"Item {item_idx}: Failed to parse item: {e}")
            continue

except Exception as e:
    logger.error(f"Scraping failed: {e}")
    # Try to save HTML even if there was an error, for debugging
    try:
        pg_html = driver.page_source
        soup = BeautifulSoup(pg_html, 'lxml')
        debug_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        raw_html_path = os.path.join(
            debug_dir, 'debug_smglobalshop_raw.html'
        )
        prettified_html_path = os.path.join(
            debug_dir, 'debug_smglobalshop.html'
        )

        with open(raw_html_path, 'w', encoding='utf-8') as f:
            f.write(pg_html)
        logger.info(
            f"Saved raw page HTML to {raw_html_path} (after error)"
        )

        with open(prettified_html_path, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        logger.info(
            f"Saved prettified HTML to {prettified_html_path} (after error)"
        )
    except Exception as save_error:
        logger.warning(f"Could not save HTML for debugging: {save_error}")
finally:
    driver.quit()

logger.info(f"Scraping complete. Collected {len(name_list)} products")

main_list = [
    name_list,
    link_list,
    cost_list,
    autograph_list,
    vendor_list,
    so_list,
    ds_list
]

column_names = [
    'item',
    'url',
    'price',
    'is_autograph',
    'vendor',
    'is_sold_out',
    'ds'
]

transposed_main_list = np.array(main_list).T.tolist()
lists_equal_len = all(
    len(i) == len(main_list[0]) for i in main_list if len(main_list) > 0
)

if lists_equal_len and len(name_list) > 0:
    logger.info("Building output DataFrame")
    output_df = pd.DataFrame(transposed_main_list, columns=column_names)
    output_file = 'smglobalshop_all.csv'
    output_df.to_csv(output_file, index=False)
    logger.info(f"Data saved to {output_file}")
else:
    logger.error("ERROR: Mismatched lengths in final lists or no data")
    if not lists_equal_len:
        for i, lst in enumerate(main_list):
            logger.error(f"List {i} length: {len(lst)}")
