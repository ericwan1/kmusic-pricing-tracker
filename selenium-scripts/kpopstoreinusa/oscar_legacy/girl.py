from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


options = Options()
#options.binary_location = "/Users/ericwan/Desktop/Google Chrome.app/Contents/MacOS/Google Chrome"
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
import json
startTime = time.time()


fail_count = 0

dict_info = {}
cnt = 0
today = datetime.now().strftime('%Y-%m-%d')

try:
    pg_count_url = "https://www.kpopstoreinusa.com/collections/girl-group-album"
    data = driver.get(pg_count_url)
    #time.sleep(8)

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
        site = f"https://www.kpopstoreinusa.com/collections/girl-group-album?page={i}"
        data = driver.get(site)
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "shopify-section-halo-toolbar-mobile")))
        #time.sleep(8)

        pg_html = driver.page_source
        pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
        soup = BeautifulSoup(pg_html, 'lxml')

        items = soup.find('ul',{'id':'main-collection-product-grid'})
        items_list = items.find_all('li',{'class':'product'})

        for item in items_list:
            url = 'https://www.kpopstoreinusa.com' + item.find('a',{'class':'card-title link-underline card-title-ellipsis'})['href']
            data = item.find('div',{'class':'product-item'})
            js = json.loads(data['data-json-product'])
            info = js['variants'][0]
            dict_info[cnt] = [info['name'],info['price']/100,url,info['available'],'kpopstoreinusa',today,False]
            cnt+=1
        print((time.time() - startTime))
    except:
        print(f"ERROR: scraping {site} for product information failed unexpectedly")
        pass


output_df = pd.DataFrame.from_dict(dict_info, orient='index',columns=['item','price','url','availability','vendor','ds','presale'])
output_df.to_csv('kpopstoreinusa_girl.csv',encoding='utf-8-sig')
print((time.time() - startTime))