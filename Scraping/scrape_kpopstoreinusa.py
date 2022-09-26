from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

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


def scrape_autographed_albums():
    site= "https://kpopstoreinusa.com/shop/autographed-album/"
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(site,headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'lxml')

    # Get Title and Price
    list_of_items = soup.find_all("div", class_="product-details-inner")

    for elem in list_of_items:
        url_tag = elem.find("a")
        item_url = url_tag['href']
        item_name = elem.find("div", class_="wpsp-product-title").get_text(strip=True)
        item_price = elem.find("span", class_="woocommerce-Price-amount amount").get_text(strip=True)
        
        product_name_list.append(item_name)
        product_link_list.append(item_url)
        product_cost_list.append(item_price)


def scrape_preorder_albums():
    site= "https://kpopstoreinusa.com/pre-order/albums/"
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(site,headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'lxml')

    # Get Title and Price
    list_of_items = soup.find_all("div", class_="product-details-inner")

    for elem in list_of_items:
        url_tag = elem.find("a")
        item_url = url_tag['href']
        item_name = elem.find("div", class_="wpsp-product-title").get_text(strip=True)
        item_price = elem.find("span", class_="woocommerce-Price-amount amount").get_text(strip=True)
        
        product_name_list.append(item_name)
        product_link_list.append(item_url)
        product_cost_list.append(item_price)


def scrape_albums():
    site= "https://kpopstoreinusa.com/shop/albums/"
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(site,headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'html.parser')
    # Grabbing the scrolling 'Featured Album' items
    try:
        scrolling_bar_items = soup.find("div", class_="carousel-slider-outer carousel-slider-outer-products carousel-slider-outer-449")
        bar_items_url = scrolling_bar_items.find_all("a", class_="woocommerce-LoopProduct-link")
        bar_items_name = scrolling_bar_items.find_all("h3")
        bar_items_price = scrolling_bar_items.find_all("span", class_="woocommerce-Price-amount amount")
        for elem in bar_items_url:
            product_link_list.append(elem['href'])
        for elem in bar_items_name:
            product_name_list.append(elem.get_text(strip=True))
        for elem in bar_items_price:
            product_cost_list.append(elem.get_text(strip=True))

    except:
        pass

    # Grabbing other items on the page
    list_of_items = soup.find("div", class_="wpsp-slider-section wpsp-slider-section28435 sp-woo-product-slider-pro28435 wpsp_theme_one pagination-type-dots navigation_position_top_right grid_style_even")
    list_of_items = list_of_items.find_all("div", class_="product-details-inner")
    for elem in list_of_items:
        try:
            url_tag = elem.find("a")
            item_url = url_tag['href']
            item_name = elem.find("div", class_="wpsp-product-title").get_text(strip=True)
            item_price = elem.find("span", class_="woocommerce-Price-amount amount").get_text(strip=True)

            product_name_list.append(item_name)
            product_link_list.append(item_url)
            product_cost_list.append(item_price)

        except:
            continue