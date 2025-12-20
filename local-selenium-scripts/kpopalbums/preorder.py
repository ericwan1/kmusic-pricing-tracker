from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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

# Import after driver is created (scraping_module uses the driver)
from scraping_module import get_page_count, get_soup  # noqa: E402

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

try:
    base_page_url = "https://www.kpopalbums.com/collections/pre-order"
    page_url = f"{base_page_url}?page=1&view=ajax"
    pass_tag = "div"
    class_name = ("ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs "
                  "text-uppercase fw-bold")
    match_dict = {"class": class_name}
    total_pages = get_page_count(page_url, pass_tag, match_dict)
    logger.info(f"Found {total_pages} pages to scrape")
except Exception as e:
    logger.error(f"Could not get page count: {e}")
    total_pages = 0

for page_ind in range(1, total_pages + 1):
    try:
        logger.info(f"Scraping page {page_ind}/{total_pages}")
        base_url = "https://www.kpopalbums.com/collections/pre-order"
        pg_count_url = f"{base_url}?page={page_ind}&view=ajax"
        soup = get_soup(pg_count_url)
        item_list = soup.find_all(
            "div", {"class": "grid__item effect-hover item pg transition"}
        )

        if len(item_list) == 0:
            logger.warning(f"Page {page_ind}: No items found")
            continue

        logger.info(f"Page {page_ind}: Found {len(item_list)} items")

        for item in item_list:
            try:
                # Title and URL Information
                class_name = ("item__name pg__sync-url pg__name "
                              "pg__name--list hide")
                title_url = item.find("a", class_=class_name)
                if title_url is None:
                    logger.debug(f"Page {page_ind}: Item missing title URL")
                    continue

                item_title = title_url.get('title', '')
                href = title_url.get('href', '')
                item_url = "https://www.kpopalbums.com" + str(href)

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
                    price_elem = item.find(
                        "span", class_="product-price__price"
                    )
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                        num_price = re.findall(r'\d+\.*\d*', price)[0]
                    else:
                        num_price = None
                        logger.debug(f"Page {page_ind}: Item missing price")
                except (IndexError, AttributeError) as e:
                    num_price = None
                    logger.debug(f"Page {page_ind}: Price parsing error: {e}")

                try:
                    disc_price_elem = item.find(
                        "s",
                        class_="product-price__price product-price__sale"
                    )
                    if disc_price_elem:
                        disc_price = disc_price_elem.get_text(strip=True)
                        num_disc_price = re.findall(
                            r'\d+\.*\d*', disc_price
                        )[0]
                    else:
                        num_disc_price = None
                except (IndexError, AttributeError):
                    num_disc_price = None

                # Sold Out Status
                try:
                    status = item.find(
                        "span", class_="product-price__sold-out"
                    )
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
                logger.warning(f"Page {page_ind}: Failed to parse item: {e}")
                continue

    except Exception as e:
        logger.error(f"Page {page_ind}: Scraping failed - {e}")
        logger.error(f"Page {page_ind}: URL was {pg_count_url}")
        continue

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
    output_file = 'kpopalbums_pre_order.csv'
    output_df.to_csv(output_file, index=False)
    logger.info(f"Data saved to {output_file}")
else:
    logger.error("ERROR: Mismatched lengths in final lists or no data")
    if not lists_equal_len:
        for i, lst in enumerate(main_list):
            logger.error(f"List {i} length: {len(lst)}")
