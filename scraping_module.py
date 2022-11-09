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
# Use this function to receive number of pages & total elements
# Inputs: 
# URL (String)
# HTML Pattern Match (String)
def get_page_count(pg_count_url, element_tag, tag_content):
    data = driver.get(pg_count_url)
    time.sleep(3)

    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')

    soup = BeautifulSoup(pg_html, 'lxml')
    items_count_str = soup.find(element_tag, tag_content).get_text(strip=True)
    items_count = int(items_count_str.split()[0])
    total_pages = math.ceil(items_count/12)
    print(total_pages)

url = "https://www.kpopalbums.com/collections/lastest-release?page=1&view=ajax"
elem_tag = "div"
matcher = {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}

driver.quit()

get_page_count(url, elem_tag, matcher)