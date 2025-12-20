from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import random
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chrome path - configurable via environment variable for Docker
chrome_path = os.getenv(
    'CHROME_BINARY_PATH',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
)

options = Options()
if os.path.exists(chrome_path):
    options.binary_location = chrome_path
else:
    logger.warning(f"Chrome binary not found at {chrome_path}, "
                   "using system default")

options.add_argument("start-maximized")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')
options.add_argument('--no-sandbox')  # Required for Docker
options.add_argument('--disable-dev-shm-usage')  # Required for Docker

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)


"""
Use this function to retrieve a page
Inputs:
    - pg_url: the url (String)
    - setting: the setting for the returned soup - default is 'lxml' (String)
"""


def get_soup(pg_url, setting='lxml'):
    driver.get(pg_url)
    # Time given for the page to fully load
    time.sleep(random.randint(4, 8))
    pg_html = driver.page_source
    pg_html = pg_html.replace('&lt;', '<').replace('&gt;', '>')
    out_soup = BeautifulSoup(pg_html, setting)
    return out_soup
