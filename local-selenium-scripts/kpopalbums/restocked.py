from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import re
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
options.add_argument('--incognito')
options.add_argument('--headless')
options.add_argument('--no-sandbox')  # Required for Docker
options.add_argument('--disable-dev-shm-usage')  # Required for Docker

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)


def scroll_to_load_all(driver, max_scrolls=50, scroll_pause=2):
    """
    Scroll down the page to load all products via infinite scroll.
    Returns True if successful, False otherwise.
    """
    logger.info("Scrolling to load all products...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0

    while scroll_count < max_scrolls:
        # Scroll down to bottom
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        time.sleep(scroll_pause)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            # No new content loaded, try scrolling a bit more
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight - 1000);"
            )
            time.sleep(1)
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(scroll_pause)
            new_height = driver.execute_script(
                "return document.body.scrollHeight"
            )

            if new_height == last_height:
                logger.info("No more content to load")
                break

        last_height = new_height
        scroll_count += 1
        logger.debug(f"Scroll {scroll_count}: Height = {new_height}")

    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    return True


# For building output
product_name_list = []
product_link_list = []
product_cost_list = []
product_discount_cost_list = []
product_sign_list = []
rating_list = []
no_of_q_list = []
no_of_reviews_list = []
product_vendor_list = []
product_sold_out_list = []
ds_list = []

page_url = "https://www.kpopalbums.com/collections/restocked-1"

try:
    logger.info(f"Loading page: {page_url}")
    driver.get(page_url)
    time.sleep(3)  # Initial page load

    # Scroll to load all products
    scroll_to_load_all(driver, max_scrolls=50, scroll_pause=2)

    # Get the fully loaded page source
    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
    soup = BeautifulSoup(pg_html, 'lxml')

    # Find all product items
    item_list = soup.find_all(
        "div", {"class": "grid__item effect-hover item pg transition"}
    )
    logger.info(f"Found {len(item_list)} products after scrolling")

    for item in item_list:
        try:
            # Title and URL Information
            title_url = item.find(
                "a",
                class_="item__name pg__sync-url pg__name pg__name--list hide"
            )
            if title_url is None:
                logger.debug("Skipping item: No title URL found")
                continue

            item_title = title_url.get('title', '')
            item_url = "https://www.kpopalbums.com" + str(
                title_url.get('href', '')
            )

            # Product Review Information
            try:
                rating = item.find("div", class_="jdgm-prev-badge")
                if rating is not None:
                    avg_rating = rating.get('data-average-rating')
                    no_of_q = rating.get('data-number-of-questions')
                    no_of_reviews = rating.get('data-number-of-reviews')
                else:
                    avg_rating = None
                    no_of_q = None
                    no_of_reviews = None
            except Exception:
                avg_rating = None
                no_of_q = None
                no_of_reviews = None

            # Pricing Information
            try:
                price_elem = item.find("span", class_="product-price__price")
                if price_elem:
                    price = price_elem.get_text(strip=True)
                    num_price = re.findall(r'\d+\.*\d*', price)[0]
                else:
                    num_price = None
            except (IndexError, AttributeError):
                num_price = None

            try:
                disc_price_elem = item.find(
                    "s",
                    class_="product-price__price product-price__sale"
                )
                if disc_price_elem:
                    disc_price = disc_price_elem.get_text(strip=True)
                    num_disc_price = re.findall(r'\d+\.*\d*', disc_price)[0]
                else:
                    num_disc_price = None
            except (IndexError, AttributeError):
                num_disc_price = None

            # Sold Out Status
            try:
                status = item.find("span", class_="product-price__sold-out")
                soldout_status = status is not None
            except Exception:
                soldout_status = False

            product_name_list.append(item_title)
            product_link_list.append(item_url)
            product_cost_list.append(num_price)
            product_discount_cost_list.append(num_disc_price)
            product_sign_list.append(False)

            rating_list.append(avg_rating)
            no_of_q_list.append(no_of_q)
            no_of_reviews_list.append(no_of_reviews)

            product_vendor_list.append("kpopalbums")
            product_sold_out_list.append(soldout_status)
            ds_list.append(datetime.now().strftime('%Y-%m-%d'))

        except Exception as e:
            logger.warning(f"Failed to parse product item: {e}")
            continue

except Exception as e:
    logger.error(f"Error scraping restocked page: {e}")

driver.quit()

logger.info(f"Scraping complete. Collected {len(product_name_list)} products")

main_list = [
    product_name_list,
    product_link_list,
    product_cost_list,
    product_discount_cost_list,
    product_sign_list,
    rating_list,
    no_of_q_list,
    no_of_reviews_list,
    product_vendor_list,
    product_sold_out_list,
    ds_list
]

column_names = [
    'item',
    'url',
    'discount_price',
    'price',
    'is_autograph',
    'avg_review_value',
    'number_of_questions',
    'number_of_reviews',
    'vendor',
    'is_sold_out',
    'ds'
]

transposed_main_list = np.array(main_list).T.tolist()
lists_equal_len = all(
    len(i) == len(main_list[0]) for i in main_list if len(main_list) > 0
)

if lists_equal_len and len(product_name_list) > 0:
    logger.info("Building output DataFrame")
    output_df = pd.DataFrame(transposed_main_list, columns=column_names)
    output_file = 'kpopalbums_restocked.csv'
    output_df.to_csv(output_file, index=False)
    logger.info(f"Data saved to {output_file}")
else:
    logger.error("ERROR: Mismatched lengths in final lists or no data")
    if not lists_equal_len:
        for i, lst in enumerate(main_list):
            logger.error(f"List {i} length: {len(lst)}")
