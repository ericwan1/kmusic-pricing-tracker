# Notes

# The DAG will be built for just this file, as each file corresponds to a single site
# Due to this, we will not need to have multiple classes or parsing methods to be called in a separate file
# DAG structure will be an operator for each subsection of the kpopalbums.com website, of which there are 5

# Each operator will have a task, where each task will report how many items are contained in each subsection of the site
# The python method will check how many items there are on each subpage and then loop through the subsequent number of pages to retrieve the items
# Items will be scraped from the site using BeautifulSoup
# This decision was made in order to identify if a particular way of scraping a site breaks

# Scraped items will be stored in a table/dataframe/csv format

from bs4 import BeautifulSoup
import requests
import math

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pendulum

import pandas as pd
from time import sleep
from random import randint


default_args = {
    'owner': 'ew',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}


# Sample URLs
# kpopalbums_website_url_new_arrivals = f"https://www.kpopalbums.com/collections/lastest-release?page={page_num}&view=ajax"
# kpopalbums_website_url_pre_orders = f"https://www.kpopalbums.com/collections/pre-order?page={page_num}&view=ajax"
# kpopalbums_website_url_whats_hot = f"https://www.kpopalbums.com/collections/whats-hot?page={page_num}&view=ajax"
# kpopalbums_website_url_hot_deals = f"https://www.kpopalbums.com/collections/hot-deals?page={page_num}&view=ajax"
# kpopalbums_website_url_restock = f"https://www.kpopalbums.com/collections/restocked?page={page_num}&view=ajax"


product_name_list = []
product_link_list = []
product_cost_list = []


def scrape_new_arrivals():
    page = requests.get("https://www.kpopalbums.com/collections/lastest-release?page=1&view=ajax")
    soup = BeautifulSoup(page.content, 'html.parser')
    items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
    items_count = int(items_count_str.split()[0])

    # Go through all the available pages
    for i in range(1, math.ceil_(items_count/12) + 1):
        page = requests.get("https://www.kpopalbums.com/collections/lastest-release?page={i}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Retrieve the item names from each page
        all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
        for product in all_products_names:
            product_name = product.get_text(strip=True)
            product_hyperlink = product['href']

            product_name_list.append(product_name)
            product_link_list.append("https://www.kpopalbums.com/" + str(product_hyperlink))

        # Retrieve the item prices from each page
        all_products_prices = soup.find_all('div', class_='product-price')
        for product in all_products_prices:
            product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)

            product_cost_list.append(product_price)

        sleep(randint(1,5))


def scrape_pre_orders():
    page = requests.get("https://www.kpopalbums.com/collections/pre-order?page=1&view=ajax")
    soup = BeautifulSoup(page.content, 'html.parser')
    items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
    items_count = int(items_count_str.split()[0])

    # Go through all the available pages
    for i in range(1, math.ceil_(items_count/12) + 1):
        page = requests.get("https://www.kpopalbums.com/collections/pre-order?page={i}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Retrieve the item names from each page
        all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
        for product in all_products_names:
            product_name = product.get_text(strip=True)
            product_hyperlink = product['href']

            product_name_list.append(product_name)
            product_link_list.append("https://www.kpopalbums.com/" + str(product_hyperlink))

        # Retrieve the item prices from each page
        all_products_prices = soup.find_all('div', class_='product-price')
        for product in all_products_prices:
            product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)

            product_cost_list.append(product_price)

        sleep(randint(1,5))


def scrape_whats_hot():
    page = requests.get("https://www.kpopalbums.com/collections/whats-hot?page=1&view=ajax")
    soup = BeautifulSoup(page.content, 'html.parser')
    items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
    items_count = int(items_count_str.split()[0])

    # Go through all the available pages
    for i in range(1, math.ceil_(items_count/12) + 1):
        page = requests.get("https://www.kpopalbums.com/collections/whats-hot?page={i}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Retrieve the item names from each page
        all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
        for product in all_products_names:
            product_name = product.get_text(strip=True)
            product_hyperlink = product['href']

            product_name_list.append(product_name)
            product_link_list.append("https://www.kpopalbums.com/" + str(product_hyperlink))

        # Retrieve the item prices from each page
        all_products_prices = soup.find_all('div', class_='product-price')
        for product in all_products_prices:
            product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)

            product_cost_list.append(product_price)

        sleep(randint(1,5))


def scrape_hot_deals():
    page = requests.get("https://www.kpopalbums.com/collections/hot-deals?page=1&view=ajax")
    soup = BeautifulSoup(page.content, 'html.parser')
    items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
    items_count = int(items_count_str.split()[0])

    # Go through all the available pages
    for i in range(1, math.ceil_(items_count/12) + 1):
        page = requests.get("https://www.kpopalbums.com/collections/hot-deals?page={i}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Retrieve the item names from each page
        all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
        for product in all_products_names:
            product_name = product.get_text(strip=True)
            product_hyperlink = product['href']

            product_name_list.append(product_name)
            product_link_list.append("https://www.kpopalbums.com/" + str(product_hyperlink))

        # Retrieve the item prices from each page
        all_products_prices = soup.find_all('div', class_='product-price')
        for product in all_products_prices:
            product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)

            product_cost_list.append(product_price)

        sleep(randint(1,5))


def scrape_restocked():
    page = requests.get("https://www.kpopalbums.com/collections/restocked?page=1&view=ajax")
    soup = BeautifulSoup(page.content, 'html.parser')
    items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
    items_count = int(items_count_str.split()[0])

    # Go through all the available pages
    for i in range(1, math.ceil_(items_count/12) + 1):
        page = requests.get("https://www.kpopalbums.com/collections/restocked?page={i}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Retrieve the item names from each page
        all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
        for product in all_products_names:
            product_name = product.get_text(strip=True)
            product_hyperlink = product['href']

            product_name_list.append(product_name)
            product_link_list.append("https://www.kpopalbums.com/" + str(product_hyperlink))

        # Retrieve the item prices from each page
        all_products_prices = soup.find_all('div', class_='product-price')
        for product in all_products_prices:
            product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)

            product_cost_list.append(product_price)

        sleep(randint(1,5))


def assemble_table():
    output_df = pd.DataFrame(list(zip(product_name_list, product_link_list, product_cost_list)),
              columns=['product_name','product_link', 'product_price'])


with DAG(
    dag_id="scrape_kpopalbums",
    default_args=default_args,
    description="Scraping and saving results from kpopalbums.com",
    schedule_interval="0 */12 * * *",
    start_date=pendulum.datetime(2022, 10, 10, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=10)
) as dag:

    extract_new_arrivals = PythonOperator(
        task_id = 'extract_new_arrivals',
        python_callable=scrape_new_arrivals
    )

    extract_pre_orders = PythonOperator(
        task_id = 'extract_pre_orders',
        python_callable=scrape_pre_orders
    )

    extract_whats_hot = PythonOperator(
        task_id = 'extract_whats_hot',
        python_callable=scrape_whats_hot
    )

    extract_hot_deals = PythonOperator(
        task_id = 'extract_hot_deals',
        python_callable=scrape_hot_deals
    )

    extract_restocked = PythonOperator(
        task_id = 'extract_restocked',
        python_callable=scrape_restocked
    )

    extract_new_arrivals >> extract_pre_orders >> extract_whats_hot >> extract_hot_deals >> extract_restocked