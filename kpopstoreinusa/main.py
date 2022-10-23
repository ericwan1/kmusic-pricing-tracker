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

def scrape_autographed_albums():
    try:
        site= "https://www.kpopstoreinusa.com/collections/autographed-album"
        hdr = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}
        req = Request(site,headers=hdr)
        page = urlopen(req)
        soup = BeautifulSoup(page, 'lxml')

        # # Get total number of pages of merchandise:
        total_item_count_text = soup.find_all("div",class_="pagination-page-item pagination-page-total")[0].get_text(strip=True)
        total_item_count_text = total_item_count_text.split('of')[1]
        total_items = int(re.findall( r'\d+\.*\d*', total_item_count_text)[0])
    except:
        print(f"ERROR: scraping {site} for failed unexpectedly; unable to retrieve page or identify total number of items")
        pass

    try:
        # Default view is 20 items per page
        for i in range(math.ceil(total_items/20)):
            site = "https://www.kpopstoreinusa.com/collections/autographed-album?page={i}"
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

            sleep(randint(1,5))

    except:
        print(f"ERROR: scraping {site} for product information failed unexpectedly")
        pass


def scrape_preorder_albums():
    try:
        site= "https://www.kpopstoreinusa.com/collections/pre-order-album"
        hdr = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}
        req = Request(site,headers=hdr)
        page = urlopen(req)
        soup = BeautifulSoup(page, 'lxml')

        # # Get total number of pages of merchandise:
        total_item_count_text = soup.find_all("div",class_="pagination-page-item pagination-page-total")[0].get_text(strip=True)
        total_item_count_text = total_item_count_text.split('of')[1]
        total_items = int(re.findall( r'\d+\.*\d*', total_item_count_text)[0])
    except:
        print(f"ERROR: scraping {site} for failed unexpectedly; unable to retrieve page or identify total number of items")
        pass

    try:
        # Default view is 20 items per page
        for i in range(math.ceil(total_items/20)):
            site = "https://www.kpopstoreinusa.com/collections/pre-order-album?page={i}"
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
                product_sign_list.append(False)
                product_vendor_list.append('kpopstoreinusa')
                ds_list.append(datetime.now().strftime('%Y-%m-%d'))

            sleep(randint(1,5))

    except:
        print(f"ERROR: scraping {site} for product information failed unexpectedly")
        pass


def load_to_bigquery():
    output_df = pd.DataFrame(list(zip(product_name_list, 
                                        product_cost_list,
                                        product_link_list,
                                        product_sign_list,
                                        product_vendor_list,
                                        ds_list
                                        )),
                            columns=['item','price','url','is_autograph','vendor','ds'])
    table_id = 'kprice-scraping.scrapeData.kpopstoreinusa-data'
    client = bigquery.Client()
    table = client.get_table(table_id)
    errors = client.insert_rows_from_dataframe(table, output_df)  
    if errors == []:
        print("Data Loaded For kpopstoreinusa")
    else:
        print("Errors in scraping kpopstoreinusa")
        print(errors)


def start_scrape_kpopstoreinusa(event, context):
    scrape_autographed_albums()
    scrape_preorder_albums()
    load_to_bigquery()


# import base64
# from google.cloud import bigquery

# from bs4 import BeautifulSoup
# from urllib.request import Request, urlopen
# import pandas as pd
# from datetime import datetime

# from time import sleep
# from random import randint

# product_name_list = []
# product_link_list = []
# product_cost_list = []
# product_sign_list = []
# product_vendor_list = []
# ds_list = []

# output_df = []

# # We are making one request, so only minor time delays between each task in the DAG
# def scrape_autographed_albums():
#     try:
#         site= "https://kpopstoreinusa.com/shop/autographed-album/"
#         hdr = {'User-Agent': 'Mozilla/5.0'}
#         req = Request(site,headers=hdr)
#         page = urlopen(req)
#         soup = BeautifulSoup(page, 'lxml')
#     except:
#         print(f"ERROR: scraping {site} for failed unexpectedly")
#         pass

#     try:
#         # Get Title and Price
#         list_of_items = soup.find_all("div", class_="product-details-inner")

#         for elem in list_of_items:
#             url_tag = elem.find("a")
#             item_url = url_tag['href']
#             item_name = elem.find("div", class_="wpsp-product-title").get_text(strip=True)
#             item_price = elem.find("span", class_="woocommerce-Price-amount amount").get_text(strip=True)
#             if '$' in item_price:
#                 num_price = float(item_price.split("$")[1])
#             else:
#                 num_price = item_price
#             product_cost_list.append(num_price)
            
#             product_name_list.append(item_name)
#             product_link_list.append(item_url)
#             product_sign_list.append(True)
#             product_vendor_list.append('kpopstoreinusa')
#             ds_list.append(datetime.now().strftime('%Y-%m-%d'))
    
#     except:
#         print(f"ERROR: scraping {site} for failed unexpectedly")
#         pass

#     sleep(randint(1,5))


# def scrape_preorder_albums():
#     try:
#         site= "https://kpopstoreinusa.com/pre-order/albums/"
#         hdr = {'User-Agent': 'Mozilla/5.0'}
#         req = Request(site,headers=hdr)
#         page = urlopen(req)
#         soup = BeautifulSoup(page, 'lxml')
#     except:
#         print(f"ERROR: scraping {site} for failed unexpectedly")
#         pass

#     # Get Title and Price
#     try:
#         list_of_items = soup.find_all("div", class_="product-details-inner")

#         for elem in list_of_items:
#             url_tag = elem.find("a")
#             item_url = url_tag['href']
#             item_name = elem.find("div", class_="wpsp-product-title").get_text(strip=True)
#             item_price = elem.find("span", class_="woocommerce-Price-amount amount").get_text(strip=True)
#             if '$' in item_price:
#                 num_price = float(item_price.split("$")[1])
#             else:
#                 num_price = item_price
#             product_cost_list.append(num_price)
            
#             product_name_list.append(item_name)
#             product_link_list.append(item_url)
#             product_sign_list.append(False)
#             product_vendor_list.append('kpopstoreinusa')
#             ds_list.append(datetime.now().strftime('%Y-%m-%d'))

#     except:
#         print(f"ERROR: scraping {site} for failed unexpectedly")
#         pass

#     sleep(randint(1,5))


# def scrape_albums():
#     try:
#         site= "https://kpopstoreinusa.com/shop/albums/"
#         hdr = {'User-Agent': 'Mozilla/5.0'}
#         req = Request(site,headers=hdr)
#         page = urlopen(req)
#         soup = BeautifulSoup(page, 'html.parser')
#     except:
#         print('could not scrape {site}')
#         pass
    
#     # Grabbing the scrolling 'Featured Album' items
#     try:
#         scrolling_bar_items = soup.find("div", class_="carousel-slider-outer carousel-slider-outer-products carousel-slider-outer-449")
#         bar_items_url = scrolling_bar_items.find_all("a", class_="woocommerce-LoopProduct-link")
#         bar_items_name = scrolling_bar_items.find_all("h3")
#         bar_items_price = scrolling_bar_items.find_all("span", class_="woocommerce-Price-amount amount")
#         for elem in bar_items_url:
#             product_link_list.append(elem['href'])
#         for elem in bar_items_name:
#             product_name_list.append(elem.get_text(strip=True))
#         for elem in bar_items_price:
#             item_price = elem.get_text(strip=True)
#             if '$' in item_price:
#                 num_price = float(item_price.split("$")[1])
#             else:
#                 num_price = item_price
#             product_cost_list.append(num_price)
#         product_sign_list.append(False)
#         product_vendor_list.append('kpopstoreinusa')
#         ds_list.append(datetime.now().strftime('%Y-%m-%d'))

#     except:
#         print(f"ERROR: scraping {site} for carousel items failed unexpectedly")
#         pass

#     # Grabbing other items on the page
#     try:
#         list_of_items = soup.find("div", class_="wpsp-slider-section wpsp-slider-section28435 sp-woo-product-slider-pro28435 wpsp_theme_one pagination-type-dots navigation_position_top_right grid_style_even")
#         list_of_items = list_of_items.find_all("div", class_="product-details-inner")
#         for elem in list_of_items:
#             url_tag = elem.find("a")
#             item_url = url_tag['href']
#             item_name = elem.find("div", class_="wpsp-product-title").get_text(strip=True)
#             item_price = elem.find("span", class_="woocommerce-Price-amount amount").get_text(strip=True)
#             if '$' in item_price:
#                 num_price = float(item_price.split("$")[1])
#             else:
#                 num_price = item_price
#             product_cost_list.append(num_price)

#             product_name_list.append(item_name)
#             product_link_list.append(item_url)
#             product_sign_list.append(False)
#             product_vendor_list.append('kpopstoreinusa')
#             ds_list.append(datetime.now().strftime('%Y-%m-%d'))

#     except:
#         print(f"ERROR: scraping {site} for non carousel items failed unexpectedly")
#         pass

#     sleep(randint(1,5))


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


# def start_scrape_kpopstoreinusa(event, context):
#     scrape_autographed_albums()
#     scrape_preorder_albums()
#     scrape_albums()
#     load_to_bigquery()

