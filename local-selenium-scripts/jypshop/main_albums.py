from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import re
import math
from datetime import datetime
import pandas as pd
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

product_name_list = []
product_link_list = []
product_model_list = []
product_disc_cost_list = []
product_orig_cost_list = []
sold_out_list = []
ds_list = []

output_df = []


def _extract_product_data(prod, index, page_num, url):
    """
    Extract product data handling both old and new HTML structures.
    Returns dict with product data or None if extraction fails.
    """
    # Try to find description div - handle both structures
    # New structure: description is inside <div class="box">
    # Old structure: description is directly in <li>
    box = prod.find('div', class_="box")
    if box:
        product_description = box.find('div', class_="description")
    else:
        product_description = prod.find('div', class_="description")

    if product_description is None:
        logger.debug(f"Product {index}: No description div found")
        return None

    # Extract product model (may not exist in old structure)
    product_model_elem = product_description.find(
        'div', class_="product_model"
    )
    product_model = (product_model_elem.get_text(strip=True)
                     if product_model_elem else "")

    # Extract product name - handle both structures
    # New: <div class="name"><a>...</a></div>
    # Old: <strong class="name"><a>...</a></strong>
    name_elem = (product_description.find('div', class_="name") or
                 product_description.find('strong', class_="name"))
    if name_elem is None:
        logger.debug(f"Product {index}: No name element found")
        return None

    name_link = name_elem.find('a')
    if name_link is None:
        logger.debug(f"Product {index}: No link found in name element")
        return None

    product_name = name_link.get_text(strip=True)
    product_href = name_link.get('href', '')

    # Extract prices - try both structures
    orig_cost = 0.0
    disc_cost = 0.0

    # Look for price elements in the product (works for both structures)
    discount_elem = prod.find('li', {'rel': 'Discounted Price'})
    if discount_elem:
        try:
            discount_text = discount_elem.get_text(strip=True)
            price_match = re.findall(r'\d+\.*\d*', discount_text)
            if price_match:
                disc_cost = float(price_match[0])
        except (ValueError, IndexError):
            pass

    price_elem = prod.find('li', {'rel': 'Price'})
    if price_elem:
        try:
            price_text = price_elem.get_text(strip=True)
            price_match = re.findall(r'\d+\.*\d*', price_text)
            if price_match:
                orig_cost = float(price_match[0])
        except (ValueError, IndexError):
            pass

    # Check if sold out - handle both structures
    sold_out = (
        prod.find('div', class_="soldout_icon") is not None or
        product_description.find('div', class_="soldout_icon") is not None
    )

    return {
        'name': product_name,
        'href': product_href,
        'model': product_model,
        'disc_price': disc_cost,
        'orig_price': orig_cost,
        'sold_out': sold_out
    }


urls = ['https://en.thejypshop.com/category/cdlp/56/',
        'https://en.thejypshop.com/category/cdlp/62/',
        'https://en.thejypshop.com/category/cdlp/68/',
        'https://en.thejypshop.com/category/cdlp/36/',
        'https://en.thejypshop.com/category/cdlp/93/',
        'https://en.thejypshop.com/category/cdlp/52/',
        'https://en.thejypshop.com/category/cdlp/59/',
        'https://en.thejypshop.com/category/cdlp/421/',
        'https://en.thejypshop.com/category/cdlp/444/',
        'https://en.thejypshop.com/category/cdlp/449/',
        'https://en.thejypshop.com/category/cdlp/463/']

for url in urls:
    data = driver.get(url)
    time.sleep(3)

    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')

    soup = BeautifulSoup(pg_html, 'lxml')
    logger.info(f"Processing URL: {url}")

    try:
        prdcount_elem = soup.find('div', class_="prdcount")
        if prdcount_elem is None:
            raise AttributeError("prdcount element not found")
        total_item_count_text = prdcount_elem.get_text(strip=True)
        total_items = int(re.findall(r'\d+\.*\d*', total_item_count_text)[0])
        total_pages = math.ceil(total_items/16)
        logger.info(f"Found {total_items} items across {total_pages} pages")
    except (AttributeError, IndexError, ValueError) as e:
        logger.error(f"Could not parse item count on {url}: {e}")
        continue

    # Calculate items per page
    item_cnt_per_page = [1] * total_pages
    for ind in range(0, total_pages):
        if total_items - 16 >= 0:
            item_cnt_per_page[ind] = 16
            total_items -= 16
        else:
            item_cnt_per_page[ind] = total_items

    for page_num in range(1, total_pages + 1):
        if page_num != 1:
            new_site = f"{url}?page={page_num}"
            data = driver.get(new_site)
            time.sleep(3)
            # Do this to get new page results for pages 2 and onwards
            pg_html = driver.page_source
            pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
            soup = BeautifulSoup(pg_html, 'lxml')

        all_prods_list = soup.find_all('li', class_="xans-record-")
        xans_cnt = len(all_prods_list)
        logger.info(f"Page {page_num}: Found {xans_cnt} product elements")

        # Loop through album items
        start_idx = (xans_cnt - total_pages -
                     (item_cnt_per_page[page_num-1] * 4))
        end_idx = xans_cnt - total_pages
        for i in range(start_idx, end_idx, 4):
            try:
                prod = all_prods_list[i]
                product_data = _extract_product_data(prod, i, page_num, url)
                if product_data:
                    product_name_list.append(product_data['name'])
                    product_link_list.append(product_data['href'])
                    product_model_list.append(product_data['model'])
                    product_disc_cost_list.append(product_data['disc_price'])
                    product_orig_cost_list.append(product_data['orig_price'])
                    sold_out_list.append(product_data['sold_out'])
                    ds_list.append(datetime.now().strftime('%Y-%m-%d'))
            except Exception as e:
                logger.warning(
                    f"Failed to parse product {i} on page {page_num}: {e}"
                )
                continue

driver.quit()

logger.info(f"Scraping complete. Collected {len(product_name_list)} products")

output_df = pd.DataFrame(
    list(
        zip(product_name_list,
            product_link_list,
            product_model_list,
            product_disc_cost_list,
            product_orig_cost_list,
            sold_out_list,
            ds_list
            )),
    columns=['item', 'url', 'artist', 'discount_price',
             'price', 'sold_out', 'ds']
)

output_file = 'jyp_shop_albums.csv'
output_df.to_csv(output_file, index=False)
logger.info(f"Data saved to {output_file}")
