from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


options = Options()
options.binary_location = "/Users/ericwan/Desktop/Google Chrome.app/Contents/MacOS/Google Chrome"
options.add_argument("start-maximized")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# After getting the driver working
import time
from bs4 import  BeautifulSoup
import re
import math
from datetime import datetime
import pandas as pd
import random

fail_count = 0

product_name_list = []
product_link_list = []
product_cost_list = []
product_sign_list = []
product_vendor_list = []
ds_list = []

output_df = []

try:
    pg_count_url = "https://www.kpopalbums.com/collections/whats-hot?page=1&view=ajax"
    data = driver.get(pg_count_url)
    time.sleep(3)

    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')

    soup = BeautifulSoup(pg_html, 'lxml')
    items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
    items_count = int(items_count_str.split()[0])
    total_pages = math.ceil(items_count/12)

    # Good to proceed to interating and logging prices
    look_at_sites = True

except:
    look_at_sites = False
    print("ERROR: could not grab what's hot page count from kpopalbums.com")
    pass

if look_at_sites:
    for page_ind in range(total_pages,total_pages+1):
        try:
            pg_count_url = f"https://www.kpopalbums.com/collections/whats-hot?page={page_ind}&view=ajax"
            data = driver.get(pg_count_url)
            time.sleep(random.randint(4,8))

            pg_html = driver.page_source
            pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')

            soup = BeautifulSoup(pg_html, 'lxml')

            # Retrieve the item names from each page
            all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
            # Retrieve product prices
            all_products_prices = soup.find_all('div', class_='product-price')

            # Want to ensure a match in the stripped values; otherwise, this would ruin our dataframe creation 
            if len(all_products_names) == len(all_products_prices):
                for product in all_products_names:
                    product_name = product.get_text(strip=True)
                    product_hyperlink = product['href']

                    product_name_list.append(product_name)
                    product_link_list.append("https://www.kpopalbums.com" + str(product_hyperlink))

                    product_sign_list.append(False)
                    product_vendor_list.append('kpopalbums')
                    ds_list.append(datetime.now().strftime('%Y-%m-%d'))

                for product in all_products_prices:
                    product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)
                    num_price = re.findall( r'\d+\.*\d*', product_price)[0]
                    product_cost_list.append(num_price)

            else:
                print(f"ERROR: mismatched soup value lengths in {page_ind}; Try rerunning the link manually and verify output")

        except:
            print("ERROR: scraping what's hot failed unexpectedly")
            fail_count += 1
            if fail_count < 10:
                time.sleep(random.randint(30,60))
                continue
            else:
                break


driver.quit()

if len(product_name_list) == len(product_cost_list) == len(product_link_list) == len(product_sign_list) == len(product_vendor_list) == len(ds_list):
        output_df = pd.DataFrame(list(
                                    zip(product_name_list, 
                                        product_cost_list,
                                        product_link_list,
                                        product_sign_list,
                                        product_vendor_list,
                                        ds_list
                                        )
                                    ),
                                columns=['item','price','url','is_autograph','vendor','ds']
                                )

output_df.to_csv('kpopalbums_what_hot_last_page.csv')