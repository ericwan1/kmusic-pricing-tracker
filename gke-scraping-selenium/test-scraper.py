# Import Needed Packages for the driver
from selenium import webdriver

# Import libraries to authenticate to google cloud
from google.cloud import bigquery

# Imports for the scraper
from bs4 import  BeautifulSoup
import numpy as np
import pandas as pd
from datetime import datetime
import random
import re
import math
import time


driver = webdriver.Remote(
            command_executor='http://35.238.56.243:4444/wd/hub',
            options=webdriver.ChromeOptions()
)

# Functions used in the scraper script
def get_page_count(pg_count_url, element_tag, tag_content):
    data = driver.get(pg_count_url)
    time.sleep(3)
    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
    soup = BeautifulSoup(pg_html, 'lxml')
    items_count_str = soup.find(element_tag, tag_content).get_text(strip=True)
    items_count = int(items_count_str.split()[0])
    total_pages = math.ceil(items_count/12)
    return total_pages

def get_soup(pg_url, setting='lxml'):
    data = driver.get(pg_url)
    time.sleep(random.randint(4,8))
    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
    out_soup = BeautifulSoup(pg_html, setting)
    return out_soup

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

# Main Body of Scraper
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
                        avg_rating, no_of_q, no_of_reviews = None, None, None

                except:
                    avg_rating, no_of_q, no_of_reviews = None, None, None

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

main_list = [product_name_list, product_link_list, product_cost_list,
            product_discount_cost_list, product_sign_list,
            rating_list, no_of_q_list, no_of_reviews_list,
            product_vendor_list, product_sold_out_list, ds_list]

column_names= ['item', 'url', 'discount_price', 'price',
            'is_autograph', 'avg_review_value', 'number_of_questions',
            'number_of_reviews', 'vendor', 'is_sold_out', 'ds']

transposed_main_list = np.array(main_list).T.tolist()
lists_equal_len = False not in [len(i) == len(main_list[0]) for i in main_list]

if lists_equal_len:
    print("Success; Building Output")
    output_df = pd.DataFrame(transposed_main_list, columns=column_names)

    table_id = 'kprice-scraping.scrapeData.kpopalbums-docker-test'
    client = bigquery.Client()
    table = client.get_table(table_id)
    errors = client.insert_rows_from_dataframe(table, output_df)  
    if errors == []:
        print("Data uploaded to BQ For kpopalbums")
    else:
        print("Errors in uploading table for kpopalbums")
        print(errors)
else:
    print("ERROR: Mismatched Lengths in Final Lists")
