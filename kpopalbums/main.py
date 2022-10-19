# Notes

# The DAG will be built for just this file, as each file corresponds to a single site
# Due to this, we will not need to have multiple classes or parsing methods to be called in a separate file
# DAG structure will be an operator for each subsection of the kpopalbums.com website, of which there are 5

# Each operator will have a task, where each task will report how many items are contained in each subsection of the site
# The python method will check how many items there are on each subpage and then loop through the subsequent number of pages to retrieve the items
# Items will be scraped from the site using BeautifulSoup
# This decision was made in order to identify if a particular way of scraping a site breaks

# Scraped items will be stored in a table/dataframe/csv format

from google.cloud import bigquery
from bs4 import BeautifulSoup
import requests
import math
from datetime import datetime
import pandas as pd
from time import sleep
from random import randint
import re


# Sample URLs
# kpopalbums_website_url_new_arrivals = f"https://www.kpopalbums.com/collections/lastest-release?page={page_num}&view=ajax"
# kpopalbums_website_url_pre_orders = f"https://www.kpopalbums.com/collections/pre-order?page={page_num}&view=ajax"
# kpopalbums_website_url_whats_hot = f"https://www.kpopalbums.com/collections/whats-hot?page={page_num}&view=ajax"
# kpopalbums_website_url_hot_deals = f"https://www.kpopalbums.com/collections/hot-deals?page={page_num}&view=ajax"
# kpopalbums_website_url_restock = f"https://www.kpopalbums.com/collections/restocked?page={page_num}&view=ajax"


product_name_list = []
product_link_list = []
product_cost_list = []
product_sign_list = []
product_vendor_list = []
ds_list = []

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}

def scrape_new_arrivals():
    look_at_sites = True
    try:
        page = requests.get("https://www.kpopalbums.com/collections/lastest-release?page=1&view=ajax",headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
        items_count = int(items_count_str.split()[0])
    except:
        look_at_sites = False
        print("ERROR: could not grab latest releases from kpopalbums.com")
        pass

    if look_at_sites:
        # Go through all the available pages
        for i in range(1, math.ceil(items_count/12)):
            try:
                page = requests.get("https://www.kpopalbums.com/collections/lastest-release?page={i}&view=ajax",headers=headers)
                soup = BeautifulSoup(page.content, 'html.parser')

                # Retrieve the item names from each page
                all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
                for product in all_products_names:
                    product_name = product.get_text(strip=True)
                    product_hyperlink = product['href']

                    product_name_list.append(product_name)
                    product_link_list.append("https://www.kpopalbums.com" + str(product_hyperlink))

                    product_sign_list.append(False)
                    product_vendor_list.append('kpopalbums')
                    ds_list.append(datetime.now().strftime('%Y-%m-%d'))

                # Retrieve the item prices from each page
                all_products_prices = soup.find_all('div', class_='product-price')
                for product in all_products_prices:
                    product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)
                    num_price = re.findall( r'\d+\.*\d*', product_price)[0]
                    product_cost_list.append(num_price)

                sleep(randint(1,3))

            except:
                print("ERROR: scraping latest releases failed unexpectedly")
                sleep(randint(20,30))
                break



def scrape_pre_orders():
    look_at_sites = True
    try:
        page = requests.get("https://www.kpopalbums.com/collections/pre-order?page=1&view=ajax",headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        items_count_str = soup.find("div", {"class":"ct__total col-xs-12 col-sm-3 gutter-ele-bottom-tbs text-uppercase fw-bold"}).get_text(strip=True)
        items_count = int(items_count_str.split()[0])
    except:
        look_at_sites = False
        print("ERROR: could not grab preorders from kpopalbums.com")
        pass

    if look_at_sites:
        # Go through all the available pages
        for i in range(1, math.ceil(items_count/12)):
            try:
                page = requests.get("https://www.kpopalbums.com/collections/pre-order?page={i}&view=ajax",headers=headers)
                soup = BeautifulSoup(page.content, 'html.parser')

                # Retrieve the item names from each page
                all_products_names = soup.find_all("a", class_="item__name pg__sync-url pg__name pg__name--list hide")
                for product in all_products_names:
                    product_name = product.get_text(strip=True)
                    product_hyperlink = product['href']

                    product_name_list.append(product_name)
                    product_link_list.append("https://www.kpopalbums.com" + str(product_hyperlink))

                    product_sign_list.append(False)
                    product_vendor_list.append('kpopalbums')
                    ds_list.append(datetime.now().strftime('%Y-%m-%d'))

                # Retrieve the item prices from each page
                all_products_prices = soup.find_all('div', class_='product-price')
                for product in all_products_prices:
                    product_price = product.find("span", {"class":"product-price__price"}).get_text(strip=True)
                    num_price = re.findall( r'\d+\.*\d*', product_price)[0]
                    product_cost_list.append(num_price)

                sleep(randint(1,3))

            except:
                print("ERROR: scraping preorders failed unexpectedly")
                sleep(randint(20,30))
                break


def load_to_bigquery():
    if len(product_name_list) == len(product_cost_list) == len(product_link_list) == len(product_sign_list) == len(product_vendor_list) == len(ds_list):
        output_df = pd.DataFrame(list(zip(product_name_list, 
                                            product_cost_list,
                                            product_link_list,
                                            product_sign_list,
                                            product_vendor_list,
                                            ds_list
                                            )),
                                columns=['item','price','url','is_autograph','vendor','ds'])
        table_id = 'kprice-scraping.scrapeData.kpopalbums-data'
        client = bigquery.Client()
        table = client.get_table(table_id)
        errors = client.insert_rows_from_dataframe(table, output_df)  
        if errors == []:
            print("Data Loaded For kpopalbums")
        else:
            print("Errors in uploading table for kpopalbums")
            print(errors)
    else:
        print("mismatched lengths in final lists; table was not constructed")
        print("length of name list: " + len(product_name_list))
        print("length of cost list: " + len(product_cost_list))


def start_scrape_kpopalbums(event, context):
    scrape_new_arrivals()
    print("done scraping new arrivals")
    scrape_pre_orders()
    print("done scraping pre orders")
    load_to_bigquery()
    print("done uploading data to bigquery")