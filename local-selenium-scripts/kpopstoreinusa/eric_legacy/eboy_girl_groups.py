from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


options = Options()
#options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
options.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"
options.add_argument("start-maximized")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# After getting the driver working
import time
from bs4 import BeautifulSoup
import re
import math
from datetime import datetime
import pandas as pd
import random
startTime = time.time()
fail_count = 0

product_name_list = []
product_link_list = []
product_cost_list = []
product_sign_list = []
product_vendor_list = []
ds_list = []

output_df = []


try:
    pg_count_url = "https://www.kpopstoreinusa.com/collections/boy-girl-group-album"
    data = driver.get(pg_count_url)
    time.sleep(8)

    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
    soup = BeautifulSoup(pg_html, 'lxml')
    
    # Get total number of pages of merchandise:
    total_item_count_text = soup.find_all("div",class_="pagination-page-item pagination-page-total")[0].get_text(strip=True)
    total_item_count_text = total_item_count_text.split('of')[1]
    total_items = int(re.findall( r'\d+\.*\d*', total_item_count_text)[0])
except:
    print(f"ERROR: scraping {pg_count_url} failed unexpectedly; unable to retrieve page or identify total number of items")
    pass


# Default view is 20 items per page
for i in range(1, math.ceil(total_items/20) + 1):
    try:
        site = f"https://www.kpopstoreinusa.com/collections/boy-girl-group-album?page={i}"
        data = driver.get(pg_count_url)
        time.sleep(3)

        pg_html = driver.page_source
        pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
        soup = BeautifulSoup(pg_html, 'lxml')

        items = soup.find('ul',{'id':'main-collection-product-grid'})
        items_list = items.find_all('li',{'class':'product'})

        for item in items_list:
            main_info=item.find('a',{'class':'card-title link-underline card-title-ellipsis'})
            cost_info=item.find('div',{'class':'price__regular'}).get_text(strip=True)
            cost = re.findall( r'\d+\.*\d*', cost_info)[0]
            availability_info = item.find('div',{'class':'product-item'})
            a = availability_info['data-json-product']

            # Add information for item
            product_name_list.append(main_info["data-product-title"])
            item_url = 'https://www.kpopstoreinusa.com' + main_info["href"]
            product_link_list.append(item_url)
            product_cost_list.append(cost)
            product_sign_list.append(False)
            product_vendor_list.append('kpopstoreinusa')
            ds_list.append(datetime.now().strftime('%Y-%m-%d'))
        print((time.time() - startTime))
    except:
        print(f"ERROR: scraping {site} for product information failed unexpectedly")
        fail_count += 1
        if fail_count < 10:
            time.sleep(random.randint(30,60))
            continue
        else:
            break


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

output_df.to_csv('ekpopstoreinusa_boy_girl.csv',encoding='utf-8-sig')
print((time.time() - startTime))