'''
NERYS
a universal product monitor

Current Module: Other Sites

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
from bs4 import BeautifulSoup as soup
import requests
from log import log as log
import time
from datetime import datetime
import random
import sqlite3
from bs4 import BeautifulSoup as soup
from discord_hooks import Webhook
from threading import Thread


class Product():
    def __init__(self, title, link, stock, keyword):
        '''
        (str, str, bool, str) -> None
        Creates an instance of the Product class.
        '''
    
        # Setup product attributes
        self.title = title
        self.stock = stock
        self.link = link
        self.keyword = keyword


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


def add_to_db(product):
    '''
    (Product) -> bool
    Given a product <product>, the product is added to a database <products.db>
    and whether or not a Discord alert should be sent out is returned. Discord
    alerts are sent out based on whether or not a new product matching
    keywords is found.
    '''

    # Initialize variables
    title = product.title
    stock = str(product.stock)
    link = product.link
    keyword = product.keyword
    alert = False

    # Create database
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS products(title TEXT, link TEXT UNIQUE, stock TEXT, keywords TEXT)""")

    # Add product to database if it's unique
    try:
        c.execute("""INSERT INTO products (title, link, stock, keywords) VALUES (?, ?, ?, ?)""", (title, link, stock, keyword))
        log('s', "Found new product with keyword " + keyword + ". Link = " + link)        
        alert = True
    except:
        # Product already exists
        pass
        #log('i', "Product at URL <" + link + "> already exists in the database.")

    # Close connection to the database
    conn.commit()
    c.close()
    conn.close()

    # Return whether or not it's a new product
    return alert


def send_embed(product):
    '''
    (Product) -> None
    Sends a discord alert based on info provided.
    '''

    url = 'INSERT YOUR WEBHOOK HERE'

    embed = Webhook(url, color=123123)

    embed.set_author(name='NERYS', icon='https://static.zerochan.net/Daenerys.Targaryen.full.2190849.jpg')
    embed.set_desc("Found product based on keyword " + product.keyword)

    embed.add_field(name="Link", value=product.link)

    embed.set_footer(text='NERYS by @snivynGOD', icon='https://static.zerochan.net/Daenerys.Targaryen.full.2190849.jpg', ts=True)

    embed.post()


def monitor(link, keywords):
    '''
    (str, list of str) -> None
    Given a URL <link> and keywords <keywords>, the URL is scanned and alerts
    are sent via Discord when a new product containing a keyword is detected.
    '''

    log('i', "Checking site <" + link + ">...")

    # Parse the site from the link
    pos_https = link.find("https://")
    pos_http = link.find("http://")

    if(pos_https == 0):
        site = link[8:]
        end = site.find("/")
        if(end != -1):
            site = site[:end]
        site = "https://" + site
    else:
        site = link[7:]
        end = site.find("/")
        if(end != -1):
            site = site[:end]
        site = "http://" + site

    # Get all the links on the "New Arrivals" page
    try:
        r = requests.get(link, timeout=5, verify=False)
    except:
        log('e', "Connection to URL <" + link + "> failed. Retrying...")
        time.sleep(5)
        try:
            r = requests.get(link, timeout=8, verify=False)
        except:
            log('e', "Connection to URL <" + link + "> failed.")
            return

    page = soup(r.text, "html.parser")

    raw_links = page.findAll("a")
    hrefs = []

    for raw_link in raw_links:
        try:
            hrefs.append(raw_link["href"])
        except:
            pass

    # Check for links matching keywords
    for href in hrefs:
        found = False
        for keyword in keywords:
            if(keyword.upper() in href.upper()):
                found = True
                if("http" in href):
                    product_page = href
                else:
                    product_page = site + href
                product = Product("N/A", product_page, True, keyword)
                alert = add_to_db(product)

                if(alert):
                    send_embed(product)

if(__name__ == "__main__"):
    # Ignore insecure messages
    requests.packages.urllib3.disable_warnings()

    # Keywords (seperated by -)
    keywords = [
        "bred-toe",
        "gold-toe",
        "pharrell",
        "free-throw-line",
        "kendrick",
        "tinker",
        "game-royal",
        "yeezy",
        "human-race",
        "big-bang",
        "dont-trip",
        "kung-fu-kenny",
        "playstation",
        "valentine",
        "ovo-air-jordan",
        "ovo-jordan",
        "air-jordan-1",
        "wotherspoon"
    ]
    
    # Load sites from file
    sites = read_from_txt("other-sites.txt")

    # Start monitoring sites
    while(True):
        threads = []
        for site in sites:
            t = Thread(target=monitor, args=(site, keywords))
            threads.append(t)
            t.start()
            time.sleep(2)  # 2 second delay before going to the next site
