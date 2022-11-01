import base64
from google.cloud import bigquery

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import pandas as pd
from datetime import datetime
import re
import math

from time import sleep
from random import randint

product_name_list = []
product_link_list = []
product_cost_list = []
product_sign_list = []
product_vendor_list = []
ds_list = []

output_df = []

def scrape_boys():
    try:
        site= "https://www.kpopstoreinusa.com/collections/girl-group-album"
        hdr = {'User-Agent': 'adsbot-google',
            'Referer': 'https://google.com',
            }
        req = Request(site,headers=hdr)
        page = urlopen(req)
        soup = BeautifulSoup(page, 'lxml')

        # # Get total number of pages of merchandise:
        total_item_count_text = soup.find_all("div",class_="pagination-page-item pagination-page-total")[0].get_text(strip=True)
        total_item_count_text = total_item_count_text.split('of')[1]
        total_items = re.findall( r'\d+\.*\d*', total_item_count_text)[0]

    except:
        print(f"ERROR: scraping {site} for failed unexpectedly; unable to retrieve page or identify total number of items")
        pass

    try:
        # Default view is 20 items per page
        for i in range(1, math.ceil(int(total_items)/20) + 1):
            print(i)

            site = f"https://www.kpopstoreinusa.com/collections/girl-group-album?page={i}"
            hdr = {'User-Agent': 'Pinterest'}
            req = Request(site,headers=hdr)
            page = urlopen(req)
            soup = BeautifulSoup(page, 'lxml')

            items = soup.find('ul',{'id':'main-collection-product-grid'})
            items_list = items.find_all('li',{'class':'product'})

            for item in items_list:
                main_info=item.find('a',{'class':'card-title link-underline card-title-ellipsis'})
                cost_info=item.find('div',{'class':'price__regular'}).get_text(strip=True)
                cost = re.findall( r'\d+\.*\d*', cost_info)[0]

                # Add information for item
                product_name_list.append(main_info["data-product-title"])
                item_url = 'https://www.kpopstoreinusa.com' + main_info["href"]
                product_link_list.append(item_url)
                product_cost_list.append(cost)
                product_sign_list.append(True)
                product_vendor_list.append('kpopstoreinusa')
                ds_list.append(datetime.now().strftime('%Y-%m-%d'))

                print(main_info["data-product-title"])

            sleep(randint(15,16))

    except:
        print(f"ERROR: scraping {site} for product information failed unexpectedly")
        pass


# def load_to_bigquery():
#     output_df = pd.DataFrame(list(zip(product_name_list, 
#                                         product_cost_list,
#                                         product_link_list,
#                                         product_sign_list,
#                                         product_vendor_list,
#                                         ds_list
#                                         )),
#                             columns=['item','price','url','is_autograph','vendor','ds'])
#     table_id = 'kprice-scraping.scrapeData.kpopstoreinusa-data'
#     client = bigquery.Client()
#     table = client.get_table(table_id)
#     errors = client.insert_rows_from_dataframe(table, output_df)  
#     if errors == []:
#         print("Data Loaded For kpopstoreinusa")
#     else:
#         print("Errors in scraping kpopstoreinusa")
#         print(errors)


def start_scrape_kpopstoreinusa(event, context):
    scrape_boys()
    # load_to_bigquery()

start_scrape_kpopstoreinusa('bah','blah')