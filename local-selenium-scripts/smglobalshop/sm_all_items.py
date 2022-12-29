from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

import time
from bs4 import  BeautifulSoup
from datetime import datetime
import pandas as pd
import numpy as np

options = Options()
options.binary_location = "/Users/ericwan/Desktop/Google Chrome.app/Contents/MacOS/Google Chrome"
options.add_argument("start-maximized")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://smglobalshop.com/collections/all?usf_take=200")
count = 1
while True and count != 10:
    try:
        ActionChains(driver).move_to_element(WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="usf_container"]/div[2]/div[3]/div/button')))).pause(5).click().perform()
        print("LOAD MORE RESULTS button clicked")
        print("counter is: " + str(count))
        count += 1
        time.sleep(5)
    except TimeoutException as ex:
        print("No more LOAD MORE RESULTS button to be clicked")
        break

# Extract item information
pg_html = driver.page_source
pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
soup = BeautifulSoup(pg_html, 'lxml')

name_list = []
link_list = []
cost_list = []
autograph_list = []
vendor_list = []
so_list = []
ds_list = []

all_items = soup.find_all("div", class_="product-index desktop-3 tablet-2 mobile-half span-3")
for item in all_items:
    item_cost = item['data-price']
    url_title_so_info = item.find("div", class_="ci")
    item_link = "https://smglobalshop.com" + str(url_title_so_info.find("a")['href'])
    item_name = url_title_so_info.find("a")['title']
    try:
        so_status_text = url_title_so_info.find("div", class_="so icn")
        if so_status_text.get_text(strip=True) == "Sold out":
            so_status = True
        else:
            so_status = False
    except:
        so_status = False

    name_list.append(item_name)
    link_list.append(item_link)
    cost_list.append(item_cost)
    autograph_list.append(False)
    vendor_list.append("smglobalshop")
    so_list.append(so_status)
    ds_list.append(datetime.now().strftime('%Y-%m-%d'))

driver.quit()

main_list = [name_list,
            link_list,
            cost_list,
            autograph_list,
            vendor_list,
            so_list,
            ds_list]

column_names= ['item',
                'url',
                'price',
                'is_autograph',
                'vendor',
                'is_sold_out',
                'ds']

transposed_main_list = np.array(main_list).T.tolist()
lists_equal_len = False not in [len(i) == len(main_list[0]) for i in main_list]

if lists_equal_len:
    print("Success; Building Output")
    output_df = pd.DataFrame(transposed_main_list, columns=column_names)
    output_df.to_csv('smglobalshop_all.csv',index=False)
else:
    print("ERROR: Mismatched Lengths in Final Lists")