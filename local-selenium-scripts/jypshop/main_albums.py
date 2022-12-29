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

product_name_list = []
product_link_list = []
product_model_list = []
product_disc_cost_list = []
product_orig_cost_list = []
sold_out_list = []
ds_list = []

output_df = []

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
    total_item_count_text = soup.find('div', class_="prdcount").get_text(strip=True)
    total_items = int(re.findall( r'\d+\.*\d*', total_item_count_text)[0])
    total_pages = math.ceil(total_items/16)

    # Calculate items per page
    item_cnt_per_page = [1]*total_pages
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

        product_grid = soup.find('ul', class_='prdList grid4')
        all_prods_list = soup.find_all('li', class_="xans-record-")
        xans_cnt = len(all_prods_list)

        # Loop through album items
        for i in range(xans_cnt - total_pages - (item_cnt_per_page[page_num-1]*4), xans_cnt - total_pages, 4):
            prod = all_prods_list[i]

            product_description = prod.find('div', class_="description")
            product_model = product_description.find('div', class_="product_model").get_text(strip=True)
            product_name = product_description.find('div', class_="name").get_text(strip=True)
            product_href = product_description.find('div', class_="name").find('a')['href']

            orig_cost = 0.0
            disc_cost = 0.0

            # Identify if item is sold out or not
            if prod.find('li', {'rel':'Discounted Price'}) != None:
                discount_price_text = prod.find('li', {'rel':'Discounted Price'}).get_text(strip=True)
                discount_price = float(re.findall( r'\d+\.*\d*', discount_price_text)[0])
                disc_cost = discount_price
            if prod.find('li', {'rel':'Price'}) != None:
                price_text = prod.find('li', {'rel':'Price'}).get_text(strip=True)
                price = float(re.findall( r'\d+\.*\d*', price_text)[0])
                orig_cost = price

            # Identify if item is sold out or not
            if prod.find('div', class_="soldout_icon") == None:
                sold_out = False
            else:
                sold_out = True

            product_name_list.append(product_name)
            product_link_list.append(product_href)
            product_model_list.append(product_model)
            product_disc_cost_list.append(disc_cost)
            product_orig_cost_list.append(orig_cost)
            sold_out_list.append(sold_out)
            ds_list.append(datetime.now().strftime('%Y-%m-%d'))

driver.quit()

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
                columns=['item','url','artist','discount_price','price','sold_out','ds'])

output_df.to_csv('jyp_shop_albums.csv')