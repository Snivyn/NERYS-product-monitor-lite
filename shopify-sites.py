'''
NERYS
a universal product monitor

Current Module: Shopify Sites

Usage:
NERYS will monitor specified sites for keywords and sends a Discord alert
when a page has a specified keyword. This can be used to monitor any site
on a product release date to automatically detect when a product has been
uploaded. Useful when monitoring hundreds of sites for shops in different
timezones.

Complete:
- find all products on Shopify site by keyword
- send discord notifications
- monitor for new products
- optimization for Shopify to return product checkout links by size
- find all products on other sites by keyword
- attempt to get product page links for universal sites

Left To Do:
- monitor for Shopify restocks
- monitor for restocks on other sites
-- find sold out by keyword
-- find sizes by keyword
-- find countdown timer by keyword
- detect cloudflare
- get product picture for other sites
- optimization for footsites

Credits:
Niveen Jegatheeswaran - Main Dev - https://github.com/snivyn/
kyb3r - Discord Embed - https://github.com/kyb3r/
'''

import requests
from log import log as log
import time
from threading import Thread
from datetime import datetime
import random
import json
import sqlite3
from bs4 import BeautifulSoup as soup
from discord_hooks import Webhook
from multiprocessing import Process


class FileNotFound(Exception):
    ''' Raised when a file required for the program to operate is missing. '''


class NoDataLoaded(Exception):
    ''' Raised when the file is empty. '''


class OutOfProxies(Exception):
    ''' Raised when there are no proxies left '''


def read_from_txt(path):
    '''
    (None) -> list of str
    Loads up all sites from the sitelist.txt file in the root directory.
    Returns the sites as a list
    '''
    # Initialize variables
    raw_lines = []
    lines = []

    # Load data from the txt file
    try:
        f = open(path, "r")
        raw_lines = f.readlines()
        f.close()

    # Raise an error if the file couldn't be found
    except:
        log('e', "Couldn't locate <" + path + ">.")
        raise FileNotFound()

    if(len(raw_lines) == 0):
        raise NoDataLoaded()

    # Parse the data
    for line in raw_lines:
        lines.append(line.strip("\n"))

    # Return the data
    return lines


def send_embed(alert_type, link, fields, site, image, product):
    '''
    (str, str, list, str, str, str) -> None
    Sends a discord alert based on info provided.
    '''

    url = webhook

    embed = Webhook(url, color=123123)

    if(alert_type == "NEW_SHOPIFY"):
        desc = "NEW: " + product
    elif(alert_type == "RESTOCK_SHOPIFY"):
        desc = "RESTOCK: " + product

    embed.set_author(name='NERYS', icon='https://static.zerochan.net/Daenerys.Targaryen.full.2190849.jpg')
    embed.set_desc(desc)

    for field in fields:
        if(alert_type == "NEW_SHOPIFY" or alert_type == "RESTOCK_SHOPIFY"):
            cart_link = site + "/cart/" + str(field[1]) + ":1"
            embed.add_field(name=str(field[0]), value=cart_link)

    if(image is not None):
        embed.set_thumbnail(image)
        embed.set_image(image)

    embed.set_footer(text='NERYS by @snivynGOD', icon='https://static.zerochan.net/Daenerys.Targaryen.full.2190849.jpg', ts=True)

    embed.post()


def get_proxy(proxy_list):
    '''
    (list) -> dict
    Given a proxy list <proxy_list>, a proxy is selected and returned.
    '''
    # Choose a random proxy
    proxy = random.choice(proxy_list)

    # Set up the proxy to be used
    proxies = {
        "http": str(proxy),
        "https": str(proxy)
    }

    # Return the proxy
    return proxies


def update_shopify_db(keywords, site, proxy_list):
    while(True):
        log('i', "Monitoring site <" + site + ">.")

        # Initialize variables
        link = site + "/collections/all/products.atom"
        working = False

        # Get a proxy
        proxies = get_proxy(proxy_list)

        # Get the products on the site
        try:
            r = requests.get(link, proxies=proxies, timeout=3, verify=False)
        except:
            try:
                proxies = get_proxy(proxy_list)
                r = requests.get(link, proxies=proxies, timeout=5, verify=False)
            except:
                log('e', "Connection to URL <" + link + "> failed.")
                continue
    
        xml = soup(r.text, "xml")
        products_raw = xml.findAll('entry')
    
        # Get products with the specified keywords
        for product in products_raw:
            product_found = False
            for keyword in keywords:
                if(not product_found):
                    # Get the product info
                    title = product.find("title").text
                    link = product.find("link")["href"]
                    tags_raw = product.findAll("s:tag")
    
                    tags = []
                    for tag in tags_raw:
                        tags.append(tag.text.upper())
    
                    # Check if the keywords are in the product's name or tags
                    if(keyword.upper() in title.upper() or keyword.upper() in tags):
                        # Get the variants from the product
                        try:
                            r = requests.get(link + ".xml", proxies=proxies, timeout=3, verify=False)
                            working = True
                        except:
                            # Get a new proxy
                            proxies = get_proxy(proxy_list)
                            # Try again with a new proxy
                            try:
                                r = requests.get(link + ".xml", proxies=proxies, timeout=5, verify=False)
                                working = True
                            except:
                                working = False
    
                        # If the site/proxy is working
                        if(working):
                            # Break down the product page
                            xml = soup(r.text, "xml")
    
                            # Get the variants for the product
                            variants = []
                            raw_variants = xml.findAll("variant")
                            for raw_variant in raw_variants:
                                variants.append((raw_variant.find("title").text, raw_variant.find("id").text))
    
                            # Get the product's image if it's available
                            try:
                                image = xml.find("image").find("src").text
                            except:
                                image = None
    
                            # Store the product in the database
                            product_info = (title, link, variants, image, title, site)
                            alert = add_to_shopify_db(product_info)
                            product_found = True
    
                            # Send a Discord alert if the product is new
                            if(alert):
                                send_embed("NEW_SHOPIFY", link, variants, site, image, title)

        # Wait the specified timeframe before checking the site again
        time.sleep(delay)


def add_to_shopify_db(product):
    # Initialize variables
    title = product[0]
    link = product[1]
    stock = str(product[2])
    alert = False

    # Create database
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS products_shopify(link TEXT UNIQUE, product TEXT, stock TEXT)""")

    # Add product to database if it's unique
    try:
        c.execute("""INSERT INTO products_shopify (link, product, stock) VALUES (?, ?, ?)""", (link, title, stock))
        log('s', "Found new product <" + title + ">.")
        alert = True
    except:
        log('i', "Product <" + title + "> already exists in the database.")

    # Close database
    conn.commit()
    c.close()
    conn.close()

    # Return whether or not it's a new product
    return alert


''' --------------------------------- RUN --------------------------------- '''

if(__name__ == "__main__"):
    # Ignore insecure messages
    requests.packages.urllib3.disable_warnings()

    # Initialize settings
    keywords = [
        "bred toe",
        "gold toe",
        "pharrell",
        "holi",
        "free throw line",
        "kendrick",
        "tinker",
        "game royal",
        "yeezy",
        "human race",
        "big bang",
        "dont trip",
        "don't trip",
        "kung fu kenny",
        "playstation",
        "ovo air jordan",
        "ovo jordan",
        "wotherspoon",
        "nike x off-white",
        "off-white x nike",
        "air jordan 1",
        "wave runner",
        "katrina",
        "animal pack",
        "acronym",
        "vf sw",
        "the ten",
        "the 10"
        ]

    webhook = "https://discordapp.com/api/webhooks/412107584380600321/0vIQE8Hp8zkHxHTXfELCDLXKwpMY3r4OEFVy2Q7O8RwQIawo7sj5uBUJDjeP5Xl-DK-0"  # Put your webhook link here

    delay = 10  # Lots of sites + few proxies = longer delay to avoid bans

    # Load proxies
    proxies = read_from_txt("proxies.txt")
    log('i', str(len(proxies)) + " proxies loaded.")

    # Store sites from txt files
    shopify_sites = read_from_txt("shopify-sites.txt")
    total_sites = len(shopify_sites)
    log('i', str(total_sites) + " sites loaded.")

    # Loop through each Shopify site
    for site in shopify_sites:
        # Monitor for new products
        t = Thread(target=update_shopify_db, args=(keywords, site, proxies))
        t.start()
        time.sleep(1)

