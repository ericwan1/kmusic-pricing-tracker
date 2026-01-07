"""
JYP Shop Scraper - Handles both albums and all merchandise.
"""

import argparse
import sys
import time
import re
import math
import platform
from datetime import datetime
from typing import Optional
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd

# Import common utilities
from pipeline.common import (
    schema,
    storage,
    logging as pipeline_logging,
    validation
)


def setup_driver() -> webdriver.Chrome:
    """Set up and return Chrome WebDriver."""

    chrome_path = os.getenv(
        'CHROME_BINARY_PATH',
        '/usr/bin/google-chrome'
    )

    options = Options()
    if os.path.exists(chrome_path):
        options.binary_location = chrome_path
    else:
        # Try chromium as fallback (for ARM64)
        chromium_path = '/usr/bin/chromium'
        if os.path.exists(chromium_path):
            options.binary_location = chromium_path
            chrome_path = chromium_path

    options.add_argument("start-maximized")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')

    # Detect architecture
    arch = platform.machine().lower()
    is_arm64 = arch in ('arm64', 'aarch64')

    # Set up ChromeDriver service
    service = None
    if is_arm64:
        # For ARM64, try system chromedriver first
        system_chromedriver_paths = [
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver'
        ]
        system_chromedriver = None
        for path in system_chromedriver_paths:
            if os.path.exists(path):
                system_chromedriver = path
                break

        if system_chromedriver:
            msg = f"ARM64: Using system chromedriver at {system_chromedriver}"
            print(msg)
            service = Service(system_chromedriver)
        else:
            msg = (
                "ARM64: No system chromedriver found. "
                "webdriver-manager may download wrong architecture. "
                "Consider building for AMD64 platform: "
                "docker build --platform linux/amd64 ..."
            )
            print(msg)
            # Try webdriver-manager anyway (will likely fail)
            service = Service(ChromeDriverManager().install())
    else:
        # AMD64 - webdriver-manager should work
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def extract_product_data(
    prod, index: int, page_num: int, url: str
) -> Optional[dict]:
    """
    Extract product data handling both old and new HTML structures.
    Returns dict with product data or None if extraction fails.
    """
    # Try to find description div - handle both structures
    box = prod.find('div', class_="box")
    if box:
        product_description = box.find('div', class_="description")
    else:
        product_description = prod.find('div', class_="description")

    if product_description is None:
        return None

    # Extract product model (artist name)
    product_model_elem = product_description.find(
        'div', class_="product_model"
    )
    product_model = (
        product_model_elem.get_text(strip=True)
        if product_model_elem else None
    )

    # Extract product name
    name_elem = (
        product_description.find('div', class_="name") or
        product_description.find('strong', class_="name")
    )
    if name_elem is None:
        return None

    name_link = name_elem.find('a')
    if name_link is None:
        return None

    product_name = name_link.get_text(strip=True)
    product_href = name_link.get('href', '')

    # Fix URL if needed
    if product_href and not product_href.startswith('http'):
        if product_href.startswith('/'):
            product_href = f"https://en.thejypshop.com{product_href}"
        else:
            product_href = f"https://en.thejypshop.com/{product_href}"

    # Extract prices
    orig_cost = None
    disc_cost = None

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

    # Use discount price as price if original price not found
    if orig_cost is None and disc_cost is not None:
        orig_cost = disc_cost
        disc_cost = None  # No discount if we're using it as main price

    # Check if sold out
    sold_out = (
        prod.find('div', class_="soldout_icon") is not None or
        (product_description and
         product_description.find('div', class_="soldout_icon") is not None)
    )

    return {
        'name': product_name,
        'href': product_href,
        'artist': product_model,
        'disc_price': disc_cost,
        'orig_price': orig_cost,
        'sold_out': sold_out
    }


def scrape_jypshop_albums(
    driver: webdriver.Chrome,
    urls: list[str],
    logger,
    step_size: int = 4
) -> pd.DataFrame:
    """
    Scrape JYP Shop products from given URLs.

    Args:
        driver: Selenium WebDriver instance
        urls: List of URLs to scrape
        logger: Logger instance
        step_size: Step size for iterating products (4 for albums, 3 for merch)

    Returns:
        DataFrame with scraped data
    """
    product_name_list = []
    product_link_list = []
    product_artist_list = []
    product_disc_cost_list = []
    product_orig_cost_list = []
    sold_out_list = []
    ds_list = []

    ds = datetime.now().strftime('%Y-%m-%d')

    for url in urls:
        logger.info(f"Processing URL: {url}")
        driver.get(url)
        time.sleep(3)

        pg_html = driver.page_source
        pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
        soup = BeautifulSoup(pg_html, 'lxml')

        try:
            prdcount_elem = soup.find('div', class_="prdcount")
            if prdcount_elem is None:
                raise AttributeError("prdcount element not found")
            total_item_count_text = prdcount_elem.get_text(strip=True)
            price_matches = re.findall(r'\d+\.*\d*', total_item_count_text)
            total_items = int(price_matches[0])
            total_pages = math.ceil(total_items / 16)
            msg = f"Found {total_items} items across {total_pages} pages"
            logger.info(msg)
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
                driver.get(new_site)
                time.sleep(3)
                pg_html = driver.page_source
                pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
                soup = BeautifulSoup(pg_html, 'lxml')

            all_prods_list = soup.find_all('li', class_="xans-record-")
            xans_cnt = len(all_prods_list)
            logger.info(f"Page {page_num}: Found {xans_cnt} product elements")

            # Loop through items (step size varies: 4 for albums, 3 for merch)
            start_idx = (
                xans_cnt - total_pages -
                (item_cnt_per_page[page_num - 1] * step_size)
            )
            end_idx = xans_cnt - total_pages
            for i in range(start_idx, end_idx, step_size):
                try:
                    prod = all_prods_list[i]
                    product_data = extract_product_data(prod, i, page_num, url)
                    if product_data:
                        product_name_list.append(product_data['name'])
                        product_link_list.append(product_data['href'])
                        product_artist_list.append(product_data['artist'])
                        product_disc_cost_list.append(
                            product_data['disc_price']
                        )
                        product_orig_cost_list.append(
                            product_data['orig_price']
                        )
                        sold_out_list.append(product_data['sold_out'])
                        ds_list.append(ds)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse product {i} on page {page_num}: {e}"
                    )
                    continue

    # Create DataFrame matching fixed schema
    df = pd.DataFrame({
        'item': product_name_list,
        'url': product_link_list,
        'artist': product_artist_list,
        'discount_price': product_disc_cost_list,
        'price': product_orig_cost_list,
        'sold_out': sold_out_list,
        'ds': ds_list
    })

    # Ensure columns are in correct order
    df = df[schema.SCHEMA_COLUMNS]

    return df


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scrape JYP Shop (albums and/or merchandise)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help=('Start date (YYYY-MM-DD) for backfill '
              '(not used for this scraper)')
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help=('End date (YYYY-MM-DD) for backfill '
              '(not used for this scraper)')
    )
    parser.add_argument(
        '--vendor',
        type=str,
        default='jypshop',
        help='Vendor identifier'
    )
    parser.add_argument(
        '--type',
        type=str,
        choices=['albums', 'merch', 'all'],
        default='all',
        help='What to scrape: albums, merch, or all (default: all)'
    )
    args = parser.parse_args()

    # Set up logging
    logger = pipeline_logging.setup_logging('jypshop-scraper')
    start_time = time.time()
    ds = datetime.now().strftime('%Y-%m-%d')

    pipeline_logging.log_run_start(
        logger,
        vendor=args.vendor,
        start_date=args.start_date,
        end_date=args.end_date
    )

    driver = None
    try:
        # Set up driver
        driver = setup_driver()

        # URLs to scrape based on type
        album_urls = [
            'https://en.thejypshop.com/category/cdlp/56/',
            'https://en.thejypshop.com/category/cdlp/62/',
            'https://en.thejypshop.com/category/cdlp/68/',
            'https://en.thejypshop.com/category/cdlp/36/',
            'https://en.thejypshop.com/category/cdlp/93/',
            'https://en.thejypshop.com/category/cdlp/52/',
            'https://en.thejypshop.com/category/cdlp/59/',
            'https://en.thejypshop.com/category/cdlp/421/',
            'https://en.thejypshop.com/category/cdlp/444/',
            'https://en.thejypshop.com/category/cdlp/449/',
            'https://en.thejypshop.com/category/cdlp/463/'
        ]

        merch_urls = [
            'https://en.thejypshop.com/category/all/293/',
            'https://en.thejypshop.com/category/all/241/',
            'https://en.thejypshop.com/category/all/207/',
            'https://en.thejypshop.com/category/all/167/',
            'https://en.thejypshop.com/category/all/260/',
            'https://en.thejypshop.com/category/all/254/',
            'https://en.thejypshop.com/category/cheerings/289/',  # twice
            'https://en.thejypshop.com/category/cheerings/88/',  # 2pm
            'https://en.thejypshop.com/category/cheerings/89/',  # day6
            'https://en.thejypshop.com/category/cheerings/251/',  # sk
            'https://en.thejypshop.com/category/cheerings/238/',  # itzy
            'https://en.thejypshop.com/category/cheerings/94/',  # nmixx
            'https://en.thejypshop.com/category/cheerings/460/',  # jh
            'https://en.thejypshop.com/category/cheerings/53/',  # 2pm dvd
            'https://en.thejypshop.com/category/cheerings/57/',  # twice dvd
            'https://en.thejypshop.com/category/cheerings/60/'  # sk dvd
        ]

        # Determine what to scrape
        dfs = []
        if args.type in ('albums', 'all'):
            logger.info("Scraping albums...")
            df_albums = scrape_jypshop_albums(
                driver, album_urls, logger, step_size=4
            )
            dfs.append(df_albums)

        if args.type in ('merch', 'all'):
            logger.info("Scraping merchandise...")
            df_merch = scrape_jypshop_albums(
                driver, merch_urls, logger, step_size=3
            )
            dfs.append(df_merch)

        # Combine all dataframes
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
        else:
            df = pd.DataFrame()

        if df.empty:
            logger.error("No data scraped")
            sys.exit(1)

        logger.info(f"Scraped {len(df)} products")

        # Normalize types
        df = schema.normalize_types(df)

        # Validate schema
        is_valid, schema_errors = schema.validate_schema(df)
        if not is_valid:
            pipeline_logging.log_validation_error(
                logger, args.vendor, schema_errors
            )
            sys.exit(2)

        # Data quality checks
        is_valid, quality_errors = validation.validate_data_quality(
            df,
            expected_ds=ds,
            min_rows=1
        )
        if not is_valid:
            pipeline_logging.log_validation_error(
                logger, args.vendor, quality_errors
            )
            sys.exit(2)

        # Upload to GCS
        try:
            gcs_path = storage.upload_raw_data(
                df,
                vendor=args.vendor,
                ds=ds,
                check_exists=True
            )
            logger.info(f"Uploaded to {gcs_path}")
        except Exception as e:
            logger.error(f"Failed to upload to GCS: {e}", exc_info=True)
            sys.exit(3)

        # Log completion
        duration = time.time() - start_time
        pipeline_logging.log_run_complete(
            logger,
            vendor=args.vendor,
            row_count=len(df),
            duration_seconds=duration,
            gcs_path=gcs_path
        )

        sys.exit(0)

    except Exception as e:
        duration = time.time() - start_time
        pipeline_logging.log_run_error(logger, args.vendor, e, duration)
        sys.exit(1)

    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    main()
