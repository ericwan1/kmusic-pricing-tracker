from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
import json
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

# Import after driver is created (scraping_module uses the driver)
from scraping_module import get_soup  # noqa: E402

# For building output
product_name_list = []
product_link_list = []
product_cost_list = []
product_sign_list = []
rating_list = []
no_of_q_list = []
no_of_reviews_list = []
product_vendor_list = []
product_sold_out_list = []
ds_list = []

# We continue scraping until we come across an element that indicates an
# empty page
index = 1
not_an_empty_page = True
max_pages = 15

logger.info(f"Starting scrape for new-releases (max {max_pages} pages)")

while not_an_empty_page and index < max_pages:
    try:
        logger.info(f"Scraping page {index}")
        base_url = "https://www.musicplaza.com/collections/new-releases"
        pg_count_url = f"{base_url}?page={index}&view=ajax"
        soup = get_soup(pg_count_url)

        # Get Product HTML Block - new structure uses grid-item
        item_list = soup.find_all("div", class_="grid-item")

        if len(item_list) == 0:
            logger.warning(
                f"Page {index}: No items found. Page may be empty or "
                "structure changed."
            )
            not_an_empty_page = False
            break

        logger.info(f"Page {index}: Found {len(item_list)} items")

        for item_idx, item in enumerate(item_list):
            try:
                # Title & URL Info - new structure uses h3.card__heading
                title_elem = item.find("h3", class_="card__heading")
                if title_elem is None:
                    logger.debug(
                        f"Page {index}, Item {item_idx}: Missing title "
                        "element"
                    )
                    continue

                url_tag = title_elem.find(
                    "a", class_="link-product-variant"
                )
                if url_tag is None:
                    # Try finding any link in the title element
                    url_tag = title_elem.find("a")
                    if url_tag is None:
                        logger.debug(
                            f"Page {index}, Item {item_idx}: Missing URL tag"
                        )
                        continue

                item_title = url_tag.get_text(strip=True)
                if not item_title:
                    # Fallback to aria-label if text is empty
                    item_title = url_tag.get('aria-label', '')
                href = url_tag.get('href', '')
                if not href.startswith('http'):
                    item_url = "https://www.musicplaza.com" + href
                else:
                    item_url = href

                # Price Information - new structure uses div.price
                try:
                    price_container = item.find("div", class_="price")
                    if price_container is None:
                        logger.debug(
                            f"Page {index}, Item {item_idx}: Missing price"
                        )
                        continue

                    price_elem = price_container.find("p", class_="price")
                    if price_elem is None:
                        logger.debug(
                            f"Page {index}, Item {item_idx}: Missing price "
                            "paragraph"
                        )
                        continue

                    price_span = price_elem.find("span")
                    if price_span is None:
                        logger.debug(
                            f"Page {index}, Item {item_idx}: Missing price "
                            "span"
                        )
                        continue

                    item_price = price_span.get_text(strip=True)
                    # Extract numeric price (remove $ and commas)
                    price_matches = re.findall(r'\d+\.?\d*', item_price)
                    if not price_matches:
                        logger.debug(
                            f"Page {index}, Item {item_idx}: No price found "
                            f"in text: {item_price}"
                        )
                        continue
                    num_price = price_matches[0]
                except (IndexError, AttributeError) as e:
                    logger.debug(
                        f"Page {index}, Item {item_idx}: Price parsing "
                        f"error: {e}"
                    )
                    continue

                # Sold Out Status - new structure uses flair-badge
                try:
                    so_badge = item.find("div", class_="flair-badge")
                    if so_badge is not None:
                        so_text = so_badge.get_text(strip=True)
                        so_status = "SOLD OUT" in so_text.upper()
                    else:
                        # Also check x-labels-data attribute
                        link_elem = item.find(
                            "a", class_="link-product-variant"
                        )
                        if link_elem:
                            labels_data = link_elem.get('x-labels-data', '')
                            if labels_data:
                                try:
                                    labels = json.loads(labels_data)
                                    so_status = not labels.get(
                                        'available', True
                                    )
                                except Exception:
                                    so_status = False
                            else:
                                so_status = False
                        else:
                            so_status = False
                except Exception:
                    so_status = False

                # Review Information - may not be present in new structure
                item_avg_rating = None
                item_no_of_q = None
                item_no_of_r = None

                # Add all scraped information to lists
                product_name_list.append(item_title)
                product_link_list.append(item_url)
                product_cost_list.append(num_price)
                rating_list.append(item_avg_rating)
                no_of_q_list.append(item_no_of_q)
                no_of_reviews_list.append(item_no_of_r)
                product_sold_out_list.append(so_status)
                product_sign_list.append(False)
                product_vendor_list.append('musicplaza')
                ds_list.append(datetime.now().strftime('%Y-%m-%d'))

            except Exception as e:
                logger.warning(
                    f"Page {index}, Item {item_idx}: Failed to parse "
                    f"item: {e}"
                )
                continue

        index += 1

    except Exception as e:
        logger.error(f"Page {index}: Scraping failed - {e}")
        logger.error(f"Page {index}: URL was {pg_count_url}")
        index += 1
        continue

driver.quit()

logger.info(f"Scraping complete. Collected {len(product_name_list)} products")

main_list = [
    product_name_list,
    product_link_list,
    product_cost_list,
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
    output_file = 'musicplaza_new_releases.csv'
    output_df.to_csv(output_file, index=False)
    logger.info(f"Data saved to {output_file}")
else:
    logger.error("ERROR: Mismatched lengths in final lists or no data")
    if not lists_equal_len:
        for i, lst in enumerate(main_list):
            logger.error(f"List {i} length: {len(lst)}")
