import base64
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import requests

def launch_scrape(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    table_id = ''
    client = bigquery.Client()
    table = client.get_table(table_id)
    
    page = requests.get("https://shop.mwave.me/en/cd.html")
    soup = BeautifulSoup(page.content, 'html.parser')

    list_of_items = soup.find_all("li", class_="product-item item product-item-one")

    product_name_list = []
    product_link_list = []
    product_cost_list = []
    product_sign_list = []
    product_vendor_list = []
    ds_list = []
    
    for elem in list_of_items:
        url_tag = elem.find("a")
        item_url = url_tag['href']
        product_link_list.append(item_url)

        item_price_box = elem.find("div", class_="price-box")
        item_price = item_price_box.find("span", class_="price").get_text(strip=True)
        if '$' in item_price:
            num_price = float(item_price.split("$")[1])
        else:
            num_price = item_price
        product_cost_list.append(num_price)

        item_name_tag = elem.find("strong")
        item_name = item_name_tag.get_text(strip=True)
        product_name_list.append(item_name)

        product_sign_list.append(True)
        product_vendor_list.append('mwave')
        ds_list.append(datetime.now().strftime('%Y-%m-%d'))
     
    output_df = pd.DataFrame(list(zip(product_name_list, 
                                        product_cost_list,
                                        product_link_list,
                                        product_sign_list,
                                        product_vendor_list,
                                        ds_list
                                        )),
                            columns=['item','price','url','is_autograph','vendor','ds'])

    errors = client.insert_rows_from_dataframe(table, output_df)  
    if errors == []:
        print("Data Loaded")
    else:
        print(errors)