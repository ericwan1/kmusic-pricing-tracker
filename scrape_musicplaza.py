# # Notes

# # The DAG will be built for just this file, as each file corresponds to a single site
# # Due to this, we will not need to have multiple classes or parsing methods to be called in a separate file
# # DAG structure will be an operator for each subsection of the musicplaza.com website, of which there are 5

# # Each operator will have a task, where each task will report how many items are contained in each subsection of the site
# # The python method will check how many items there are on each subpage and then loop through the subsequent number of pages to retrieve the items
# # Items will be scraped from the site using BeautifulSoup
# # This decision was made in order to identify if a particular way of scraping a site breaks

# # Scraped items will be stored in a table/dataframe/csv format

from xml.dom.minidom import Element
from bs4 import BeautifulSoup
import requests

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pendulum

import pandas as pd
import time


default_args = {
    'owner': 'ew',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

# Example websites
# https://www.musicplaza.com/collections/new-releases?page=1&view=ajax
# https://www.musicplaza.com/collections/pre-order?page=1&view=ajax
# https://www.musicplaza.com/collections/k-pop?page=1&view=ajax
# https://www.musicplaza.com/collections/adult-contemporary?page=1&view=ajax


product_name_list = []
product_link_list = []
product_cost_list = []


def scrape_new_releases():
    # We continue scraping until we come across an element that indicates an empty page
    index = 1
    not_an_empty_page = True
    while(index > 0 and not_an_empty_page):
        page = requests.get("https://www.musicplaza.com/collections/new-releases?page={index}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Check for an empty page
        out_of_items = soup.find("div", class_="tt-empty-search")
        if(out_of_items == None):
    
            # Get Title and URL
            list_of_titles = soup.find_all("h2", class_="tt-title prod-thumb-title-color")
            for elem in list_of_titles:
                url_tag = elem.find("a")
                item_url = url_tag['href']
                item_name = elem.get_text(strip=True) 
                product_name_list.append(item_name)
                product_link_list.append(item_url)

            # Get Prices
            list_of_prices = soup.find_all("div", class_="tt-price")
            for elem in list_of_prices:
                item_price = elem.get_text(strip=True)
                product_cost_list.append(item_price)

            index += 1

        else:
            not_an_empty_page = False


def scrape_pre_order():
    # We continue scraping until we come across an element that indicates an empty page
    index = 1
    not_an_empty_page = True
    while(index > 0 and not_an_empty_page):
        page = requests.get("https://www.musicplaza.com/collections/pre-order?page={index}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Check for an empty page
        out_of_items = soup.find("div", class_="tt-empty-search")
        if(out_of_items == None):
    
            # Get Title and URL
            list_of_titles = soup.find_all("h2", class_="tt-title prod-thumb-title-color")
            for elem in list_of_titles:
                url_tag = elem.find("a")
                item_url = url_tag['href']
                item_name = elem.get_text(strip=True) 
                product_name_list.append(item_name)
                product_link_list.append(item_url)

            # Get Prices
            list_of_prices = soup.find_all("div", class_="tt-price")
            for elem in list_of_prices:
                item_price = elem.get_text(strip=True)
                product_cost_list.append(item_price)

            index += 1

        else:
            not_an_empty_page = False


def scrape_k_pop():
    # We continue scraping until we come across an element that indicates an empty page
    index = 1
    not_an_empty_page = True
    while(index > 0 and not_an_empty_page):
        page = requests.get("https://www.musicplaza.com/collections/k-pop?page={index}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Check for an empty page
        out_of_items = soup.find("div", class_="tt-empty-search")
        if(out_of_items == None):
    
            # Get Title and URL
            list_of_titles = soup.find_all("h2", class_="tt-title prod-thumb-title-color")
            for elem in list_of_titles:
                url_tag = elem.find("a")
                item_url = url_tag['href']
                item_name = elem.get_text(strip=True) 
                product_name_list.append(item_name)
                product_link_list.append(item_url)

            # Get Prices
            list_of_prices = soup.find_all("div", class_="tt-price")
            for elem in list_of_prices:
                item_price = elem.get_text(strip=True)
                product_cost_list.append(item_price)

            index += 1

        else:
            not_an_empty_page = False


def scrape_adult_contemporary():
    # We continue scraping until we come across an element that indicates an empty page
    index = 1
    not_an_empty_page = True
    while(index > 0 and not_an_empty_page):
        page = requests.get("https://www.musicplaza.com/collections/adult-contemporary?page={index}&view=ajax")
        soup = BeautifulSoup(page.content, 'html.parser')

        # Check for an empty page
        out_of_items = soup.find("div", class_="tt-empty-search")
        if(out_of_items == None):
    
            # Get Title and URL
            list_of_titles = soup.find_all("h2", class_="tt-title prod-thumb-title-color")
            for elem in list_of_titles:
                url_tag = elem.find("a")
                item_url = url_tag['href']
                item_name = elem.get_text(strip=True) 
                product_name_list.append(item_name)
                product_link_list.append(item_url)

            # Get Prices
            list_of_prices = soup.find_all("div", class_="tt-price")
            for elem in list_of_prices:
                item_price = elem.get_text(strip=True)
                product_cost_list.append(item_price)

            index += 1

        else:
            not_an_empty_page = False


def assemble_table():
    output_df = pd.DataFrame(list(zip(product_name_list, product_link_list, product_cost_list)),
              columns=['product_name','product_link', 'product_price'])


with DAG(
    dag_id="scrape_musicplaza",
    default_args=default_args,
    description="Scraping and saving results from musicplaza.com",
    schedule_interval="0 */6 * * *",
    start_date=pendulum.datetime(2022, 10, 1, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=10)
) as dag:

    extract_new_releases = PythonOperator(
        task_id = 'extract_new_releases',
        python_callable=scrape_new_releases
    )

    extract_pre_order = PythonOperator(
        task_id = 'extract_pre_order',
        python_callable=scrape_pre_order
    )

    extract_k_pop = PythonOperator(
        task_id = 'extract_k_pop',
        python_callable=scrape_k_pop
    )

    extract_adult_contemporary = PythonOperator(
        task_id = 'extract_adult_contemporary',
        python_callable=scrape_adult_contemporary
    )

    run_assemble_table = PythonOperator(
        task_id = 'run_assemble_table',
        python_callable=assemble_table
    )

    extract_new_releases >> extract_pre_order >> extract_k_pop >> extract_adult_contemporary >> run_assemble_table