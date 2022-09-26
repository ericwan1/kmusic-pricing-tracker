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

product_name_list = []
product_link_list = []
product_cost_list = []

# We only scrape the frontpage because MWave's signed CD's are listed very infrequently.
# Scraping this site is to give us notice of new items and possibly compare their current/original price to resellers or official artist pages.
def scrape_mwave_frontpage():
    page = requests.get("https://shop.mwave.me/en/cd.html")
    soup = BeautifulSoup(page.content, 'html.parser')

    list_of_items = soup.find_all("li", class_="product-item item product-item-one")

    for elem in list_of_items:
        url_tag = elem.find("a")
        item_url = url_tag['href']
        product_link_list.append(item_url)

        item_price_box = elem.find("div", class_="price-box")
        item_price = item_price_box.find("span", class_="price").get_text(strip=True)
        product_cost_list.append(item_price)

        item_name_tag = elem.find("strong")
        item_name = item_name_tag.get_text(strip=True)
        product_name_list.append(item_name)


def assemble_table():
    output_df = pd.DataFrame(list(zip(product_name_list, product_link_list, product_cost_list)),
              columns=['product_name','product_link', 'product_price'])


with DAG(
    dag_id="scrape_mwave",
    default_args=default_args,
    description="Scraping and saving results from https://shop.mwave.me/en/cd.html",
    schedule_interval="0 */12 * * *",
    start_date=pendulum.datetime(2022, 10, 1, tz="UTC"),
    dagrun_timeout=datetime.timedelta(minutes=10)
) as dag:

    extract_signed_cds = PythonOperator(
        task_id = 'extract_new_releases',
        python_callable=scrape_mwave_frontpage
    )

    run_assemble_table = PythonOperator(
        task_id = 'run_assemble_table',
        python_callable=assemble_table
    )

    extract_signed_cds >> run_assemble_table