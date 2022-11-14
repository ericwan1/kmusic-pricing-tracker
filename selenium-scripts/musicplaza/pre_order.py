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
from datetime import datetime
import pandas as pd
import random
import numpy as np
import math

from scraping_module import get_soup

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

output_df = []

# We continue scraping until we come across an element that indicates an empty page
index = 1
not_an_empty_page = True
while(not_an_empty_page and index < 15):
    pg_count_url = f"https://www.musicplaza.com/collections/pre-order?page={index}&view=ajax"
    soup = get_soup(pg_count_url)
    time.sleep(3)
    # Check for an empty page
    out_of_items = soup.find("div", class_="tt-empty-search")
    if(out_of_items == None):
        # Get Product HTML Block
        item_list = soup.find_all("div", class_="col-6 col-md-3 tt-col-item")
        for item in item_list:
            # Title & URL Info
            t_url_info = item.find("h2", class_="tt-title prod-thumb-title-color")
            url_tag = t_url_info.find("a")
            item_title = t_url_info.get_text(strip=True)
            item_url = "https://www.musicplaza.com" + str(url_tag['href'])

            # Price Information
            price_info = item.find("div", class_="tt-price")
            item_price = price_info.get_text(strip=True)
            num_price = re.findall( r'\d+\.*\d*', item_price)[0]

            # Sold Out Status
            try:
                so_tag = item.find("span", class_="tt-label-our-stock")
                so_status = True
            except:
                so_status = False

            # Review Information
            try:
                review_tag = item.find("div", class_="jdgm-prev-badge")
                item_avg_rating = review_tag['data-average-rating']
                item_no_of_q = review_tag['data-number-of-questions']
                item_no_of_r = review_tag['data-number-of-reviews']
            except:
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

        index += 1

    else:
        not_an_empty_page = False

driver.quit()

main_list = [product_name_list, 
            product_link_list, 
            product_cost_list,
            product_sign_list,
            rating_list,
            no_of_q_list,
            no_of_reviews_list,
            product_vendor_list,
            product_sold_out_list,
            ds_list]

column_names= ['item',
                'url',
                'price',
                'is_autograph',
                'avg_review_value',
                'number_of_questions',
                'number_of_reviews',
                'vendor',
                'is_sold_out',
                'ds']

transposed_main_list = np.array(main_list).T.tolist()
lists_equal_len = False not in [len(i) == len(main_list[0]) for i in main_list]

if lists_equal_len:
    print("Success; Building Output")
    output_df = pd.DataFrame(transposed_main_list, columns=column_names)
    output_df.to_csv('musicplaza_pre_order.csv',index=False)
else:
    print("ERROR: Mismatched Lengths in Final Lists")