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
product_discount_cost_list = []
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

    # Check for an empty page
    out_of_items = soup.find("div", class_="tt-empty-search")
    if(out_of_items == None):

        # Get Title and URL
        list_of_titles = soup.find_all("h2", class_="tt-title prod-thumb-title-color")
        for elem in list_of_titles:
            url_tag = elem.find("a")
            item_url = url_tag['href']
            item_name = elem.get_text(strip=True) 
            product_name_list.append(item_name)
            product_link_list.append("https://www.musicplaza.com" + item_url)

            product_sign_list.append(False)
            product_vendor_list.append('musicplaza')
            ds_list.append(datetime.now().strftime('%Y-%m-%d'))

        # Get Prices
        list_of_prices = soup.find_all("div", class_="tt-price")
        for elem in list_of_prices:
            item_price = elem.get_text(strip=True)
            num_price = re.findall( r'\d+\.*\d*', item_price)[0]
            product_cost_list.append(num_price)

        index += 1

        time.sleep(math.randint(1,5))

    else:
        not_an_empty_page = False


                
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


driver.quit()

main_list = [product_name_list, 
            product_link_list, 
            product_cost_list,
            product_discount_cost_list,
            product_sign_list,
            rating_list,
            no_of_q_list,
            no_of_reviews_list,
            product_vendor_list,
            product_sold_out_list,
            ds_list]

column_names= ['item',
                'url',
                'discount_price',
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
    output_df.to_csv('kpopalbums_whats_hot.csv',index=False)
else:
    print("ERROR: Mismatched Lengths in Final Lists")