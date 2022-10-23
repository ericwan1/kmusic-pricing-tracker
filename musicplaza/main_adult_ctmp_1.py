from google.cloud import bigquery
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
from time import sleep
from random import randint
import re


product_name_list = []
product_link_list = []
product_cost_list = []
product_sign_list = []
product_vendor_list = []
ds_list = []

headers = {'User-Agent': 'adsbot-google'}

def scrape_adult_contemporary():
    # We continue scraping until we come across an element that indicates an empty page
    index = 1
    not_an_empty_page = True
    while(not_an_empty_page and index < 30):
        print(index)
        page = requests.get("https://www.musicplaza.com/collections/adult-contemporary?page={index}&view=ajax", headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Check for an empty page
        out_of_items = soup.find("div", class_="tt-empty-search")
        if out_of_items != None:
            not_an_empty_page = False

        else:
            # Get Title and URL
            list_of_titles = soup.find_all("h2", class_="tt-title prod-thumb-title-color")
            for elem in list_of_titles:
                url_tag = elem.find("a")
                item_url = url_tag['href']
                item_name = elem.get_text(strip=True) 
                print(item_name)
                product_name_list.append(item_name)
                product_link_list.append("https://www.musicplaza.com" + item_url)

                product_sign_list.append(False)
                product_vendor_list.append('musicplaza')
                ds_list.append(datetime.now().strftime('%Y-%m-%d'))

            # Get Prices
            list_of_prices = soup.find_all("div", class_="tt-price")
            for elem in list_of_prices:
                item_price = elem.get_text(strip=True)
                product_cost_list.append(item_price)
                num_price = re.findall( r'\d+\.*\d*', item_price)[0]
                product_cost_list.append(num_price)

            index += 1

            sleep(randint(2,5))


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
        table_id = 'kprice-scraping.scrapeData.musicplaza-data'
        client = bigquery.Client()
        table = client.get_table(table_id)
        errors = client.insert_rows_from_dataframe(table, output_df)  
        if errors == []:
            print("Data Loaded For musicplaza")
        else:
            print("Errors in uploading table for musicplaza")
            print(errors)
    else:
        print("mismatched lengths in final lists; table was not constructed")
        print("length of name list: " + len(product_name_list))
        print("length of cost list: " + len(product_cost_list))


def start_scrape_musicplaza(event, context):
    scrape_adult_contemporary()
    print("done scraping adult contemporary")
    load_to_bigquery()
    print("done uploading data to bigquery")
    print(product_cost_list)

start_scrape_musicplaza("blah", "blah")