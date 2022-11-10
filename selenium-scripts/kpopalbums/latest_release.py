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

from scraping_module import get_page_count
from scraping_module import get_soup

fail_count = 0
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

try:
    page_url = "https://www.kpopalbums.com/collections/lastest-release?page=1&view=ajax"
    pass_tag = "div"
    match_dict = {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}
    total_pages = get_page_count(page_url, pass_tag, match_dict)
    look_at_sites = True

except:
    print("ERROR: could not grab what's lastest-release count from kpopalbums.com")
    look_at_sites = False
    
if look_at_sites:
    for page_ind in range(1,total_pages+1):
        try:
            pg_count_url = f"https://www.kpopalbums.com/collections/lastest-release?page={page_ind}&view=ajax"
            soup = get_soup(pg_count_url)
            item_list = soup.find_all("div",{"class":"grid__item effect-hover item pg transition"})
            
            for item in item_list:
                # Title and URL Information
                title_url = item.find("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
                item_title = title_url['title']
                item_url = "https://www.kpopalbums.com" + str(title_url['href'])
      
                # Product Review Information
                try:
                    rating = item.find("div", class_="jdgm-prev-badge")
                    if rating != None:
                        avg_rating = rating['data-average-rating']
                        no_of_q = rating['data-number-of-questions']
                        no_of_reviews = rating['data-number-of-reviews']
                    else:
                        avg_rating = None
                        no_of_q = None
                        no_of_reviews = None
                except:
                    avg_rating = None
                    no_of_q = None
                    no_of_reviews = None

                # Pricing Information
                price = item.find("span", class_="product-price__price").get_text(strip=True)
                num_price = re.findall( r'\d+\.*\d*', price)[0]

                try:
                    disc_price = item.find("s", class_="product-price__price product-price__sale").get_text(strip=True)
                    if disc_price != None:
                        num_disc_price = re.findall( r'\d+\.*\d*', disc_price)[0]
                    else:
                        num_disc_price = None
                except:
                    num_disc_price = None

                # Sold Out Status
                try:
                    status = item.find("span", class_="product-price__sold-out")
                    if status == None:
                        soldout_status = False
                    else:
                        soldout_status = True
                except:
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

        except:
            print("ERROR: scraping lastest-release failed unexpectedly")
            print(f"index is {page_ind}")
            fail_count += 1
            if fail_count < 10:
                time.sleep(random.randint(30,60))
                continue
            else:
                break

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
    output_df.to_csv('kpopalbums_lastest_release.csv',index=False)
else:
    print("ERROR: Mismatched Lengths in Final Lists")